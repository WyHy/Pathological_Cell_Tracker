import os
import re
import sys

sys.path.append('..')

from utils import generate_name_path_dict

pattern = re.compile(r'(.*?)([A-Z]{2}\d{8})')


def parent_children_lst(parent_path):
    lst = generate_name_path_dict(parent_path, ['.jpg'])

    lst_ = []
    for item in lst:
        parent = os.path.dirname(item)
        cell_type = os.path.basename(parent)
        lst_.append({
            'path': item,
            'type': cell_type
        })

    return lst_


def get_parent_list(parent_dir_path):
    lst = os.listdir(parent_dir_path)

    dict_ = {}
    for item in lst:
        prefix, name = re.findall(pattern, item)[0]
        dict_[name] = os.path.join(parent_dir_path, item)

    return dict_


if __name__ == '__main__':
    auto_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181022/CELLS/TIFFS'
    manual_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181022/CELLS/TIFFS_CHECKED'

    auto_dict = get_parent_list(auto_dir_path)
    manual_dict = get_parent_list(manual_dir_path)

    for key in manual_dict:
        if key not in auto_dict:
            print("%s NOT FOUND" % key)
