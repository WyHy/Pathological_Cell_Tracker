# coding: utf-8
import csv
import datetime
import os
import re
import shutil
import openslide
import requests

import xlrd

from common.tslide.tslide import TSlide


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
        label, accuracy, center_x, center_y, w, h = point[0], point[1], point[2][0], point[2][1], point[2][2], point[2][
            3]
        x, y = center_x - (w / 2), center_y - (h / 2)
        point_ = (x, y, w, h)

        for item in pure_lst:
            if cal_IOU(item, point_) > 0.5:
                break
        else:
            pure_lst.append(point_)
            return_lst.append((label, accuracy, point_))

    return return_lst


def get_processed_lst(clas_files_path, cell_images_path):
    clas_files = os.listdir(clas_files_path)
    cell_lst = os.listdir(cell_images_path)

    clas_lst = [item.replace("_clas.csv", "") for item in clas_files if item.endswith("_clas.csv")]

    print("CLAS FILES LENGTH: %s, IMAGE DIRS LENGTH: %s" % (len(clas_lst), len(cell_lst)))

    count = 0
    for item in clas_lst:
        if item in cell_lst:
            count += 1
        else:
            print(item)
            exit()

    print('GOT %s PROCESSED' % count)

    return clas_lst


def load_classes(path):
    with open(path) as f:
        lines = f.readlines()
        return [line.replace('\n', '') for line in lines]


def get_location_from_filename(filename_string):
    """
    通过正则表达式从文件名中解析细胞在大图位置
    :param filename_string: 细胞图像文件名
    :return: (image_name, x, y, w, h)
    """
    name = filename_string.replace(' - 副本', '').replace(' ', '').encode('utf-8').decode('utf-8')

    # 1-p0.0000_markedAs_ASCH_2017-10-27-16_12_50_x9659_y28027_w616_h331.jpg
    # 1-p0.0000_markedAs_CC_2018-03-27-23_18_27_x5675_y23431_w230_h207_4x.jpg
    # 1-p0.0000_markedAs_ACTINO_2018-06-20_18_37_06_x34602_y10123_w145_h172_2x.jpg
    pattern00 = re.compile(r'.*?_markedAs_.*?_(\d+\-\d+\-\d+[\-_]\d+_\d+_\d+)_x(\d+)_y(\d+)_w(\d+)_h(\d+)_?(\dx)?.jpg')

    # 1-p0.0000_2017-11-24-13_16_54_x6626_y35845_w150_h79_4x.jpg
    # 1-p0.0001_2017-10-09-17_12_28_x19230_y29594_w370_h910_.jpg
    # m1_2018-04-04-17_50_08_x11194_y33583_w163_h112.jpg
    # m1_2018-06-20_18_37_06_x10880_y42947_w113_h122.jpg
    pattern01 = re.compile(r'.*?_(\d+\-\d+\-\d+[\-_]\d+_\d+_\d+)_x(\d+)_y(\d+)_w(\d+)_h(\d+)_?(\dx)?.jpg')

    # 1-p0.0000_TC17033982_x21065_y14444_w56_h49_.jpg
    # 1-p0.0987_TC17013562_x28691_y23628_w64_h61_.jpg
    # 1-p0.0033_TC18018765_x28205_y36889_w41_h52_2x.jpg
    pattern02 = re.compile(r'.*?_([A-Z]+\d+)_x(\d+)_y(\d+)_w(\d+)_h(\d+)_?(\dx)?.jpg')

    if '_markedAs' in name:
        point = re.findall(pattern00, name)
    else:
        point = re.findall(pattern01, name)

    if not point:
        point = re.findall(pattern02, name)

    if point:
        return point[0]
    else:
        return None


def generate_datetime_label():
    """
    生成日期时间对应时间戳字符串
    :return:
    """
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def generate_work_list(excel_path):
    """
    基于 excel 文件生成文件名对应病理分类 txt
    :param excel_path: excel 文件路径
    :return:
    """

    # 得到Excel文件的book对象，实例化对象
    book = xlrd.open_workbook(excel_path)

    # 通过sheet索引获得sheet对象
    sheet = book.sheet_by_index(0)

    # # 获得指定索引的sheet表名字
    # sheet_name = book.sheet_names()[0]
    #
    # # 通过sheet名字来获取，当然如果知道sheet名字就可以直接指定
    # sheet1 = book.sheet_by_name(sheet_name)

    # 获取行总数
    nrows = sheet.nrows

    dict_ = {}
    for i in range(0, nrows):
        tiff_name, pt_type = sheet.row_values(i)
        basename, _ = os.path.splitext(os.path.basename(tiff_name))
        dict_[basename] = pt_type

    return dict_


# 数据服务器 图像存放地址
REMOTE_TIFF_PATH = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/0TIFF"
LOCAL_RESOURCE_POOL = "/home/cnn/Development/DATA/TRAIN_DATA/TIFFS"


def download_tiff_to_local(work_list, local_save_path, local_resource_pool=LOCAL_RESOURCE_POOL,
                           remote_tiff_path=REMOTE_TIFF_PATH):
    """
    下载任务文件至被你
    :param work_list: 待处理图像名称列表
    :param local_save_path: 本地图像存放路径
    :param local_resource_pool: 本地图像文件资源池
    :param remote_tiff_path: 远程图像文件资源池
    :return:
    """

    if not os.path.exists(local_save_path):
        os.makedirs(local_save_path)

    tiff_dict = generate_name_path_dict(local_save_path, ['.kfb', '.tif'])
    local_tiff_dict = generate_name_path_dict(local_resource_pool, ['.kfb', '.tif'])
    remote_tiff_dict = generate_name_path_dict(remote_tiff_path, ['.kfb', '.tif'])

    total = len(work_list)
    for index, item in enumerate(work_list):
        print("%s / %s" % (index + 1, total))
        if item not in tiff_dict:
            if item in local_tiff_dict:
                remote_file_path = local_tiff_dict[item]
            else:
                if item in remote_tiff_dict:
                    remote_file_path = remote_tiff_dict[item]
                else:
                    print("%s IS NOT FOUND ANYWHERE!" % item)
                    continue

            print("COPY FILE ...\nFROM %s\nTO %s" % (remote_file_path, local_save_path))
            shutil.copy(remote_file_path, local_save_path)
        else:
            print("%s IS ALREADY EXIST!" % item)


def worker(tiff_path, keys, points_dict, save_path, N):
    basename = os.path.splitext(os.path.basename(tiff_path))[0].replace(" ", "-")

    try:
        slide = openslide.OpenSlide(tiff_path)
    except:
        slide = TSlide(tiff_path)

    cell_count = 0
    for x_y in keys:
        boxes = points_dict[x_y]
        for box in boxes:
            x0, y0 = x_y.split('_')
            x = int(x0) + int(box[4][0])
            y = int(y0) + int(box[4][1])
            w = int(box[4][2])
            h = int(box[4][3])

            # make save dir
            cell_save_dir = os.path.join(save_path, box[2])
            os.makedirs(cell_save_dir, exist_ok=True)

            image_name = "1-p{:.10f}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(1 - box[3], basename, x, y, w, h, N)
            cell_save_path = os.path.join(cell_save_dir, image_name)

            slide.read_region((int(x + (1 - N) * w / 2), int(y + (1 - N) * h / 2)), 0,
                              (int(N * w), int(N * h))).convert("RGB").save(cell_save_path)

            cell_count += 1

    slide.close()

    return cell_count


jwt_cache = {}
HOST = '192.168.2.148'


def get_jwt(open_id):
    if open_id not in jwt_cache:
        login_url = 'http://%s/api/v1/auth_token/' % HOST
        response = requests.post(login_url, json={'username': 'convert', 'password': 'tsimage666'})
        if response.status_code != 200:
            raise Exception('can not logins', response.json())
        jwt_cache[open_id] = 'JWT {}'.format(response.json()['token'])
    return jwt_cache[open_id]


def gen_tiff_label_to_db(path):
    header = {"Authorization": "JWT %s" % get_jwt('convert')}

    with open(path) as f:
        tiff_name = os.path.splitext(os.path.basename(path))[0]
        tiff_name = tiff_name.replace("_clas", '')

        print("Processing on %s..." % tiff_name)

        image = None
        for item in ['.kfb', '.tif']:
            response = requests.get('http://%s/api/v1/images/?name=%s' % (HOST, tiff_name + item), headers=header)
            if response.status_code == 200 and response.json():
                data = response.json()
                if data:
                    image = data[0]['id']
                    break
        else:
            raise Exception("NO TIFF NAMED %s" % tiff_name)

        reader = csv.reader(f, delimiter=',')
        next(reader)

        for line in reader:
            x_y, label_yolo, accuracy_yolo, label_xception, accuracy_xception, xmin, ymin, xmax, ymax = line
            x0, y0 = x_y.split('_')
            x0, y0, accuracy, xmin, ymin, xmax, ymax = int(x0), int(y0), float(accuracy_xception), float(xmin), float(ymin), float(xmax), float(ymax)
            x, y, w, h = x0 + xmin, y0 + ymin, xmax - xmin, ymax - ymin

            label = {
                'image': image,
                'cell_type': label_xception,
                'accuracy': accuracy,
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'source_type': "AI",
            }

            response = requests.post('http://%s/api/v1/labels/' % HOST, json=label, headers=header)
            if response.status_code == 201:
                pass
            else:
                raise Exception(response.json())


def gen_tiff_diagnose_to_db(tiff_name, result):
    header = {"Authorization": "JWT %s" % get_jwt('convert')}

    image = None
    response = requests.get('http://%s/api/v1/images/?name=%s' % (HOST, tiff_name), headers=header)
    if response.status_code == 200 and response.json():
        data = response.json()
        if data:
            image = data[0]['id']
        else:
            raise Exception("NO TIFF NAMED %s" % tiff_name)

    result = {
        "result_auto": result,
    }
    response = requests.patch('http://%s/api/v1/images/%s/' % (HOST, image), json=result, headers=header)
    if response.status_code == 200:
        pass
    else:
        raise Exception(response.json())


if __name__ == '__main__':
    # clas_files_path = '/home/tsimage/Development/DATA/meta'
    # cell_images_path = '/home/tsimage/Development/DATA/cells'
    #
    # get_processed_lst(clas_files_path, cell_images_path)

    print(generate_datetime_label())
