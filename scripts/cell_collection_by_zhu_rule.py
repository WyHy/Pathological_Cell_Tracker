import json
import os
import re
import sys
import shutil

sys.path.append('..')

from utils import generate_name_path_dict, get_location_from_filename, cal_IOU

pattern = re.compile(r'(.*?)([A-Z]{2}\d{8})')
pattern01 = re.compile(r'(.*?)_?(\d{4}\-\d{2}\-\d{2} \d{2}_\d{2}_\d{2})')


def load_dict(file_path):
    with open(file_path) as f:
        lines = f.readlines()

        dict_ = {}
        for line in lines:
            key, value = line.replace('\n', '').split('\t')
            dict_[key.replace(' ', '-')] = json.loads(value)

        return dict_


def get_coordinate(point_path_lst):
    lst = []
    for item in point_path_lst:
        basename = os.path.basename(item['path'])
        point = get_location_from_filename(basename)
        if not point:
            print(basename)
            exit()

        _, x, y, w, h, _ = point
        lst.append((x, y, w, h))

    return lst


def parent_children_lst(parent_path):
    dict_ = generate_name_path_dict(parent_path, ['.jpg'])

    lst_ = []
    for key, path in dict_.items():
        parent = os.path.dirname(path)
        cell_type = os.path.basename(parent)
        lst_.append({
            'path': path,
            'type': cell_type
        })

    return lst_


def get_parent_list(parent_dir_path):
    lst = os.listdir(parent_dir_path)

    dict_ = {}
    for item in lst:
        name, _ = os.path.splitext(item)
        # prefix, name = re.findall(pattern, item)[0]
        dict_[name] = os.path.join(parent_dir_path, item)

    return dict_


if __name__ == '__main__':
    # DIAGNOSE_RESULT = load_dict('DIAGNOSE_RESULT_DICT.txt')
    # exit()
    
    auto_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181026_1/CELLS/20181026_1'
    manual_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181024/CELLS/TIFFS_CHECKED'
    merge_dir_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181026_1/CELLS/TIFFS_MERGED_20181026_1'

    print('GENERATE AUTO IMAGE DICT ...')
    auto_dict = get_parent_list(auto_dir_path)
    print('AUTO DICT LENGTH = %s' % len(auto_dict))
    print('GENERATE MANUAL IMAGE DICT ...')
    manual_dict = get_parent_list(manual_dir_path)
    print('MANUAL DICT LENGTH = %s' % len(manual_dict))

    auto_children_dict = {}
    manual_children_dict = {}

    print('GENERATE KEY <=> IMAGE_LST DICT ...')
    for key in auto_dict:
        auto_children_dict[key] = parent_children_lst(auto_dict[key])
        # if key in manual_dict:
        #     manual_children_dict[key] = parent_children_lst(manual_dict[key])

    DIAGNOSE_RESULT = load_dict('DIAGNOSE_RESULT_DICT.txt')

    print('COMPARE AND COPY CELL IMAGE TO DST ...')
    keys = list(auto_children_dict.keys())
    total = len(keys)
    for index, key in enumerate(keys):
        print("%s / %s %s ... " % (index + 1, total, key))

        parent = DIAGNOSE_RESULT[key]
        if parent['zhu'] != 42:
            parent_type = parent['zhu']
        else:
            if parent['doctor'] != 42:
                parent_type = parent['doctor']
            else:
                parent_type = "UNKNOWN"

        auto_point_lst = auto_children_dict[key]
        if key not in manual_children_dict:
            for item in auto_point_lst:
                path = item['path']
                cell_type = item['type']
                cell_save_path = os.path.join(merge_dir_path, parent_type, key, cell_type + '_NEW')
                if not os.path.exists(cell_save_path):
                    os.makedirs(cell_save_path)

                # 该图像不存在审核文件，直接拷贝图像至目标文件夹
                shutil.copy(path, cell_save_path)
        else:
            manual_point_lst = manual_children_dict[key]
            # 创建审核过的细胞存放路径
            for item in manual_point_lst:
                path = item['path']
                cell_type = item['type']

                cell_save_path = os.path.join(merge_dir_path, parent_type, key, cell_type)
                if not os.path.exists(cell_save_path):
                    os.makedirs(cell_save_path)

                shutil.copy(path, cell_save_path)

            # 检测算法识别细胞的坐标位置，进行重复性判断
            manual_point_coordinate_lst = get_coordinate(manual_point_lst)
            for point in auto_point_lst:
                basename = os.path.basename(point['path'])
                _, x, y, w, h, _ = get_location_from_filename(basename)

                # 与审核图像存在重复
                for item in manual_point_coordinate_lst:
                    if cal_IOU((x, y, w, h), item) > 0.8:
                        break
                else:
                    path = point['path']
                    cell_type = point['type']
                    cell_save_path = os.path.join(merge_dir_path, parent_type, key, cell_type + '_NEW')
                    if not os.path.exists(cell_save_path):
                        os.makedirs(cell_save_path)

                    # 该图像不存在对应审核图像，直接拷贝图像至目标文件夹
                    shutil.copy(path, cell_save_path)

