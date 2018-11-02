import os
import re
import sys

sys.path.append("..")

from utils import FilesScanner

TRAIN_DATA = '/home/data_samba/DATA/4TRAIN_DATA/20181026/DATA_FOR_TRAIN/CELLS'

# 2018-03-22-11_26_58_x3223_y30268_w163_h145_s354.jpg
PATTERN = re.compile(r'(.*?)_x(\d+)_y(\d+)_w(\d+)_h(\d+)_s(\d+).jpg')

SELECTED = ['AGC', 'VIRUS', 'EC', 'FUNGI', 'ACTINO']


def collect(path):
    lst = []

    images = FilesScanner(path).get_files()
    for image in images:
        basename = os.path.basename(image)
        ctype = os.path.basename(os.path.dirname(image))

        if ctype in SELECTED:
            tiff_name, x, y, w, h, s = re.findall(PATTERN, basename)[0]
            if tiff_name not in lst:
                lst.append(tiff_name)

    with open("work_tiff_list_20181102_SELECTED.txt", 'w') as o:
        o.write("%s" % ("\n".join(lst)))


def collect_tiff_ctype_collection(path):
    dict_ = {}

    images = FilesScanner(path).get_files()
    for image in images:
        basename = os.path.basename(image)
        tiff_name, x, y, w, h, s = re.findall(PATTERN, basename)[0]

        ctype = os.path.basename(os.path.dirname(image))

        if tiff_name in dict_:
            lst = dict_[tiff_name]
        else:
            lst = []

        if ctype in lst:
            pass
        else:
            lst.append(ctype)

        dict_[tiff_name] = lst

    with open('tiff_children_distribution.txt', 'w') as o:
        for key, lst in dict_.items():
            o.write("%s\t%s\n" % (key, "\t".join(lst)))


if __name__ == '__main__':
    # collect(TRAIN_DATA)
    collect_tiff_ctype_collection(TRAIN_DATA)
