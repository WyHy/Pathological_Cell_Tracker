# coding: utf-8
import csv
import os
import re
from xml.dom.minidom import parse, parseString
import xml.etree.ElementTree as ET
import copy

# CSV 文件路径
CSV_FILES_PATH = 'C:/tmp/csv'

# 图像尺寸
IMAGE_SIZE = 608

# XML 文件写入路径
XML_SAVE_PATH = 'C:/tmp/xmls'

if not os.path.exists(XML_SAVE_PATH):
    os.makedirs(XML_SAVE_PATH)


def cal_IOU(ret01, ret02):
    """
    计算矩阵重叠率
    :param ret01: 矩阵01 （x1, y1, w1, h1）
    :param ret02: 矩阵01 （x2, y2, w2, h2）
    :return: 矩阵重叠率 ratio
    """

    x1, y1, w1, h1 = ret01
    x1, y1, w1, h1 = int(x1), int(y1), int(w1), int(h1)

    x2, y2, w2, h2 = ret02
    x2, y2, w2, h2 = int(x2), int(y2), int(w2), int(h2)

    endx = max(x1 + w1, x2 + w2)
    startx = min(x1, x2)
    w = w1 + w2 - (endx - startx)

    endy = max(y1 + h1, y2 + h2)
    starty = min(y1, y2)
    h = h1 + h2 - (endy - starty)

    if w <= 0 or h <= 0:
        ratio = 0
    else:
        area = w * h
        area01 = w1 * h1
        area02 = w2 * h2
        ratio = area / (area01 + area02 - area)

    return ratio


class FilesScanner(object):
    """
    获取文件列表工具类
    """

    def __init__(self, files_path, postfix=None):
        """

        :param files_path: 待扫描文件路径
        :param postfix: 所需文件后缀，默认为空，即获取该路径下所有文件
        """
        self.files_path = files_path

        files = []
        if os.path.isfile(files_path):
            if postfix:
                if files_path.endswith(postfix):
                    files.append(files_path)
            else:
                files.append(files_path)

        if os.path.isdir(files_path):
            for root, dirs, filenames in os.walk(files_path):
                for filename in filenames:
                    if postfix:
                        if filename.endswith(postfix):
                            files.append(os.path.join(root, filename))
                    else:
                        files.append(os.path.join(root, filename))
        # 替换为绝对路径
        files = [os.path.abspath(item) for item in files]

        self.files = files

    def get_files(self):
        return self.files


def read_from_xml(xml_files_path):
    """
    读入 xml 文件标注点信息
    :param xml_files_path:
    :return:
    """
    tree = parse(xml_files_path)
    collection = tree.documentElement

    # 标注点数组
    lst = []

    objects = collection.getElementsByTagName("object")
    for index, obj in enumerate(objects):
        name = obj.getElementsByTagName('name')[0].childNodes[0].data
        box = obj.getElementsByTagName('bndbox')[0]
        xmin = box.getElementsByTagName('xmin')[0].childNodes[0].data
        ymin = box.getElementsByTagName('ymin')[0].childNodes[0].data
        xmax = box.getElementsByTagName('xmax')[0].childNodes[0].data
        ymax = box.getElementsByTagName('ymax')[0].childNodes[0].data

        xmin, ymin, xmax, ymax = int(xmin), int(ymin), int(xmax), int(ymax)
        lst.append((name, xmin, ymin, xmax - xmin, ymax - ymin))
        # lst.append({
        #     "type": name,
        #     "x": xmin,
        #     "y": ymin,
        #     "w": xmax - xmin,
        #     "h": ymax - ymin,
        # })

    return lst


def write_to_xml(points_dict):
    """
    将标注点信息写入 xml 文件
    :param points_dict:
    :return:
    """

    count = 0
    total = len(points_dict)

    for key, lst in points_dict.items():
        count += 1
        print("GENERATE %s / %s %s ..." % (count, total, key + '.xml'))
        root = ET.Element("annotation")
        ET.SubElement(root, "folder").text = "folder"
        ET.SubElement(root, "filename").text = key + ".jpg"
        ET.SubElement(root, "path").text = "path"

        source = ET.SubElement(root, "source")
        ET.SubElement(source, "database").text = "Unknown"

        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(IMAGE_SIZE)
        ET.SubElement(size, "height").text = str(IMAGE_SIZE)
        ET.SubElement(size, "depth").text = "3"

        ET.SubElement(root, "segmented").text = "0"

        for point in lst:
            object = ET.SubElement(root, "object")
            ET.SubElement(object, "name").text = point['name']
            ET.SubElement(object, "pose").text = "Unspecified"
            ET.SubElement(object, "truncated").text = "0"
            ET.SubElement(object, "difficult").text = "0"
            bndbox = ET.SubElement(object, "bndbox")
            ET.SubElement(bndbox, "xmin").text = str(int(point['xmin']))
            ET.SubElement(bndbox, "ymin").text = str(int(point['ymin']))
            ET.SubElement(bndbox, "xmax").text = str(int(point['xmax']))
            ET.SubElement(bndbox, "ymax").text = str(int(point['ymax']))

        raw_string = ET.tostring(root, "utf-8")
        reparsed = parseString(raw_string)
        with open(os.path.join(XML_SAVE_PATH, key + ".xml"), "w") as o:
            o.write(reparsed.toprettyxml(indent="\t"))


def write_xml(csv_files_path=CSV_FILES_PATH):
    """
    将 csv 文件内容写入 xml
    :param csv_files_path:
    :return:
    """
    files = FilesScanner(csv_files_path, postfix=".csv").get_files()
    clas_files = [item for item in files if item.endswith('_clas.csv')]

    for file in clas_files:
        with open(file) as f:
            lines = csv.reader(f)

            dict_ = {}
            next(lines, None)

            for line in lines:
                key = line[0]
                box = {
                    'name': line[3],
                    'xmin': 0 if float(line[5]) < 0 else int(float(line[5]) + 0.5),
                    'ymin': 0 if float(line[6]) < 0 else int(float(line[6]) + 0.5),
                    'xmax': 0 if float(line[7]) < 0 else int(float(line[7]) + 0.5),
                    'ymax': 0 if float(line[8]) < 0 else int(float(line[8]) + 0.5),
                }

                if not key in dict_:
                    dict_[key] = [box]
                else:
                    dict_[key].append(box)

            write_to_xml(dict_)


def merge_tiff_xmls(xml_path_lst):
    """
    合并归属同一大图的 xml
    :param xml_path_lst:  xml 文件路径列表
    :return:
    """

    label_lst = []
    for path in xml_path_lst:
        label_lst.extend(read_from_xml(path))

    new_lst = []
    for point in label_lst:
        type01, x01, y01, w01, h01 = point
        for item in new_lst:
            type02, x02, y02, w02, h02 = item
            if cal_IOU((x02, y02, w02, h02), (x01, y01, w01, h01)) > 0.8:
                break
        else:
            new_lst.append(point)

    return new_lst


def compare_and_process(dict01, dict02):
    """
    比较新旧标注点，识别出
    1. 原始漏标的细胞
    2. 算法诊断与原始标注类别不一致的细胞
    3. 新识别的细胞
    4. 原始标注的小宝
    :param dict01: 原有手工标注细胞
    :param dict02:  新模型识别细胞
    :return:
    """

    # 1. 新模型漏标细胞
    dict_miss = {}

    # 2. 新模型与原始手工分类不一致细胞
    dict_modify = {}

    # 3. 新模型新识别细胞
    dict_new = {}

    # 4. 原始细胞分类
    dict_old = copy.deepcopy(dict01)

    for key, lst02 in dict02.items():
        if key in dict01:
            lst01 = dict01[key]
        else:
            raise Exception("%s IS NOT FOUND IN DICT01")

        miss_lst = []
        for item02 in lst02:
            type02, x02, y02, w02, h02 = item02
            for item01 in lst01:
                type01, x01, y01, w01, h01 = item01

                # 判断是否为同一细胞
                if cal_IOU((x02, y02, w02, h02), (x01, y01, w01, h01)) > 0.5:
                    # 判断类别是否一致
                    if type02 != type01:
                        if key in dict_modify:
                            dict_modify[key].append(item02)
                        else:
                            dict_modify[key] = [item02]
                else:
                    continue
            else:
                # 新识别细胞
                if key in dict_new:
                    dict_new[key].append(item02)
                else:
                    dict_new[key] = [item02]

        # 漏标细胞
        if len(miss_lst) > 0:
            if key in dict_miss:
                dict_miss[key].extend(miss_lst)
            else:
                dict_miss[key] = miss_lst


if __name__ == '__main__':
    # write_xml()

    xml_files_path = 'C:/tmp/xmls'
    files = FilesScanner(xml_files_path, postfix=".xml").get_files()

    # 2017-09-07-09_47_42_9202_35031.xml
    pattern = re.compile(r'^(.*?)_(\d+)_(\d+).xml$')
    dict_ = {}
    for file in files:
        basename = os.path.basename(file)
        key, x, y = re.findall(pattern, basename)

        if key in dict_:
            dict_[key].append(file)
        else:
            dict_[key] = [file]

    for key, lst in dict_.items():
        merge_tiff_xmls(lst)

