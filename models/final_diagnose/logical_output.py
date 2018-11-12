import os
import csv

NORMAL_CATEGORY = ["MC", 'RC', 'SC', 'GEC']
ABNORMAL_CATEGORY = ["LSIL_F", "LSIL_E", "HSIL_S",  "HSIL_M", "HSIL_B", "SCC_G", "SCC_R", "EC", "AGC", "FUNGI", "TRI", "CC", "ACTINO", "VIRUS"]

SQUA_CELL_CATEGORY = []
INFECT_CELL_CATEGORY = []
GLAND_CELL_CATEGORY = []


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


def squa_decision(clas_18):
    pass


def infect_decision(clas_18):
    pass


def gland_decision(clas_18):
    """

    :param clas_18:
    :return:
    """
    pass


def diagnose_from_categories_18(clas_18):
    """

    :param clas_18:
    :return:
    """
    res_squa    = squa_decision(clas_18)
    res_infect  = infect_decision(clas_18)
    res_gland   = gland_decision(clas_18)

    return [res_squa, res_infect, res_gland]


def gen_categories_normal_4(points_lst):
    """

    :param points_lst:
    :return:
    """

    normal_dict = {}
    for item in NORMAL_CATEGORY:
        normal_dict[item] = []

    return [normal_dict[point['xception']['label']].append(point) for point in points_lst if point['xception']['label'] in normal_dict]


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
        label_yolo, acc_yolo, label_xcp, acc_xcp = points_lst['yolo']['label'], points_lst['yolo']['accuracy'], points_lst['xception']['label'], points_lst['xception']['accuracy']
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

    keys = list(threshes_dict.keys())
    normal_dict = gen_categories_normal_4(points_lst)
    abnormal_dict = gen_categories_abnormal_14(points_lst, threshes_dict)

    return abnormal_dict + normal_dict


def slide_diagnose(points_lst, threshes_dict):
    """

    :param threshes_dict:
    :param points_lst:
    :return:
    """

    clas_18 = gen_categories_18(points_lst, threshes_dict)

    result = diagnose_from_categories_18(clas_18)

    return result






