# coding: utf-8

import os


def get_path_postfix(filename):
    """
    获取文件名和文件后缀
    :param filename: 待处理文件路径
    :return: (文件名， 文件后缀) 如：a.txt --> return ('a', '.txt')
    """
    basename = os.path.basename(filename)
    return os.path.splitext(basename)


class FilesScanner(object):
    """
    获取文件列表工具类
    """

    def __init__(self, files_path, postfix=None):
        """

        :param files_path: 待扫描文件路径
        :param postfix: 所需文件后缀，['.tif', '.kfb'], 默认为空，即获取该路径下所有文件
        """
        self.files_path = files_path

        if postfix:
            assert isinstance(postfix, list), 'argument [postfix] should be list'

        files = []
        if os.path.isfile(files_path):
            if postfix:
                _, ctype = get_path_postfix(files_path)
                if ctype in postfix:
                    files.append(files_path)
            else:
                files.append(files_path)

        if os.path.isdir(files_path):
            for root, dirs, filenames in os.walk(files_path):
                for filename in filenames:
                    if postfix:
                        _, ctype = get_path_postfix(filename)
                        if ctype in postfix:
                            files.append(os.path.join(root, filename))
                    else:
                        files.append(os.path.join(root, filename))
        # 替换为绝对路径
        files = [os.path.abspath(item) for item in files]

        self.files = files

    def get_files(self):
        return self.files


def generate_name_path_dict(path, postfix=None, output_file_path=None):
    """
    获取大图文件路径 key: value = 文件名：文件路径
    :param path: 待检索文件路径列表
    :param output_file_path: 将生成字典结果写入本地的文件路径，含文件名称
    :param postfix: 回收文件类型 ['.tif', '.kfb']
    :return: {filename: file_abs_path}
    """

    assert isinstance(path, (str, list)), 'argument [path] should be path or path list'

    files_collection = []

    if isinstance(path, list):
        for item in path:
            files_collection.extend(FilesScanner(item, postfix).get_files())
    else:
        files_collection = FilesScanner(path, postfix).get_files()

    dict_ = {}
    for file in files_collection:
        key, _ = os.path.splitext(os.path.basename(file))
        key = key.replace(" ", "-")

        if key in dict_:
            value = dict_[key]
            if value.endswith('.kfb'):
                pass
            else:
                dict_[key] = file
        else:
            dict_[key] = file

    # 如果存在输出路径则写入本地文件
    if output_file_path:
        with open(os.path.join(output_file_path), 'w') as f:
            for key, path in dict_.items():
                f.write('%s\t%s\n' % (key, path))

    return dict_


def get_tiff_dict():
    tif_path = '/home/tsimage/Development/DATA/tiff'
    return generate_name_path_dict(tif_path, ['.tif', '.kfb'])


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


def rm_duplicate_point(point_lst):
    """
    删除重合度较高的标注点坐标
    :param point_lst: 标注点坐标列表
    :return: 去重后的标注点坐标列表
    """

    return_lst = []
    pure_lst = []

    for point in point_lst:
        label, accuracy, center_x, center_y, w, h = point[0], point[1], point[2][0], point[2][1], point[2][2], point[2][3]
        x, y = center_x - (w / 2), center_y - (h / 2)
        for item in pure_lst:
            point_ = (x, y, w, h)
            if cal_IOU(item, point_) > 0.5:
                break
        else:
            pure_lst.append(point_)
            return_lst.append((label, accuracy, point_))

    return return_lst


