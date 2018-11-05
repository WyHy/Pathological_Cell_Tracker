import datetime
import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import openslide

from common.tslide.tslide import TSlide
from common.utils import ImageSlice
from config.config import *
from models.darknet.darknet_predict import DarknetPredict
from models.xception.xception_postprocess import XceptionPostprocess
from models.xception.xception_predict import XceptionPredict
from models.xception.xception_preprocess import XceptionPreprocess
from utils import FilesScanner, generate_name_path_dict, generate_work_list, download_tiff_to_local

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

            ############################### 生成审核图像 ######################################################
            # GET VIEW CELL IMAGES
            clas.cut_cells_p_marked(tiff, clas_dict, self.cells_path, factor=0.2, N=2)
            t4 = datetime.datetime.now()
            print("GET VIEW IMAGES COST %s" % (t4 - t3))

            print("TIFF %s TOTAL COST %s ..." % (tiff_basename, t4 - t0))


def do_collect_by_tiff_type(path, dict_):
    """
    根据类别及分类别数量限制收集分类图像
    :param path: CELLS 文件路径
    :param dict_:  TIFF 文件名及对应 诊断结果 dict
    :return:
    """

    # 提取分类概率正则表达式
    pattern = re.compile(r'1\-p(0.\d{4}).*?.jpg')

    # 文件归类存放路径
    save_path = os.path.join(os.path.dirname(path), 'TO_BE_CHECK_CELLS')

    # 获取大图列表
    tiffs = os.listdir(path)
    total = len(tiffs)
    for index, tiff in enumerate(tiffs):
        print("%s / %s ..." % (index + 1, total))
        src_root_dir = os.path.join(path, tiff)

        # 获取大图下包含细胞类别名称
        types = os.listdir(src_root_dir)

        for ctype in types:
            src_path = os.path.join(src_root_dir, ctype)
            images_lst = os.listdir(src_path)

            dst_path = os.path.join(save_path, dict_[tiff], tiff, ctype)
            if ctype == 'HSIL' and len(images_lst) > 500:
                print("FOUND HSIL COUNT > 500 IN %s" % tiff)

                # 按概率大小排序
                p_dict = {}
                for img in images_lst:
                    p = float(re.findall(pattern, img)[0][0])
                    p_dict[img] = p

                p_dict_sorted = sorted(p_dict.items(), key=lambda x: x[1])
                for key in p_dict_sorted[:500]:
                    shutil.copy(os.path.join(src_path, key[0]), dst_path)
            else:
                shutil.copytree(src_path, dst_path)

    print("PLEASE GET CLASSIFIED CELL IMAGES IN %s" % save_path)


if __name__ == "__main__":
    # wanna test?
    test = False

    t0 = datetime.datetime.now()

    # RUN AS "python3 lbp_algo_tiff_worker_by_excel.py *.xlsx */*"
    excel_path, resource_save_path = sys.argv[1], sys.argv[2]

    # 生成任务字典
    print("1-GENERATE JOB DICT ...")
    job_dict = generate_work_list(excel_path)

    # # TIFF 图像存储路径
    tiff_dir_path = os.path.join(resource_save_path, 'TIFFS')

    # 开始下载远程文件到本地
    print('2-DOWNLOADING TIFFS TO LOCAL PATH ...')
    download_tiff_to_local(list(job_dict.keys()), tiff_dir_path)

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
    print('3-TIFFS INTEGRITY VERIFICATION ...')
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

    # 开始切图任务
    print("4-JOB START...")
    PCK(tiff_lst, slice_dir_path, meta_files_path, cells_save_path).run()

    # 执行文件归类操作
    print("5-TIFFS CLASSIFICATION ...")
    do_collect_by_tiff_type(cells_save_path, job_dict)

    t1 = datetime.datetime.now()
    print("TIFF NUM: %s， TOTAL COST %s ..." % (len(tiff_lst), (t1 - t0)))
