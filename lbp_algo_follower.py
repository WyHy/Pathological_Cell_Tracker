import datetime
import shutil
import sys
import re
from common.utils import FilesScanner, ImageSlice
from config.config import *
from models.darknet.darknet_predict import DarknetPredict
from models.xception.xception_postprocess import XceptionPostprocess
from models.xception.xception_predict import XceptionPredict
from models.xception.xception_preprocess import XceptionPreprocess

import datetime


class PCK:
    def __init__(self, images_path, meta_files_path, cells_path):
        self.images_path = images_path
        self.cells_path = cells_path
        self.meta_files_path = meta_files_path

    def run(self):
        # 获取 608 图像文件地址列表
        images_lst = FilesScanner(self.images_path, postfix=".jpg").get_files()

        # 2018-04-19-22_28_52_15843_20909.jpg
        pattern = re.compile(r'(.*?)_(\d+)_(\d+).jpg')

        # 路径字典信息本地保存文件
        local_dict_info_file = 'tiff_images_dict.txt'

        dict_file = os.path.join(self.meta_files_path, local_dict_info_file)

        # 大图对应大图所属608文件路径列表字典
        tiff_dict = {}
        if os.path.exists(dict_file):
            print("LOADING <TIFF_NAME>: <IMAGE_PATH_LIST> DICT ...")
            with open(dict_file) as f:
                lines = f.readlines()
                for line in lines:
                    key, lst = line.replace('\n', '').split('\t')
                    tiff_dict[key] = lst.split('|')
        else:
            print("GENERATE <TIFF_NAME>: <IMAGE_PATH_LIST> DICT ...")
            for item in images_lst:
                basename = os.path.basename(item)
                try:
                    tiff_name, x, y = re.findall(pattern, basename)[0]
                except:
                    print(item)
                    continue

                if tiff_name in tiff_dict:
                    tiff_dict[tiff_name].append(item)
                else:
                    tiff_dict[tiff_name] = [item]

            with open(dict_file, 'w') as o:
                for key, lst in tiff_dict.items():
                    o.write('%s\t%s\n' % (key, '|'.join(lst)))

        # Yolo 初始化
        darknet_model = DarknetPredict()

        # Xception 初始化
        xception_model = XceptionPredict()

        keys = list(tiff_dict.keys())
        total = len(keys)

        failed_tiff_lst = []

        # 遍历切割细胞，识别细胞分类
        for index, tiff_name in enumerate(keys[:10]):
            print('Process %s / %s %s ...' % (index + 1, total, tiff_name))

            try:
                images_lst = tiff_dict[tiff_name]

                t0 = datetime.datetime.now()
                # 执行 Yolo 细胞分割
                seg_results = darknet_model.predict(images_lst)
                t1 = datetime.datetime.now()
                print("DARKNET COST %s" % (t1 - t0))

                # 将细胞分割结果写入文件
                xcep_pre = XceptionPreprocess(tiff_name)
                seg_csv = os.path.join(self.meta_files_path, tiff_name + "_seg.csv")
                xcep_pre.write_csv(seg_results, seg_csv)

                # generate numpy array, it is the input of second stage classification algorithm
                cell_numpy, cell_index = xcep_pre.gen_np_array_csv_(seg_csv=seg_csv)

                # 执行细胞分类
                predictions = xception_model.predict(cell_numpy)
                t2 = datetime.datetime.now()
                print("XCEPTION COST %s" % (t2 - t1))

                # summarize two stages' result and generate a final csv
                clas = XceptionPostprocess()
                clas_dict = clas.convert_all(predictions=predictions, cell_index=cell_index)
                clas_csv = os.path.join(self.meta_files_path, tiff_name + "_clas.csv")
                clas.write_csv(clas_dict, clas_csv)

                clas.cut_cells_p_marked_(tiff_name, clas_dict, self.cells_path, factor=0.2, N=2)
            except Exception as e:
                print(str(e))
                failed_tiff_lst.append((tiff_name, str(e)))
                continue

        with open("failed_tiff_lst.txt", 'w') as o:
            for ele in failed_tiff_lst:
                o.write("%s\n" % '\t'.join(ele))


if __name__ == "__main__":
    # wanna test?
    test = True

    if test:
        # 608 图像存储路径
        images_dir_path = '/home/tsimage/Development/DATA/test/remark'

        # 中间文件存放目录
        meta_files_path = '/home/tsimage/Development/DATA/test/meta'

        # 识别出的细胞存储路径
        cells_save_path = '/home/tsimage/Development/DATA/test/cells'
    else:
        # 608 图像存储路径
        images_dir_path = '/home/tsimage/Development/DATA/remark'

        # 中间文件存放目录
        meta_files_path = '/home/tsimage/Development/DATA/meta'

        # 识别出的细胞存储路径
        cells_save_path = '/home/tsimage/Development/DATA/cells'

    PCK(images_dir_path, meta_files_path, cells_save_path).run()
