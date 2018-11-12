import csv
import os

NORMAL_CATEGORY = ["MC", 'RC', 'SC', 'GEC']
ABNORMAL_CATEGORY = ["LSIL", "HSIL", "SCC", "ASCUS", "ASCH",
                     "LSIL_F", "LSIL_E", "HSIL_S", "HSIL_M", "HSIL_B", "SCC_G", "SCC_R", "EC", "AGC", "FUNGI", "TRI",
                     "CC", "ACTINO", "VIRUS"]

SQUA_CELL_CATEGORY = ["LSIL", "HSIL", "SCC", "ASCUS", "ASCH",
                      "LSIL_F", "LSIL_E", "HSIL_S", "HSIL_M", "HSIL_B", "SCC_G", "SCC_R"]
GLAND_CELL_CATEGORY = ['EC', 'AGC']
INFECT_CELL_CATEGORY = ["FUNGI", "TRI", "CC", "ACTINO", "VIRUS"]

IMPACT_CATEGORY_THRESH_DICT = {
    "LSIL": 0.7,
    "HSIL": 0.7,
    "SCC": 0.7,
    "ASCUS": 0.7,
    "ASCH": 0.7,

    "LSIL_F": 0.7,
    "LSIL_E": 0.7,
    "HSIL_S": 0.7,
    "HSIL_M": 0.7,
    "HSIL_B": 0.7,
    "SCC_G": 0.7,
    "SCC_R": 0.7,
    "EC": 0.7,
    "AGC": 0.7,
    "FUNGI": 0.7,
    "TRI": 0.7,
    "CC": 0.7,
    "ACTINO": 0.7,
    "VIRUS": 0.7,
}

IMPACT_CATEGORY_CELL_COUNT_DICT = {
    "LSIL": 30,
    "HSIL": 5,
    "SCC": 7,
    "ASCUS": 30,
    "ASCH": 10,

    "LSIL_F": 30,
    "LSIL_E": 5,
    "HSIL_S": 5,
    "HSIL_M": 10,
    "HSIL_B": 3,
    "SCC_G": 7,
    "SCC_R": 7,
    "EC": 3,
    "AGC": 10,
    "FUNGI": 5,
    "TRI": 150,
    "CC": 300,
    "ACTINO": 150,
    "VIRUS": 150,
}


def read_clas_xmls(csv_path):
    with open(csv_path) as f:
        lines = csv.reader(f)

        points_lst = []

        next(lines, None)
        for line in lines:
            name, label01, accu01, label02, accu02, xmin, ymin, w, h = line
            accu01, accu02, xmin, ymin, w, h = float(accu01), float(accu02), float(xmin), float(ymin), float(w), float(h)
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


def squa_decision(clas_18, cell_count_dict):
    """

    :param clas_18:
    :param cell_count_dict:
    :return: label
    """
    impact_category = []

    for item in SQUA_CELL_CATEGORY:
        cell_count = len(clas_18[item])
        if cell_count == 0:
            continue

        # if cell_count > cell_count_dict[item]:
        impact_category.append((item, cell_count))

    impact_category = sorted(impact_category, key=lambda category: category[1], reverse=True)

    return [category for category in impact_category[:3]]


def infect_decision(clas_18, cell_count_dict):
    """

    :param clas_18:
    :param cell_count_dict:
    :return: label
    """
    category_max_label = None
    category_max_count = 0

    for item in INFECT_CELL_CATEGORY:
        cell_count = len(clas_18[item])
        # if cell_count > cell_count_dict[item]:
        if cell_count > category_max_count:
            category_max_label = item
            category_max_count = cell_count

    return (category_max_label, category_max_count) if category_max_label else None


def gland_decision(clas_18, cell_count_dict):
    """

    :param clas_18:
    :param cell_count_dict:
    :return: label
    """
    category_max_label = None
    category_max_count = 0

    for item in GLAND_CELL_CATEGORY:
        cell_count = len(clas_18[item])
        # if cell_count > cell_count_dict[item]:
        if cell_count > category_max_count:
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

    return [res_squa, res_infect, res_gland]


def gen_categories_normal_4(points_lst):
    """

    :param points_lst:
    :return:
    """

    normal_dict = {}
    for item in NORMAL_CATEGORY:
        normal_dict[item] = []

    [normal_dict[point['xception']['label']].append(point) for point in points_lst if point['xception']['label'] in normal_dict]

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
        label_yolo, acc_yolo, label_xcp, acc_xcp = point['yolo']['label'], point['yolo']['accuracy'], point['xception']['label'], point['xception']['accuracy']
        if label_yolo != label_xcp:
            continue

        p_mix = (acc_yolo + acc_xcp) / 2
        if p_mix > threshes_dict[label_xcp]:
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


if __name__ == '__main__':
    csv_path = 'C:/Users/graya/Desktop/test'
    files = os.listdir(csv_path)
    for file in files:
        points_lst = read_clas_xmls(os.path.join(csv_path, file))
        result = slide_diagnose(points_lst, IMPACT_CATEGORY_THRESH_DICT)

        print(file, result)
