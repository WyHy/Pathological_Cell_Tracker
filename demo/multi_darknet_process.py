import os
from multiprocessing import Pipe
from time import sleep
from concurrent.futures import ProcessPoolExecutor, as_completed

from models.darknet.darknet import detect, load_net, load_meta
from models.darknet.darknet_predict import DarknetPredict, cfg

# GPU数量
gpu_count = len(os.popen("lspci |grep VGA").read().split('\n')) - 1


def generate_darknet_configure_file():
    """
    生成 darknet 模型配置文件
    :return:
    """
    # for minitest.data
    cfg_data = {
        "classes": len(cfg.darknet.classes),
        "train": "train.txt",
        "valid": "valid.txt",
        "names": cfg.darknet.namecfg_file,
        "backup": "backup"
    }

    # write cfg_data into minitest.data
    with open(cfg.darknet.datacfg_file, "w") as f:
        for key, value in cfg_data.items():
            f.write("%s = %s\n" % (key, value))


def segment(index):
    DarknetPredict(gpu=str(index))


generate_darknet_configure_file()


if __name__ == '__main__':
    tasks = []
    # 创建细胞切割进程池
    executor = ProcessPoolExecutor(max_workers=2)

    for i in range(gpu_count):
        tasks.append(executor.submit(segment, i % gpu_count))

    # os.environ["CUDA_VISIBLE_DEVICES"] = '0'
    #
    # # init
    # thresh = .5
    # hier_thresh = .5
    # nms = .45
    #
    # net = load_net(cfg.darknet.cfg_file.encode('utf-8'), cfg.darknet.weights_file.encode('utf-8'), 0)
    # meta = load_meta(cfg.darknet.datacfg_file.encode('utf-8'))
    #
    # print(11111111111)

    executor.shutdown(wait=True)
