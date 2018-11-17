import os
import queue
import sys
import time
from multiprocessing.managers import BaseManager
import sys

sys.path.append("../..")

sys.path.append("../..")
from utils import generate_name_path_dict
from lbp_algo_tiff_worker_for_demo import slides_diagnose_worker

SLIDE_STORAGE_PATH = "/home/stimage/Development/DATA/PRODUCTION_FULL_TEST/TIFFS/"


# 创建类似的QueueManager:
class QueueManager(BaseManager):
    pass


if __name__ == '__main__':
    # 注册任务队列:、
    QueueManager.register('get_task_queue')
    QueueManager.register('get_result_queue')

    # 连接到服务器，也就是运行task_master.py的机器:
    master_address = '192.168.2.148'
    print('Connect to server %s...' % master_address)

    # 端口和验证码注意保持与task_master.py设置的完全一致:
    m = QueueManager(address=(master_address, 5000), authkey=b'abc')

    # 连接:
    m.connect()

    # 获取Queue的队列
    task = m.get_task_queue()
    result = m.get_result_queue()

    dict_ = generate_name_path_dict(SLIDE_STORAGE_PATH)
    resource_save_path = '/home/cnn/Development/DATA/PRODUCTION_FULL_TEST/'

    # 从task队列取任务,并把结果写入result队列:
    while 1:
        try:
            obj = task.get(timeout=1)
            basename, _ = os.path.splitext(os.path.basename(obj['name']))
            print('Run Task Image Id = %s...\nPath=%s' % (obj['id'], dict_[basename]))
            slides_diagnose_worker([dict_[basename]], resource_save_path)

            result.put({'id': obj['id'], 'status': 1})
        except queue.Empty:
            time.sleep(5)
            print('task queue is empty.')
