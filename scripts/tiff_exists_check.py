import os
import shutil
import sys
import openslide

sys.path.append('..')
from common.tslide.tslide import TSlide
from utils import generate_name_path_dict, FilesScanner

TIFF_FILES_PATH = '/home/cnn/Development/DATA/TRAIN_DATA/TIFFS/20181026'

REMOTE_TIFF_PATH = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/0TIFF"


def tiff_readable_check(path):
    """
    病理图像可读性验证
    :param path: 原图路径
    :return:
    """

    files = FilesScanner(path, ['.tif', 'kfb']).get_files()
    filename_lst = []
    filepath_lst = []

    for file in files:
        basename = os.path.basename(file)

        if basename in filename_lst:
            raise Exception("%s\n%s" % (file, filepath_lst[filename_lst.index(basename)]))
        else:
            filename_lst.append(basename)
            filepath_lst.append(file)

    for file in files:
        try:
            try:
                slide = openslide.OpenSlide(file)
            except:
                slide = TSlide(file)
        except Exception as e:
            raise Exception("%s %s" % (file, str(e)))


def get_and_download(file_path):
    tiff_dict = generate_name_path_dict(TIFF_FILES_PATH, ['.kfb', '.tif'])
    remote_tiff_dict = generate_name_path_dict(REMOTE_TIFF_PATH, ['.kfb', '.tif'])

    with open(file_path) as f:
        lines = f.readlines()
        items = [line.replace('\n', '').replace(' ', '-') for line in lines]

    miss_tiff_lst = []

    total = len(items)
    for index, item in enumerate(items):
        print("%s / %s" % (index + 1, total))
        if item not in tiff_dict:
            miss_tiff_lst.append(item)
            remote_file_path = remote_tiff_dict[item]
            print("COPY FILE ...\nFROM %s\nTO %s" % (remote_file_path, TIFF_FILES_PATH))
            shutil.copy(remote_file_path, TIFF_FILES_PATH)
            # raise Exception('TIFF %s IS NOT FOUND IN LOCAL RESOURCE' % item)
        else:
            print("%s IS ALREADY EXIST!" % item)
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
    # 检查文件名是否有重复
    # tiff_readable_check(REMOTE_TIFF_PATH)

    get_and_download('work_tiff_list_20181026.txt')
