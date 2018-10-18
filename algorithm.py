import datetime
import json
import math
import shutil
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import sleep

import numpy as np
import pandas as pd

# 共享变量
from multiprocessing import Manager

import openslide
import os

from sklearn.externals import joblib

from config.config import cfg
from common.tslide import TSlide
from common.utils import worker, calculate_patch_num, generate_cell_image, FilesScanner, update_algorithm_progress
from models.darknet.darknet_predict import DarknetPredict

# CPU数量
from models.xception.xception_predict import XceptionPredict
from models.xgboost.xgboost_preprocess import header as HEADER

CLASSES = cfg.xgboost.classes

cpu_count = cfg.slice.SLICE_PROCESS_NUM

# GPU数量
# gpu_count = len(os.popen("lspci |grep VGA").read().split('\n')) - 1

gpu_count = 1

TEMP_FILES_PATH = '/tmp/metadata/lbp/algorithm/output/'


def get_xgboost_results(dataset, DELTA):
    """
    输出有效的标签index
    :return:
    """

    ws = []
    hs = []

    rets = []
    for item in dataset:
        segment = item.pop('segment')
        det = segment['accuracy']
        if det < DELTA:
            continue

        segment = segment['label']

        classify = item.pop('classify')
        det_ = classify['accuracy']
        classify = classify['label']
        if classify in cfg.xgboost.NORMAL:
            continue

        if classify not in cfg.xgboost.classes:
            continue

        item.update({
            'det': det,
            'segment': segment,
            'det.1': det_,
            'classify': classify,
        })

        rets.append(item)
        ws.append([item['xmax'], item['xmin']])
        hs.append([item['ymax'], item['ymin']])

    item_dict = {key: 0 for key in HEADER}

    for index, row in enumerate(rets):
        item_dict[row['segment'] + "_s"] += 1
        item_dict[row['classify'] + "_c"] += 1
        if float(row['det']) > 0.05:
            item_dict[row['segment'] + "_s_005"] += 1
        if float(row['det']) > 0.99:
            item_dict[row['segment'] + "_s_099"] += 1
        percentile = [x * 0.1 for x in range(1, 10)]
        for index, p in enumerate(percentile):
            if float(row['det']) > p:
                item_dict[row['segment'] + '_s_0{}'.format(index + 1)] += 1
            if float(row['det.1']) > p:
                item_dict[row['classify'] + '_c_0{}'.format(index + 1)] += 1
        if float(row['det.1']) > 0.99:
            item_dict[row['classify'] + "_c_099"] += 1
        if float(row['det.1']) > 0.999:
            item_dict[row['classify'] + "_c_0999"] += 1

    ws = pd.DataFrame(ws, columns=['xmax', 'xmin'])
    hs = pd.DataFrame(hs, columns=['ymax', 'ymin'])
    w = ws['xmax'] - ws['xmin']
    h = hs['ymax'] - hs['ymin']

    item_dict['w_mean'] = w.mean()
    item_dict['h_mean'] = h.mean()
    item_dict['v_mean'] = (w * h).mean()
    percentile = [x * 0.1 for x in range(1, 10)]
    for index, p in enumerate(percentile):
        item_dict['w_0{}'.format(index + 1)] = w.quantile(p)
        item_dict['h_0{}'.format(index + 1)] = h.quantile(p)
        item_dict['d_0{}'.format(index + 1)] = (w * w + h * h).pow(0.5).quantile(p)
        item_dict['v_0{}'.format(index + 1)] = (w * h).quantile(p)

    datasets = []
    for col in HEADER[1:]:
        datasets.append(item_dict[col])

    datasets = pd.DataFrame([datasets, ], columns=HEADER[1:])

    with open(cfg.xgboost.pkl_file, 'rb') as f:
        model = joblib.load(f)

    return model.predict(datasets)


def segment(index, queue):
    """
    细胞分割
    :param index: gpu编号
    :param queue: 待识别含细胞图像
    :return:
    """
    seg = DarknetPredict(thresh=cfg.algo.thresh, hier_thresh=cfg.algo.hier_thresh, nms=cfg.algo.nms, gpu=str(index))
    print('No.%s Cell Engine Staring...' % index)

    return seg.predict(queue)


def do_cell_classification(index, cells):
    """
    细胞识别
    :param index: gpu编号
    :param cells: 细胞lst，numpy array
    :return:
    """
    cells_content = [cell.pop('patch') for cell in cells]
    cls = XceptionPredict(gpu=str(index)).predict(np.asarray(cells_content))
    for i, value in enumerate(cls):
        # 获取最大概率值index
        index = np.argmax(value)
        # 获取最大概率值
        accuracy = value[index]
        # 获取标签
        label = cfg.xception.classes[index]

        cells[i]['classify'] = {
            'label': label,
            'accuracy': accuracy,
        }

    return cells


def update_progress(payload, progress, delta=0):
    """
    更新算法进度
    :param payload: payload
    :param progress:
    :param delta:
    :return:
    """
    progress += delta
    progress = 100 if progress > 100 else progress

    print("=========================================> %.2f" % progress)

    # payload.set_algorithm_progress(progress)

    return progress


def main(file_path, payload, cell_output_path, output_file_path=TEMP_FILES_PATH):
    """
    更新算法进度
    :param file_path:
    :param payload: 用于更新当前算法进度
    :param cell_output_path: cell output path
    :param output_file_path:
    :return:
    """

    # 清理历史文件
    if os.path.exists(output_file_path):
        shutil.rmtree(output_file_path)

    # 获取病理图像文件名，假如文件名中有空格的话，以 "_" 替换
    img_name = os.path.basename(file_path).split(".")[0].replace(" ", "_")
    print("Image Process %s ..." % file_path)

    try:
        t0 = datetime.datetime.now()

        # 算法当前进度
        progress = 0.0
        progress = update_progress(payload, progress)

        try:
            slide = openslide.OpenSlide(file_path)
        except:
            slide = TSlide(file_path)

        if slide:
            progress = update_progress(payload, progress, 1.0)
            _width, _height = slide.dimensions

            # 按行读取，仅读取图像中间(指定比例)位置
            x, y, width, height = int(_width * cfg.slice.AVAILABLE_PATCH_START_RATIO), \
                                  int(_height * cfg.slice.AVAILABLE_PATCH_START_RATIO), \
                                  int(_width * cfg.slice.AVAILABLE_PATCH_END_RATIO), \
                                  int(_height * cfg.slice.AVAILABLE_PATCH_END_RATIO)

            # 获取预测切片数量
            prediction_patch_num = calculate_patch_num(width, height, cfg.slice.DELTA)

            # 构造临时文件存储目录
            output_path = os.path.join(output_file_path, img_name)
            os.makedirs(output_path, exist_ok=True)

            ############################################################################################################
            ########################################## 1. 切分大图 #####################################################

            t1 = datetime.datetime.now()

            print("Starting Image slicing...")
            print("Adding Job to Pool...")

            tasks = []

            # 创建切图进程池
            executor = ProcessPoolExecutor(max_workers=2)
            while x < width:
                tasks.append(
                    executor.submit(worker, file_path, x, y, height, cfg.slice.WIDTH, cfg.slice.HEIGHT, cfg.slice.DELTA,
                                    output_path))
                x += cfg.slice.DELTA

            t2 = datetime.datetime.now()
            job_count = len(tasks)
            print("Done, cost: %s, Total Job Count: %s, Worker Count: %s" % (
                (t2 - t1), job_count, cfg.slice.SLICE_PROCESS_NUM))

            progress = update_progress(payload, progress, 10)

            # 获取切片地址列表
            patches = []

            # 每个进程结束时进度更新
            delta = 12 / len(tasks)
            for future in as_completed(tasks):
                queue = future.result()
                # 添加进任务队列
                patches.extend(queue)
                job_count -= 1
                print("One Job Done, Got %s patches, last Job Count: %s" % (len(queue), job_count))
                progress = update_progress(payload, progress, delta)

            # 关闭进程池
            executor.shutdown(wait=True)

            # # root = '/tmp/pycharm_project_584/data_result/XB1800118'
            # # patches = FilesScanner(root).get_files()
            # # patches = [os.path.join(root, patch) for patch in patches]

            # t3 = datetime.datetime.now()
            # total_patch_count = len(patches)
            # print("Image slicing done, get %s patches, prediction patch num is %s, cost %s" % (
            #     total_patch_count, prediction_patch_num, (t3 - t2)))

            # # patch分组
            # n = int(math.ceil(len(patches) / float(gpu_count)))
            # patches = [patches[i: i + n] for i in range(0, len(patches), n)]

            # ############################################################################################################
            # ########################################## 2. 基于小图识别细胞位置-Darknet #################################

            # print("Start Cell Recognizing...")

            # tasks = []
            # # 创建细胞切割进程池
            # executor = ProcessPoolExecutor()
            # for i, queue in enumerate(patches):
            #     tasks.append(executor.submit(segment, i % gpu_count, queue))

            # cells = {}
            # # 获取细胞分割结果
            # # 每个进程结束时进度更新
            # delta = 46 / len(tasks)
            # for future in as_completed(tasks):
            #     rets = future.result()
            #     cells.update(rets)
            #     progress = update_progress(payload, progress, delta)

            # executor.shutdown(wait=True)
            # t4 = datetime.datetime.now()
            # print("Done, Total available patches num is %s., cost %s" % (len(cells), (t4 - t3)))

            # ############################################################################################################
            # ########################################## 3. 基于细胞位置获取细胞图像 #####################################

            # print("Start Cell Imaging...")

            # tags = list(cells)
            # # patch分组
            # n = int(math.ceil(len(patches) / float(cpu_count)))
            # tags = [tags[i: i + n] for i in range(0, len(tags), n)]

            # tasks = []
            # # 创建细胞切割进程池
            # executor = ProcessPoolExecutor(max_workers=cpu_count)
            # for i, tag in enumerate(tags):
            #     tasks.append(executor.submit(generate_cell_image, output_path, tag, cells))

            # cells = []
            # # 获取细胞分割结果

            # # 每个进程结束时进度更新
            # delta = 8 / len(tasks)
            # for future in as_completed(tasks):
            #     rets = future.result()
            #     cells.extend(rets)
            #     progress = update_progress(payload, progress, delta)

            # executor.shutdown(wait=True)
            # t5 = datetime.datetime.now()
            # print("Done Matting, Total cells num %s, cost %s" % (len(cells), (t5 - t4)))

            # ############################################################################################################
            # ########################################## 4. 识别细胞分类-Xception ########################################

            # print("Start Cell Classification...")
            # # patch分组
            # n = int(math.ceil(len(cells) / float(gpu_count)))
            # cells = [cells[i: i + n] for i in range(0, len(cells), n)]

            # tasks = []
            # # 创建细胞分类进程池
            # executor = ProcessPoolExecutor(max_workers=gpu_count)
            # for i, cell_group in enumerate(cells):
            #     tasks.append(executor.submit(do_cell_classification, i, cell_group))

            # ranks = []
            # # 获取细胞分类结果
            # # 每个进程结束时进度更新
            # delta = 21 / len(tasks)
            # for future in as_completed(tasks):
            #     rets = future.result()
            #     ranks.extend(rets)
            #     progress = update_progress(payload, progress, delta)

            # executor.shutdown(wait=True)
            # t5 = datetime.datetime.now()
            # print("Done Classification, Total collection cells num %s, cost %s" % (len(ranks), (t5 - t4)))


            # # output_dir_path
            # output_dir_path = os.path.join(cell_output_path, img_name)
            # os.makedirs(output_dir_path, exist_ok=True)

            # for rank in ranks:
            #     label = rank['classify']['label']
            #     x = rank['xmin'] + rank['x0']
            #     y = rank['ymin'] + rank['y0']
            #     w = rank['w']
            #     h = rank['h']
            #     accu = rank['classify']['accuracy']

            #     # double
            #     x = int(x - 0.5*w)
            #     y = int(y - 0.5*h)
            #     w = 2*w
            #     h = 2*h

            #     patch = slide.read_region((x, y), 0, (w, h))

            #     # 图像格式转换
            #     patch = cv2.cvtColor(np.asarray(patch), cv2.COLOR_RGBA2BGR)


            #     # 生成文件路径
            #     save_path = os.path.join(output_dir_path, label)
            #     os.makedirs(save_path, exist_ok=True)

            #     # 文件写入
            #     save_path = os.path.join(save_path, "%s_p%.6f_%s_x%s_y%s_w%s_h%s.jpg" % (label, accu, img_name, x, y, w, h))
            #     cv2.imwrite(save_path, patch)



            # # 返回坐标列表，按照label分组
            # point_lst = {}
            # for rank in ranks:
            #     x = rank['xmin'] + rank['x0']
            #     y = rank['ymin'] + rank['y0']
            #     w = rank['w']
            #     h = rank['h']
            #     label = rank['classify']['label']
            #     accu = rank['classify']['accuracy']

            #     obj = {
            #         'x': (x * 1.0) / _width,
            #         'y': (y * 1.0) / _width,
            #         'w': (w * 1.0) / _width,
            #         'h': (h * 1.0) / _width,
            #         'name': label,
            #         'c': accu
            #     }

            #     if label in point_lst:
            #         point_lst[label].append(obj)
            #     else:
            #         point_lst[label] = [obj, ]

            # # # 列表按照准确率进行排序
            # # for key, value in point_lst.items():
            # #     point_lst[key] = sorted(value, key=lambda x: x['c'], reverse=True)
            # #     print(point_lst[key][:10])

            # ############################################################################################################
            # ########################################## 5. Format 细胞分类结果 ##########################################

            # t6 = datetime.datetime.now()
            # print("Start Xgboost Data Preprocess...")
            # label = cfg.xgboost.classes[int(get_xgboost_results(ranks, cfg.xception.det2)[0])]
            # print('The final algorithm diagnose result is %s' % label)
            # print("Total cost %s" % (t6 - t0))
            # update_progress(payload, progress, 100)

            # for key, vals in point_lst.items():
            #     print(vals[:10])

            # return label, point_lst
        else:
            raise Exception("image %s open failed" % img_name)
    except:
        raise


def get_unrunned(src_tifs, des_tifs):
    src = FilesScanner(src_tifs, postfix=".tif").get_files() \
        + FilesScanner(src_tifs, postfix=".kfb").get_files()

    src_dict = {fullname:os.path.splitext(os.path.basename(fullname))[0] for fullname in src}
    des = os.listdir(des_tifs)
    for fullname,basename in src_dict.items():
        if not des:
            return fullname
        for i,derivativename in enumerate(des):
            if basename in derivativename:
                break
            if i == len(des)-1:
                return fullname

    sys.exit(1)


if __name__ == '__main__':
    # file_path = '/home/sakulaki/yolo-yuli/one_stop_test/tif/XB1800118.tif'

    # tif_path = "/media/tsimage/新加卷/label_kfb_tif/label_data"
    # file_path = "/media/tsimage/新加卷/label_kfb_tif/unlabelled_for_cellCutting_tmp"
    # cell_path = "/media/tsimage/新加卷/label_kfb_tif/unlabelled_for_cellCutting_cells"

    # tif_name = get_unrunned(tif_path, file_path)
   
    # if tif_name:
    #     main(file_path, None)
    # else:
    #     print('all job done!')

    file_path = '/home/tsimage/Development/2017-10-19-09_17_28.tif'
    cell_output_path = '/tmp/metadata/test/'

    main(file_path, None, cell_output_path)

    