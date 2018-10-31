import os
import re
import shutil

import xlrd

DST_PATH = ""
PATTERN = re.compile(r'1\-p(0.\d{4}).*?.jpg')


def generate_task_lst(path, name):
    """
    读取 excel 文件，获取 TIFF 文件名
    :param path: excel 文件路径
    :return:
    """
    # 得到Excel文件的book对象，实例化对象
    book = xlrd.open_workbook(path)

    # 通过sheet索引获得sheet对象
    sheet = book.sheet_by_index(0)

    # 获取行总数
    nrows = sheet.nrows

    with open(name, 'w') as o:
        for i in range(1, nrows):
            tiff_name, tiff_type = sheet.row_values(i)
            if tiff_name:
                o.write("%s\n" % tiff_name)


def get_tiff_name_and_type(path):
    """
    读取 excel 文件，获取 TIFF 文件名及对应 诊断结果
    :param path:  excel 文件路径
    :return:
    """
    dict_ = {}
    # 得到Excel文件的book对象，实例化对象
    book = xlrd.open_workbook(path)

    # 通过sheet索引获得sheet对象
    sheet = book.sheet_by_index(0)

    # 获取行总数
    nrows = sheet.nrows

    for i in range(1, nrows):
        tiff_name, tiff_type = sheet.row_values(i)
        dict_[tiff_name.replace(" ", "-")] = tiff_type.upper()

    return dict_


def do_collect_by_tiff_type(path, dict_):
    """
    根据类别及分类别数量限制收集分类图像
    :param path: CELLS 文件路径
    :param dict_:  TIFF 文件名及对应 诊断结果 dict
    :return:
    """
    files = os.listdir(path)
    for tiff in files:
        src_root_dir = os.path.join(path, tiff)
        types = os.listdir(src_root_dir)
        for item in types:
            src_path = os.path.join(src_root_dir, item)
            images_lst = os.listdir(src_path)

            dst_path = os.path.join(DST_PATH, dict_[tiff], tiff, item)
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)

            if item == 'HSIL' and len(images_lst) > 500:
                # 按概率大小排序
                p_dict = {}
                for img in images_lst:
                    p = float(re.findall(PATTERN, img)[0][0])
                    p_dict[img] = p

                p_dict_sorted = sorted(p_dict.items(), key=lambda x: x[1])
                for key in p_dict_sorted[:500]:
                    shutil.copytree(os.path.join(src_path, key), dst_path)
            else:
                for img in images_lst:
                    shutil.copytree(os.path.join(src_path, img), dst_path)


if __name__ == '__main__':
    # excel 文件路径
    xls_path = 'WANGYING-auto_label_task_2018.10.27.xlsx'

    # 切图任务 TIFF 任务清单
    date_str = '20181031'
    name = 'work_tiff_list_%s.txt' % date_str

    # 生成任务清单
    generate_task_lst(xls_path, name)

    # # 按数量类别限制收集细胞审核图像
    # cell_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_%s/CELLS' % date_str
    # do_collect_by_tiff_type(cell_path, get_tiff_name_and_type(xls_path))
