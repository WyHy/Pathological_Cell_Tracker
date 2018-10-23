import os
import re

pattern = re.compile(r'(.*?)([A-Z]{2}\d{8})')


def get_parent_list(parent_dir_path):
    lst = os.listdir(parent_dir_path)
    for item in lst:
        prefix, name = re.findall(pattern, item)[0]
        print(name)


if __name__ == '__main__':
    parent_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181022/CELLS/TIFFS_CHECKED'
    get_parent_list(parent_dir_path)
