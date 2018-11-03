import os
import re
import shutil
import sys

sys.path.append('..')

from utils import cal_IOU, FilesScanner


def get_tiff_children_lst(path):
    """
    返回算法识别细胞分类及路径字典
    :param path:
    :return:
    """
    tiff_lst = os.listdir(path)

    dict_ = {}
    for tiff in tiff_lst:
        ctypes = os.listdir(os.path.join(path, tiff))

        lst = []
        for ctype in ctypes:
            lst.extend([(ctype, os.path.join(path, tiff, ctype, item)) for item in os.listdir(os.path.join(path, tiff, ctype))])

        dict_[tiff] = lst

    return dict_


def restore_tiff_children_lst(path):
    """
    返回训练数据 路径及细胞类别字典
    :param path:
    :return:
    """
    images = FilesScanner(path, ['.jpg']).get_files()
    print("TRAIN_DATA IMAGE COUNT: %s" % len(images))

    # TC18053113_x54903_y33619_w465_h522_s95.jpg
    pattern = re.compile(r'(.*?)_x(\d+)_y(\d+)_w(\d+)_h(\d+)_s(\d+).jpg')

    dict_ = {}
    for image in images:
        basename = os.path.basename(image)
        ctype = os.path.basename(os.path.dirname(image))

        print(basename)
        tiff_name, x, y, w, h, s = re.findall(pattern, basename)[0]
        if tiff_name in dict_:
            dict_[tiff_name].append((ctype, image))
        else:
            dict_[tiff_name] = [(ctype, image)]

    return dict_


if __name__ == '__main__':
    # DIAGNOSE_RESULT = load_dict('DIAGNOSE_RESULT_DICT.txt')
    # exit()

    cell_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181102_SELECTED/TO_BE_MERGE/'
    train_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181102_SELECTED/TRAIN_DATA/'
    merge_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181102_SELECTED/MERGE/'

    print('GENERATE CELL IMAGE DICT ...')
    cell_dict = get_tiff_children_lst(cell_dir_path)
    print('CELL DICT LENGTH = %s' % len(cell_dict))

    print('GENERATE TRAIN IMAGE DICT ...')
    train_dict = restore_tiff_children_lst(train_dir_path)
    print('TRAIN DICT LENGTH = %s' % len(train_dict))

    print('COMPARE AND COPY CELL IMAGE TO DST ...')
    keys = list(cell_dict.keys())
    total = len(keys)

    # 1-p0.0033_TC18018765_x28205_y36889_w41_h52_2x.jpg
    pattern01 = re.compile(r'.*?_x(\d+)_y(\d+)_w(\d+)_h(\d+)_?(\dx)?.jpg')
    pattern02 = re.compile(r'.*?_x(\d+)_y(\d+)_w(\d+)_h(\d+)_s(\d+).jpg')

    print(cell_dict.keys()[:20])
    print(train_dict.keys()[:20])
    for index, key in enumerate(keys):
        print("%s / %s %s ... " % (index + 1, total, key))

        lst01 = cell_dict[key]

        if key in train_dict:
            print(key)

        #     lst02 = train_dict[key]
        #
        #     for ctype01, path01 in lst01:
        #         basename = os.path.basename(path01)
        #         x01, y01, w01, h01, _ = re.findall(pattern01, basename)
        #
        #         for ctype02, path02 in lst02:
        #             basename = os.path.basename(path01)
        #             x02, y02, w02, h02, _ = re.findall(pattern02, basename)
        #
        #             ratio = cal_IOU((int(x01), int(y01), int(w01), int(h01)), (int(x02), int(y02), int(w02), int(h02)))
        #             if ratio > 0.5:
        #                 cell_save_path = os.path.join(merge_dir_path, key, ctype02)
        #                 if not os.path.exists(cell_save_path):
        #                     os.makedirs(cell_save_path)
        #
        #                 shutil.copy(path01, cell_save_path)
        #                 break
        #         else:
        #             cell_save_path = os.path.join(merge_dir_path, key, ctype01 + '_NEW')
        #             if not os.path.exists(cell_save_path):
        #                 os.makedirs(cell_save_path)
        #
        #             shutil.copy(path01, cell_save_path)
        # else:
        #     for ctype01, path01 in lst01:
        #         cell_save_path = os.path.join(merge_dir_path, key, ctype01 + '_NEW')
        #         if not os.path.exists(cell_save_path):
        #             os.makedirs(cell_save_path)
        #
        #         shutil.copy(path01, cell_save_path)
