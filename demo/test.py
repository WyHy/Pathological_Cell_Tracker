import datetime
import math
from concurrent.futures import ProcessPoolExecutor

import cv2
import os

from multiprocessing import Pool, Manager
from time import sleep

import openslide
import numpy as np


def get_patch_num(w, h, step=224):
    """
    计算patch数量
    :param w:
    :param h:
    :param step:
    :return:
    """
    return math.ceil(w / step) * math.ceil(h / step)


def patch_worker(queue, input_image_path, start_x, start_y, height, in_queue):
    '''
    按指定 patch size 和 步长 对 tif 图像进行切分
    :param queue: 进程间共享图像数据队列
    :param input_image_path: tif文件路径
    :param start_x: 切割起点坐标-x
    :param start_y: 切割起点坐标-y
    :param height: 切割区域
    :return: 无返回值
    '''

    # 读取tif文件
    img_data = openslide.OpenSlide(input_image_path)

    # items = []
    while start_y < height:
        # 读取patch块
        patch = img_data.read_region((start_x, start_y), 0, (224, 224))
        # 图像格式转换
        patch = cv2.cvtColor(np.asarray(patch), cv2.COLOR_RGBA2BGR)
        queue.put((start_x, start_y, patch))
        in_queue.put(1)
        start_y += 224

    # 关闭句柄
    img_data.close()


if __name__ == '__main__':
    # print(get_available_gpus())
    # import pycuda.driver as cuda
    #
    # cuda.init()
    #
    # # GPU数量
    # gpu_count = cuda.Device.count()
    # print(gpu_count)

    # a = "`12.345a-cx=你骄傲"
    # print(''.join(filter(str.isalpha, a)))
    #
    # import re
    #
    # b = re.sub("[^A-Za-z0-9]", "", a).upper()
    # print(b, type(b))
    #
    # c = ''
    # if c:
    #     print(True)
    # else:
    #     print(False)
    #
    # print(not '')

    from datetime import datetime

    a = "2018-08-26 09:49:50"
    b = datetime.strptime(a, "%Y-%m-%d %H:%M:%S")

    print((datetime.now() - b).days)
    # tif = '/home/sakulaki/yolo-yuli/one_stop_test/tif/XB1800118.tif'
    # slide = openslide.OpenSlide(tif)
    #
    # if slide:
    #     t1 = datetime.datetime.now()
    #     img_name = os.path.basename(tif).split(".")[0]
    #     print("Process %s ..." % img_name)
    #
    #     # 采用多线程，线程数默认为CPU核心数
    #     # pool = Pool(3)
    #
    #     pool = ProcessPoolExecutor(3)
    #
    #
    #     # 跨进程图像队列
    #     queue = Manager().Queue()
    #     # 切图队列
    #     in_queue = Manager().Queue()
    #     # 任务进度队列
    #     progress_queue = Manager().Queue()
    #
    #     width, height = slide.dimensions
    #
    #     # 按列读取，仅读取图像中间(指定比例)位置
    #     x, y, width, height = int(width * 0), int(height * 0), int(width * 1), int(height * 1)
    #
    #     patch_num = get_patch_num(width - x, height - y)

    # # 切图处理
    # while x < width:
    #     pool.apply_async(patch_worker, (queue, tif, x, y, height, in_queue))
    #     x += 224
    #
    # while progress_queue.qsize() + 10 < patch_num:
    #     sleep(2)
    #     print("%.2f" % (progress_queue.qsize() / patch_num))
    #
    # pool.close()
    # pool.join()

    # 切图处理
    # results = []
    # while x < width:
    #     results.append(pool.submit(patch_worker, queue, tif, x, y, height, in_queue))
    #     x += 224
    #
    # pool.shutdown(wait=True)

    # a = [54, 623, 684, 1, 31, 3105]

    # a = {'a': 1, 'b': 2}
    # with open('./test.txt', 'w') as f:
    #     f.write(str(a))

    # import numpy as np
    #
    # a = 1.00000
    # b = np.float32(a)
    # c = b.item()
    # print(b, type(b))
    # print(c, type(c))

    # import random
    #
    # a = [1, 2, 3, 4, 5]
    # random.shuffle(a)
    #
    # print(a)

    a = '/home/sakulaki/code/udapro/dogcat/data/resized/dog/dog.7853.jpg 0'
    print('dog' in a)
