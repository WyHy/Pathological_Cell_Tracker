import os
import sys
import openslide

sys.path.append('..')
from utils import generate_name_path_dict
from common.tslide.tslide import TSlide

TIFF_FILES_PATH = '/home/cnn/Development/DATA/TRAIN_DATA/TIFFS'


def main(file_path):
    tiff_dict = generate_name_path_dict(TIFF_FILES_PATH, ['.kfb'])
    with open(file_path) as f:
        lines = f.readlines()
        items = [line.replace('\n', '') for line in lines]

    for item in items:
        if item not in tiff_dict:
            raise Exception('TIFF %s IS NOT FOUND IN LOCAL RESOURCE' % item)

        path = tiff_dict[item]
        try:
            try:
                slide = openslide.OpenSlide(path)
            except:
                slide = TSlide(path)
        except Exception as e:
            raise Exception("%s %s" % (item, str(e)))


if __name__ == '__main__':
    main('work_tiff_list')
