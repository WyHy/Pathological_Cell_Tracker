import os
import shutil


def load_dict(file_path):
    with open(file_path) as f:
        lines = f.readlines()

        dict_ = {}
        for line in lines:
            key, value = line.replace('\n', '').split('\t')
            key = key.replace(' ', '-')
            dict_[key] = value

        return dict_


def do_collect_by_tiff_type(path, dict_):
    """
    根据类别及分类别数量限制收集分类图像
    :param path: CELLS 文件路径
    :param dict_:  TIFF 文件名及对应 诊断结果 dict
    :return:
    """
    files = os.listdir(path)
    total = len(files)
    for index, tiff in enumerate(files):
        print("%s / %s ..." % (index + 1, total))
        src_root_dir = os.path.join(path, tiff)
        types = os.listdir(src_root_dir)
        for item in types:
            if tiff in dict_:
                label = dict_[tiff]
            else:
                label = "Unknown"

            label = label.replace("/", "-")
            src_path = os.path.join(src_root_dir, item)
            dst_path = os.path.join(os.path.dirname(path), 'TO_BE_CHECK_CELLS', label, tiff, item)
            shutil.copytree(src_path, dst_path)


if __name__ == '__main__':
    cell_path = '/home/cnn/Development/DATA/TRAIN_DATA/TIFFS/201811132110_FULL_TEST/CELLS'
    dict_path = 'name_and_labels_production_test.txt'
    do_collect_by_tiff_type(cell_path, load_dict(dict_path))
