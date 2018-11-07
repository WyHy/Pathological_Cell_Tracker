import datetime
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import openslide

from common.tslide.tslide import TSlide
from common.utils import ImageSlice
from config.config import *
from models.darknet.darknet_predict import DarknetPredict
from utils import FilesScanner

GPU_NUM = len(os.popen("lspci|grep VGA|grep NVIDIA").read().split('\n')) - 1


def yolo_predict(gpu_index, images_lst):
    """
    Yolo 检测细胞位置
    :param gpu_index: gpu id
    :param images_lst: image 路径列表
    :return: dict: <x_y: [label, accuracy, xmin, ymin, xmax, ymax]>
    """
    return DarknetPredict(str(gpu_index)).predict(images_lst)


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

            try:
                slide = openslide.OpenSlide(tiff)
            except:
                slide = TSlide(tiff)

            keys = list(seg_results.keys())
            for key in keys:
                lst = seg_results[key]
                x0, y0 = key.split('_')
                x0, y0 = int(x0), int(y0)

                for item in lst:
                    label, accuracy, (x, y, w, h) = item
                    accuracy, x, y, w, h = float(accuracy), int(x), int(y), int(w), int(h)
                    x, y = x0 + x, y0 + y

                    save_path = os.path.join(self.cells_path, tiff_basename, label)
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)

                    image_name = "1-p{:.4f}_{}_x{}_y{}_w{}_h{}.jpg".format(1 - accuracy, tiff_basename, x, y, w, h)
                    slide.read_region((x, y), 0, (w, h)).convert("RGB").save(os.path.join(save_path, image_name))


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
