import csv
import os

import xlrd

NORMAL_CATEGORY = ["MC", 'RC', 'SC', 'GEC']
ABNORMAL_CATEGORY = ["LSIL", "HSIL", "SCC", "ASCUS", "ASCH",
                     "LSIL_F", "LSIL_E", "HSIL_S", "HSIL_M", "HSIL_B", "SCC_G", "SCC_R", "EC", "AGC", "FUNGI", "TRI",
                     "CC", "ACTINO", "VIRUS", "ASCUS", "TRASH"]

SQUA_CELL_CATEGORY = ["LSIL", "HSIL", "SCC", "ASCH",
                      "ASCUS", "LSIL_F", "LSIL_E", "HSIL_S", "HSIL_M", "HSIL_B", "SCC_G", "SCC_R"]
GLAND_CELL_CATEGORY = ['EC', 'AGC']
INFECT_CELL_CATEGORY = ["FUNGI", "TRI", "CC", "ACTINO", "VIRUS"]

SQUA_THRESH = 0
INFECT_THRESH = 50
GRAND_THRESH = 20

IMPACT_CATEGORY_THRESH_DICT = {
    "LSIL": 0.9,
    "HSIL": 0.9,
    "SCC": 0.9,
    "ASCUS": 0.9,
    "ASCH": 0.9,

    "LSIL_F": 0.9,
    "LSIL_E": 0.9,
    "HSIL_S": 0.9,
    "HSIL_M": 0.9,
    "HSIL_B": 0.9,
    "SCC_G": 0.9,
    "SCC_R": 0.9,
    "EC": 0.9,
    "AGC": 0.9,
    "FUNGI": 0.9,
    "TRI": 0.9,
    "CC": 0.9,
    "ACTINO": 0.9,
    "VIRUS": 0.9,
    "ASCUS": 0.9,
    "TRASH": 0.0,
}

IMPACT_CATEGORY_CELL_COUNT_DICT = {
    "LSIL": 250,
    "HSIL": 5,
    "SCC": 7,
    "ASCUS": 30,
    "ASCH": 10,

    "LSIL_F": 17,
    "LSIL_E": 4,
    "HSIL_S": 7,
    "HSIL_M": 5,
    "HSIL_B": 5,
    "SCC_G": 7,
    "SCC_R": 7,
    "EC": 3,
    "AGC": 10,
    "FUNGI": 5,
    "TRI": 300,
    "CC": 300,
    "ACTINO": 150,
    "VIRUS": 150,
    "ASCUS": 1,
    "TRASH": 1,
}


def read_xls(path):
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
        key, label = sheet1.row_values(i)
        dict_[key] = label

    return dict_


def read_clas_xmls(csv_path):
    with open(csv_path) as f:
        lines = csv.reader(f)

        points_lst = []

        next(lines, None)
        for line in lines:
            name, label01, accu01, label02, accu02, xmin, ymin, w, h = line
            accu01, accu02, xmin, ymin, w, h = float(accu01), float(accu02), float(xmin), float(ymin), float(w), float(
                h)
            x0, y0 = [int(item) for item in name.split('_')]

            x, y = xmin + x0, ymin + y0
            points_lst.append({
                "yolo": {
                    "label": label01,
                    "accuracy": accu01,
                },
                "xception": {
                    "label": label02,
                    "accuracy": accu02,
                },
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            })

    return points_lst


def squa_decision(clas_18, cell_count_dict, thr=SQUA_THRESH):
    """

    :param clas_18:
    :param cell_count_dict:
    :return: label
    """
    impact_category_dict = {}

    for item in SQUA_CELL_CATEGORY:
        cell_count = len(clas_18[item])
        if cell_count <= thr:
            continue

        impact_category_dict[item] = cell_count

    if not impact_category_dict:
        return None
    # print(impact_category_dict)

    impact_category_lst = sorted(impact_category_dict.items(), key=lambda category: category[1], reverse=True)
    print(impact_category_lst)

    if 'SCC_R' in impact_category_dict and impact_category_dict['SCC_R'] >= cell_count_dict['SCC_R']:
        return "SCC", impact_category_lst

    if 'SCC_G' in impact_category_dict and impact_category_dict['SCC_G'] >= cell_count_dict['SCC_G']:
        return "SCC", impact_category_lst

    if 'HSIL_S' in impact_category_dict and impact_category_dict['HSIL_S'] >= cell_count_dict['HSIL_S']:
        return "HSIL", impact_category_lst

    if 'LSIL_E' in impact_category_dict and impact_category_dict['LSIL_E'] >= cell_count_dict['LSIL_E']:
        return "LSIL", impact_category_lst

    if impact_category_lst[0][0] == 'ASCUS':
        if 'LSIL_F' in impact_category_dict and impact_category_dict['LSIL_F'] >= cell_count_dict['LSIL']:
            return "LSIL", impact_category_lst

        if 'LSIL_E' in impact_category_dict and impact_category_dict['LSIL_E'] >= cell_count_dict['LSIL_E']:
            return 'LSIL', impact_category_lst

        if ('LSIL_E' in impact_category_dict and impact_category_dict['LSIL_E'] < cell_count_dict['LSIL_E']) and (
                'LSIL_F' in impact_category_dict and impact_category_dict['LSIL_F'] < cell_count_dict['LSIL_F']):
            return 'ASCUS', impact_category_lst

        if ('LSIL_E' not in impact_category_dict or (
                'LSIL_E' in impact_category_dict and impact_category_dict['LSIL_E'] < cell_count_dict['LSIL_E'])) and (
                'LSIL_F' not in impact_category_dict or (
                'LSIL_F' in impact_category_dict and impact_category_dict['LSIL_F'] < cell_count_dict['LSIL_F'])):
            return "NORMAL", impact_category_lst

        return 'ASCUS', impact_category_lst

    if impact_category_lst[0][0] == 'LSIL_E':
        return 'LSIL', impact_category_lst

    if impact_category_lst[0][0] == 'LSIL_F':
        if 'HSIL_B' in impact_category_dict and impact_category_dict['HSIL_B'] >= cell_count_dict['HSIL_B']:
            return "ASCH", impact_category_lst

        if 'HSIL_M' in impact_category_dict and impact_category_dict['HSIL_M'] >= cell_count_dict['HSIL_M']:
            return "ASCH", impact_category_lst

        if 'LSIL_E' in impact_category_dict and impact_category_dict['LSIL_E'] >= cell_count_dict['LSIL_E']:
            return 'LSIL', impact_category_lst

        if impact_category_dict['LSIL_F'] < cell_count_dict['LSIL_F'] and "ASCUS" not in impact_category_dict:
            return None

        if impact_category_dict['LSIL_F'] >= cell_count_dict['LSIL']:
            return "LSIL", impact_category_lst

        return 'ASCUS', impact_category_lst

    if impact_category_lst[0][0] == 'HSIL_S':
        if ('SCC_R' in impact_category_dict and impact_category_dict['SCC_R'] >= cell_count_dict['SCC_R']) or (
                'SCC_G' in impact_category_dict and impact_category_dict['SCC_G'] >= cell_count_dict['SCC_G']):
            return 'SCC', impact_category_lst

        return 'HSIL', impact_category_lst

    if impact_category_lst[0][0] == 'HSIL_M':
        if ('SCC_R' in impact_category_dict and impact_category_dict['SCC_R'] >= cell_count_dict['SCC_R']) or (
                'SCC_G' in impact_category_dict and impact_category_dict['SCC_G'] >= cell_count_dict['SCC_G']):
            return 'SCC', impact_category_lst

        if 'HSIL_S' in impact_category_dict:
            if impact_category_dict['HSIL_S'] >= cell_count_dict['HSIL_S']:
                return 'HSIL', impact_category_lst
            else:
                return "ASCH", impact_category_lst

    if impact_category_lst[0][0] == 'HSIL_B':
        if ('SCC_R' in impact_category_dict and impact_category_dict['SCC_R'] >= cell_count_dict['SCC_R']) or (
                'SCC_G' in impact_category_dict and impact_category_dict['SCC_G'] >= cell_count_dict['SCC_G']):
            return 'SCC', impact_category_lst

        if 'HSIL_S' in impact_category_dict:
            if impact_category_dict['HSIL_S'] >= cell_count_dict['HSIL_S']:
                return 'HSIL', impact_category_lst
            else:
                return "ASCH", impact_category_lst

    if impact_category_lst[0][0] == 'SCC_G':
        if impact_category_dict['SCC_G'] >= cell_count_dict['SCC_G']:
            return 'SCC', impact_category_lst

    if impact_category_lst[0][0] == 'SCC_R':
        if impact_category_dict['SCC_R'] >= cell_count_dict['SCC_R']:
            return 'SCC', impact_category_lst

    return None


def infect_decision(clas_18, cell_count_dict, thr=INFECT_THRESH):
    """

    :param clas_18:
    :param cell_count_dict:
    :return: label
    """
    category_max_label = None
    category_max_count = thr

    for item in INFECT_CELL_CATEGORY:
        cell_count = len(clas_18[item])
        # if cell_count >= cell_count_dict[item]:
        if cell_count >= category_max_count:
            category_max_label = item
            category_max_count = cell_count

    return (category_max_label, category_max_count) if category_max_label else None


def gland_decision(clas_18, cell_count_dict, thr=GRAND_THRESH):
    """

    :param clas_18:
    :param cell_count_dict:
    :return: label
    """
    category_max_label = None
    category_max_count = thr

    for item in GLAND_CELL_CATEGORY:
        cell_count = len(clas_18[item])
        # if cell_count >= cell_count_dict[item]:
        if cell_count >= category_max_count:
            category_max_label = item
            category_max_count = cell_count

    return (category_max_label, category_max_count) if category_max_label else None


def diagnose_from_categories_18(clas_18):
    """

    :param clas_18:
    :return:
    """
    res_squa = squa_decision(clas_18, IMPACT_CATEGORY_CELL_COUNT_DICT)
    res_infect = infect_decision(clas_18, IMPACT_CATEGORY_CELL_COUNT_DICT)
    res_gland = gland_decision(clas_18, IMPACT_CATEGORY_CELL_COUNT_DICT)

    print("Squa Result: ", res_squa)
    print("Infect Result: ", res_infect)
    print("Gland Result: ", res_gland)

    result = "+".join([item[0] for item in [res_squa, res_infect, res_gland] if item])

    return result if result else "NORMAL"


def gen_categories_normal_4(points_lst):
    """

    :param points_lst:
    :return:
    """

    normal_dict = {}
    for item in NORMAL_CATEGORY:
        normal_dict[item] = []

    [normal_dict[point['xception']['label']].append(point) for point in points_lst if
     point['xception']['label'] in normal_dict]

    return normal_dict


def gen_categories_abnormal_14(points_lst, threshes_dict):
    """

    :param points_lst:
    :param threshes_dict:
    :return:
    """
    abnormal_dict = {}
    for item in ABNORMAL_CATEGORY:
        abnormal_dict[item] = []

    for point in points_lst:
        label_yolo, acc_yolo, label_xcp, acc_xcp = point['yolo']['label'], point['yolo']['accuracy'], point['xception'][
            'label'], point['xception']['accuracy']
        if label_yolo != label_xcp:
            if label_xcp in NORMAL_CATEGORY:
                continue

            pass

        # p_mix = (acc_yolo + acc_xcp) / 2
        p_mix = (acc_xcp + acc_xcp) / 2

        if p_mix >= threshes_dict[label_xcp]:
            abnormal_dict[label_xcp].append(point)

    return abnormal_dict


def gen_categories_18(points_lst, threshes_dict):
    """

    :param threshes_dict:
    :param points_lst:
    :return:
    """

    normal_dict = gen_categories_normal_4(points_lst)
    abnormal_dict = gen_categories_abnormal_14(points_lst, threshes_dict)

    return dict(abnormal_dict, **normal_dict)


def slide_diagnose(points_lst, threshes_dict):
    """

    :param threshes_dict:
    :param points_lst:
    :return:
    """

    clas_18 = gen_categories_18(points_lst, threshes_dict)
    result = diagnose_from_categories_18(clas_18)

    return result


def gen_slide_diagnose(csv_path):
    return slide_diagnose(read_clas_xmls(csv_path), IMPACT_CATEGORY_THRESH_DICT)


if __name__ == '__main__':
    csv_path = 'C:/Users/graya/Desktop/META'
    files = os.listdir(csv_path)

    xls_path = "../../scripts/89张_河南大会.xlsx"
    dict_ = read_xls(xls_path)

    for file in files:
        basename, _ = os.path.splitext(os.path.basename(file))
        basename = basename.replace("_clas", "")
        if basename in dict_:
            if file.endswith("_clas.csv"):
                points_lst = read_clas_xmls(os.path.join(csv_path, file))
                result = slide_diagnose(points_lst, IMPACT_CATEGORY_THRESH_DICT)

                basename, _ = os.path.splitext(os.path.basename(file))
                basename = basename.replace("_clas", "")
                print("==> FileName: %s, Our: %s, Zhu: %s" % (file, result, dict_[basename]))
                print("-----------------------")
