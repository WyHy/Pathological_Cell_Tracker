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
            with open(dict_file) as f:
                lines = f.readlines()
                for line in lines:
                    key, lst = line.replace('\n', '').split('\t')
                    tiff_dict[key] = lst.split('|')
        else:
            for item in images_lst:
                basename = os.path.basename(item)
                tiff_name, x, y = re.findall(pattern, basename)[0]

                if tiff_name in tiff_dict:
                    tiff_dict[tiff_name].append(item)
                else:
                    tiff_dict[tiff_name] = [item]

            with open(dict_file, 'w') as o:
                for key, lst in tiff_dict.items():
                    o.write('%s\t%s\n' % (key, '|'.join(lst)))

        keys = list(tiff_dict.keys())
        for key in keys[:1]:
            print(tiff_dict[key])

        # # Yolo 初始化
        # model = DarknetPredict()
        #
        # # 遍历切割细胞，识别细胞分类
        # for tiff_name, images_lst in tiff_dict.items():
        #     # 执行 Yolo 细胞分割
        #     seg_results = model.predict(images_lst)
        #
        #     # 将细胞分割结果写入文件
        #     xcep_pre = XceptionPreprocess(tiff_name)
        #     seg_csv = os.path.join(self.meta_files_path, tiff_name + "_seg.csv")
        #     xcep_pre.write_csv(seg_results, seg_csv)
        #
        #     # generate numpy array, it is the input of second stage classification algorithm
        #     cell_numpy, cell_index = xcep_pre.gen_np_array_csv(seg_csv=seg_csv)
        #
        #     # 执行细胞分类
        #     predictions = XceptionPredict().predict(cell_numpy)
        #
        #     # summarize two stages' result and generate a final csv
        #     clas = XceptionPostprocess()
        #     clas_dict = clas.convert_all(predictions=predictions, cell_index=cell_index)
        #     clas_csv = os.path.join(self.meta_files_path, tiff_name + "_clas.csv")
        #     clas.write_csv(clas_dict, clas_csv)
        #
        #     clas.cut_cells_p_marked(tiff_name, clas_dict, self.cell_path, factor=0.2, N=2)


if __name__ == "__main__":
    # 608 图像存储路径
    images_dir_path = '/home/tsimage/Development/DATA/remark'

    # 中间文件存放目录
    meta_files_path = '/home/tsimage/Development/DATA/meta'

    # 识别出的细胞存储路径
    cells_save_path = '/home/tsimage/Development/DATA/cells'

    PCK(images_dir_path, meta_files_path, cells_save_path).run()
