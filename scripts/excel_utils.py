# coding: utf-8
import json
import os

import xlrd


def read_xls(path):
    # 打开指定路径中的xls文件
    xlsfile = "./40张_河南.xlsx"

    # 得到Excel文件的book对象，实例化对象
    book = xlrd.open_workbook(path)

    # 通过sheet索引获得sheet对象
    sheet0 = book.sheet_by_index(0)

    # 获得指定索引的sheet表名字
    sheet_name = book.sheet_names()[0]

    # 通过sheet名字来获取，当然如果知道sheet名字就可以直接指定
    sheet1 = book.sheet_by_name(sheet_name)

    # 获取行总数
    nrows = sheet0.nrows

    dict_ = {}
    for i in range(1, nrows):
        key, label, *_ = sheet1.row_values(i)
        dict_[key] = label

    return dict_

    # with open('DIAGNOSE_RESULT_DICT.txt', 'w') as o:
    #     for key, value in dict_.items():
    #         o.write("%s\t%s\n" % (key.encode('utf-8').decode('utf-8'), json.dumps(value)))

# with open('DIAGNOSE_RESULT_DICT.txt') as f:
#     lines = f.readlines()

# 病理类别
# CLASSES = ["ASCUS", "LSIL", "ASCH", "HSIL", "SCC", "AGC", "EC", "FUNGI", "TRI", "CC", "ACTINO", "VIRUS", "MC", "SC",
#            "RC", "GEC", ]
# # AGC
# AGC_CLASSES = ['AGC1', 'AGC2', 'AGC3', 'ADC']
#
#
# def is_element_in_dict(ele, dict_):
#     return ele in dict_
#
#
# tiff_dict = {}
# # 循环打印每一行的内容
# for i in range(1, nrows):
#     c_type, key, cell_type, num, _ = sheet1.row_values(i)
#
#     if cell_type in AGC_CLASSES:
#         cell_type = 'AGC'
#
#     # if cell_type in CLASSES:
#     #     print(CLASSES.index(cell_type))
#     # else:
#     #     print(cell_type, sheet1.row_values(i))
#
#     if key in tiff_dict:
#         if tiff_dict[key]['type'] != c_type:
#             print(key, tiff_dict[key]['type'], c_type)
#             exit()
#
#         children = tiff_dict[key]['children']
#         if cell_type in children:
#             if cell_type == 'AGC':
#                 children[cell_type] += num
#             else:
#                 print(cell_type, children[cell_type])
#                 print(key, cell_type)
#                 exit()
#         else:
#             children[cell_type] = num
#     else:
#         try:
#             tiff_dict[key] = {'type': c_type, 'children': {cell_type: int(num)}}
#         except:
#             print(i + 1, cell_type, num)
#
# X = []
# Y = []
#
# for key, value in tiff_dict.items():
#     ret = value['type']
#     children = value['children']
#
#     lst = [0] * len(CLASSES)
#     for index, item in enumerate(CLASSES):
#         if item in children:
#             lst[index] = children[item]
#
#     if '+' in ret:
#         y_classes = ret.split('+')
#         for y_class in y_classes:
#             if not is_element_in_dict(y_class, CLASSES):
#                 print(y_class)
#                 exit()
#
#             Y.append(y_class)
#             X.append('\t'.join([str(int(ele)) for ele in lst]))
#     else:
#         if not is_element_in_dict(ret, CLASSES):
#             print(ret)
#             exit()
#
#         Y.append(ret)
#         X.append('\t'.join([str(int(ele)) for ele in lst]))
#
# print(Y)
# print(len(Y), len(X))
#
# with open('./data/Classes.txt', 'w') as o:
#     o.writelines(["%s\n" % ele for ele in CLASSES])
#
# with open('./data/Y.txt', 'w') as o:
#     o.writelines(["%s\n" % CLASSES.index(ele) for ele in Y])
#
# with open('./data/X.txt', 'w') as o:
#     o.writelines(["%s\n" % ele for ele in X])


# # 获取列总数
# ncols = sheet0.ncols
#
# # 获得第1行的数据列表
# row_data = sheet0.row_values(0)
#
# # 获得第1列的数据列表
# col_data = sheet0.col_values(0)
#
# # 通过坐标读取表格中的数据
# cell_value1 = sheet0.cell_value(0, 0)
#
# cell_value2 = sheet0.cell_value(0, 1)
