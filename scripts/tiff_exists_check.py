import os
import shutil
import sys
import openslide

sys.path.append('..')
from utils import generate_name_path_dict
from common.tslide.tslide import TSlide

TIFF_FILES_PATH = '/home/cnn/Development/DATA/TRAIN_DATA/TIFFS/20181025'

REMOTE_TIFF_PATH = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/0TIFF"


def main(file_path):
    tiff_dict = generate_name_path_dict(TIFF_FILES_PATH, ['.kfb'])
    remote_tiff_dict = generate_name_path_dict(REMOTE_TIFF_PATH, ['.kfb'])

    with open(file_path) as f:
        lines = f.readlines()
        items = [line.replace('\n', '') for line in lines]

    miss_tiff_lst = []
    for item in items:
        if item not in tiff_dict:
            miss_tiff_lst.append(item)
            remote_file_path = remote_tiff_dict[item]
            print("COPY FILE ...\nFROM %s\nTO %s" % (remote_file_path, TIFF_FILES_PATH))
            shutil.copy(remote_file_path, TIFF_FILES_PATH)
            # raise Exception('TIFF %s IS NOT FOUND IN LOCAL RESOURCE' % item)

        # path = tiff_dict[item]
        # try:
        #     try:
        #         slide = openslide.OpenSlide(path)
        #     except:
        #         slide = TSlide(path)
        # except Exception as e:
        #     raise Exception("%s %s" % (item, str(e)))

    print('\n'.join(miss_tiff_lst))


if __name__ == '__main__':
    main('work_tiff_list_01.txt')
