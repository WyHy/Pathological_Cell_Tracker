import datetime

import openslide

from common.tslide.tslide import TSlide
from common.utils import ImageSlice
from config.config import *
from models.darknet.darknet_predict import DarknetPredict
from models.decisionTree.decision_tree_predict import DecisionTreePredict
from models.xception.xception_postprocess import XceptionPostprocess
from models.xception.xception_predict import XceptionPredict
from models.xception.xception_preprocess import XceptionPreprocess
from utils import FilesScanner
from sklearn.externals import joblib


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
        # Yolo 初始化
        darknet_model = DarknetPredict()

        # Xception 初始化
        xception_model = XceptionPredict()

        # Decision Tree 初始化
        dst_model = DecisionTreePredict()

        total = len(tiff_lst)
        for index, tiff in enumerate(self.tiff_lst):
            # 获取大图文件名，不带后缀
            tiff_basename, _ = os.path.splitext(os.path.basename(tiff))
            tiff_basename = tiff_basename.replace(" ", "_")
            print('Process %s / %s %s ...' % (index + 1, total, tiff_basename))

            # 切片文件存储路径
            slice_save_path = os.path.join(self.slice_dir_path, tiff_basename)

            # 如果路径下切图文件不存在，执行切图
            if not os.path.join(slice_save_path):
                # 执行切图
                ImageSlice(tiff, self.slice_save_path).get_slices()

            # 获取切图文件路径
            tif_images = FilesScanner(slice_save_path, ['.jpg']).get_files()

            print("DARKNET PROCESSING ...")
            t0 = datetime.datetime.now()
            # 执行 Yolo 细胞分割
            seg_results = darknet_model.predict(tif_images)
            t1 = datetime.datetime.now()
            print("DARKNET COST %s" % (t1 - t0))

            # 将细胞分割结果写入文件
            xcep_pre = XceptionPreprocess(tiff_basename)
            seg_csv = os.path.join(self.meta_files_path, tiff_basename + "_seg.csv")
            xcep_pre.write_csv(seg_results, seg_csv)

            # generate numpy array, it is the input of second stage classification algorithm
            cell_numpy, cell_index = xcep_pre.gen_np_array_csv(seg_csv=seg_csv)

            print("XCEPTION PROCESSING ...")
            # 执行细胞分类
            predictions = xception_model.predict(cell_numpy)
            t2 = datetime.datetime.now()
            print("XCEPTION COST %s" % (t2 - t1))

            clas = XceptionPostprocess()
            clas_dict = clas.convert_all(predictions=predictions, cell_index=cell_index)
            clas_csv = os.path.join(self.meta_files_path, tiff_basename + "_clas.csv")
            clas.write_csv(clas_dict, clas_csv)

            # 预测诊断结果
            final_diagnose_result = dst_model.predict(clas_dict)
            print("FINAL DIAGNOSE RESULT IS %s" % final_diagnose_result)

            clas.cut_cells_p_marked(tiff_basename, clas_dict, os.path.join(self.cells_path, final_diagnose_result), factor=0.2, N=2)
            t3 = datetime.datetime.now()
            print("GET VIEW IMAGES COST %s" % (t3 - t2))


if __name__ == "__main__":
    # wanna test?
    test = True

    t0 = datetime.datetime.now()

    resource_path = '/home/cnn/Development/DATA/RESOURCE'

    if not test:
        # TIFF 图像存储路径
        tiff_dir_path = os.path.join(resource_path, 'TIFF')

        # 切图文件存储路径
        slice_dir_path = os.path.join(resource_path, 'SLICE')

        # 中间文件存放目录
        meta_files_path = os.path.join(resource_path, 'META')

        # 识别出的细胞存储路径
        cells_save_path = os.path.join(resource_path, 'CELLS')
    else:
        # TIFF 图像存储路径
        tiff_dir_path = os.path.join(resource_path, 'test', 'TIFF')

        # 切图文件存储路径
        slice_dir_path = os.path.join(resource_path, 'test', 'SLICE')

        # 中间文件存放目录
        meta_files_path = os.path.join(resource_path, 'test', 'META')

        # 识别出的细胞存储路径
        cells_save_path = os.path.join(resource_path, 'test', 'CELLS')

    # 获取 TIFF 图像文件地址列表
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

    t1 = datetime.datetime.now()
    print("TIFF NUM: %s， TOTAL COST %s ..." % (len(tiff_lst), (t1 - t0)))
