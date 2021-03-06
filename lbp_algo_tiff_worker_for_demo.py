import datetime
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import openslide

from common.tslide.tslide import TSlide
from common.utils import ImageSlice
from config.config import *
from models.darknet.darknet_predict import DarknetPredict
from models.final_diagnose.diagnose import gen_slide_diagnose
from models.xception.xception_postprocess import XceptionPostprocess
from models.xception.xception_predict import XceptionPredict
from models.xception.xception_preprocess import XceptionPreprocess
from utils import FilesScanner, gen_tiff_label_to_db, gen_tiff_diagnose_to_db

GPU_NUM = len(os.popen("lspci|grep VGA|grep NVIDIA").read().split('\n')) - 1


def yolo_predict(gpu_index, images_lst):
    """
    Yolo 检测细胞位置
    :param gpu_index: gpu id
    :param images_lst: image 路径列表
    :return: dict: <x_y: [label, accuracy, xmin, ymin, xmax, ymax]>
    """
    return DarknetPredict(str(gpu_index)).predict(images_lst)


def xception_predict(gpu_index, images_numpy):
    """
    Xception 识别细胞病理分类
    :param gpu_index: gpu id
    :param images_numpy: image numpy_array
    :return:
    """
    return gpu_index, XceptionPredict(str(gpu_index)).predict(images_numpy)


class PCK:
    def __init__(self, tiff_lst, slice_dir_path, meta_files_path, cells_path):
        """

        :param tiff_lst: TIFF 文件列表
        :param slice_dir_path:  切图文件存放路径
        :param meta_files_path:  中间文件存放路径
        :param cells_path:  输出审核细胞存放路径
        """
        self.tiff_lst = tiff_lst
        self.slice_dir_path = slice_dir_path
        self.cells_path = cells_path
        self.meta_files_path = meta_files_path

        # 获取 Decision Tree 分类
        with open(cfg.decision_tree.classes_files) as f:
            lines = f.readlines()
            self.decision_tree_classes = [line.replace('\n', '') for line in lines]

    def run(self):
        print("Initial DARKNET and XCEPTION model ...")

        total = len(self.tiff_lst)
        for index, tiff in enumerate(self.tiff_lst):
            # 获取大图文件名，不带后缀
            tiff_basename, _ = os.path.splitext(os.path.basename(tiff))
            tiff_basename = tiff_basename.replace(" ", "-")
            print('Process %s / %s %s ...' % (index + 1, total, tiff_basename))

            # 检测是否已经切图并识别完成
            # 检测细胞文件夹是否已经存在，若存在直接跳过
            check_cell_path = os.path.join(self.cells_path, tiff_basename)

            if os.path.exists(check_cell_path):
                children = os.listdir(check_cell_path)
                if len(children) > 0:
                    print("%s HAS BEEN PROCESSED!" % tiff_basename)
                    continue

            # 切片文件存储路径
            slice_save_path = os.path.join(self.slice_dir_path, tiff_basename)

            t0 = datetime.datetime.now()
            # 如果路径下切图文件不存在，执行切图
            if not os.path.exists(slice_save_path):
                # 执行切图
                ImageSlice(tiff, self.slice_dir_path).get_slices()

            # 获取切图文件路径
            tif_images = FilesScanner(slice_save_path, ['.jpg']).get_files()
            t1 = datetime.datetime.now()
            print('TIFF SLICE COST: %s' % (t1 - t0))

            # CHECK IF ALREADY PROCESSED
            seg_csv = os.path.join(self.meta_files_path, tiff_basename + "_seg.csv")

            # 将细胞分割结果写入文件
            xcep_pre = XceptionPreprocess(tiff)

            if not os.path.exists(seg_csv):
                #################################### YOLO 处理 #####################################################
                tasks = []

                # 创建切图进程池
                executor = ProcessPoolExecutor(max_workers=GPU_NUM)

                if len(tif_images) < cfg.darknet.min_job_length:
                    tasks.append(executor.submit(yolo_predict, '0', tif_images))
                else:
                    # 任务切分
                    n = int((len(tif_images) / float(GPU_NUM)) + 0.5)
                    patches = [tif_images[i: i + n] for i in range(0, len(tif_images), n)]

                    for gpu_index, patch in enumerate(patches):
                        tasks.append(executor.submit(yolo_predict, str(gpu_index), patch))

                seg_results = {}
                for future in as_completed(tasks):
                    result = future.result()
                    seg_results.update(result)

                # 关闭进程池
                executor.shutdown(wait=True)

                # WRITE DATA TO CSV
                xcep_pre.write_csv(seg_results, seg_csv)

            t2 = datetime.datetime.now()
            print("DARKNET COST %s" % (t2 - t1))

            # XCEPTION preprocess
            cell_lst, cell_index = xcep_pre.gen_np_array_csv(seg_csv=seg_csv)

            ##################################### XCEPTION 处理 #################################################
            tasks = []
            # 创建切图进程池
            executor = ProcessPoolExecutor(max_workers=GPU_NUM)

            if len(cell_lst) < cfg.xception.min_job_length:
                tasks.append(executor.submit(xception_predict, '0', np.asarray(cell_lst)))
            else:
                # 任务切分
                n = int((len(cell_lst) / float(GPU_NUM)) + 0.5)
                cell_patches = [cell_lst[i: i + n] for i in range(0, len(cell_lst), n)]

                for gpu_index, patch in enumerate(cell_patches):
                    tasks.append(executor.submit(xception_predict, str(gpu_index), np.asarray(patch)))

            predictions_ = {}
            for future in as_completed(tasks):
                index, result = future.result()
                predictions_[index] = result

            predictions = []
            for i in range(len(predictions_)):
                predictions.extend(predictions_[str(i)])

            # 关闭进程池
            executor.shutdown(wait=True)

            t3 = datetime.datetime.now()
            print("XCEPTION COST %s" % (t3 - t2))

            clas = XceptionPostprocess()
            clas_dict = clas.convert_all(predictions=predictions, cell_index=cell_index)
            clas_csv = os.path.join(self.meta_files_path, tiff_basename + '_clas.csv')
            clas.write_csv(clas_dict, clas_csv)

            # 更新诊断信息
            gen_tiff_diagnose_to_db(os.path.basename(tiff), gen_slide_diagnose(clas_csv))

            # 更新标记信息
            gen_tiff_label_to_db(clas_csv)


def slides_diagnose_worker(tiff_lst, resource_save_path):
    # 切图文件存储路径
    slice_dir_path = os.path.join(resource_save_path, 'SLICE')

    # 中间文件存放目录
    meta_files_path = os.path.join(resource_save_path, 'META')

    # 识别出的细胞存储路径
    cells_save_path = os.path.join(resource_save_path, 'CELLS')

    # tiff_lst = FilesScanner(tiff_dir_path, ['.kfb', '.tif']).get_files()

    for item in [slice_dir_path, meta_files_path, cells_save_path]:
        if not os.path.exists(item):
            os.makedirs(item)

    PCK(tiff_lst, slice_dir_path, meta_files_path, cells_save_path).run()


if __name__ == "__main__":
    # wanna test?
    test = False

    t0 = datetime.datetime.now()

    tiff_dir_path, resource_save_path = sys.argv[1], sys.argv[2]

    if test:
        # 切图文件存储路径
        slice_dir_path = os.path.join(resource_save_path, 'test', 'SLICE')

        # 中间文件存放目录
        meta_files_path = os.path.join(resource_save_path, 'test', 'META')

        # 识别出的细胞存储路径
        cells_save_path = os.path.join(resource_save_path, 'test', 'CELLS')
    else:
        # 切图文件存储路径
        slice_dir_path = os.path.join(resource_save_path, 'SLICE')

        # 中间文件存放目录
        meta_files_path = os.path.join(resource_save_path, 'META')

        # 识别出的细胞存储路径
        cells_save_path = os.path.join(resource_save_path, 'CELLS')

    tiff_lst = FilesScanner(tiff_dir_path, ['.kfb', '.tif']).get_files()

    # 执行 TIFF 文件完整性校验
    for tiff in tiff_lst:
        try:
            try:
                slide = openslide.OpenSlide(tiff)
            except:
                slide = TSlide(tiff)
        except Exception as e:
            raise Exception("%s %s" % (tiff, str(e)))

    for item in [slice_dir_path, meta_files_path, cells_save_path]:
        if not os.path.exists(item):
            os.makedirs(item)

    PCK(tiff_lst, slice_dir_path, meta_files_path, cells_save_path).run()
    print("PLEASE GET CELL IMAGES IN %s" % cells_save_path)

    t1 = datetime.datetime.now()
    print("TIFF NUM: %s， TOTAL COST %s ..." % (len(tiff_lst), (t1 - t0)))
