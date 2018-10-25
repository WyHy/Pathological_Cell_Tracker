from easydict import EasyDict as edict
from multiprocessing import cpu_count
import os

curr_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

__C = edict()
# Consumers can get config by:
#   from config import cfg
cfg = __C

#
# lbp algo param
#
__C.lbp = edict()
__C.lbp.angle = 0


# #
# # darknet param for 5 classes
# #
# __C.darknet = edict()
# __C.darknet.classes = ["ASCUS", "LSIL", "ASCH", "HSIL", "SCC"]
# __C.darknet.dartnetlib = os.path.join(curr_path, "models/darknet/libdarknet.so")
# __C.darknet.cfg_file = os.path.join(curr_path, "models/darknet/yolov3-minitest-infer.cfg")
# __C.darknet.weights_file = os.path.join(curr_path, "dataset_files/yolov3-sota.weights")
# __C.darknet.datacfg_file = os.path.join(curr_path, "models/darknet/minitest.data")
# __C.darknet.namecfg_file = os.path.join(curr_path, "models/darknet/minitest.names")

#
# darknet param for 12 classes
#
__C.darknet = edict()
__C.darknet.classes = ["ASCUS", "LSIL", "ASCH", "HSIL", "SCC", "AGC", "EC", "FUNGI", "TRI", "CC", "ACTINO", "VIRUS"]
__C.darknet.dartnetlib = os.path.join(curr_path, "models/darknet/libdarknet.so")
__C.darknet.cfg_file = os.path.join(curr_path, "models/darknet/yolov3-minitest-12-infer.cfg")
__C.darknet.weights_file = os.path.join(curr_path, "dataset_files/yolov3-minitest-12_final.weights")
__C.darknet.datacfg_file = os.path.join(curr_path, "models/darknet/minitest-12-1009.data")
__C.darknet.namecfg_file = os.path.join(curr_path, "models/darknet/minitest-12.names")
__C.darknet.thresh = 0.1
__C.darknet.hier_thresh = 0.5
__C.darknet.nms = 0.45
# 启动多进程任务的最低图像数
__C.darknet.min_job_length = 16
# 依据坐标位置判断两个图像是否重复时的最低重叠比
__C.darknet.min_overlap_ratio = 0.6


#
# xception param for 16 classes
#
__C.xception = edict()
__C.xception.det1 = -0.05  # used in gen_np_array
__C.xception.size = 299
__C.xception.weights_file = os.path.join(curr_path, "dataset_files/Xception_finetune_40.h5")
# __C.xception.weights_file = os.path.join(curr_path, "dataset_files/Xception_finetune.h5")

__C.xception.classes = ["ACTINO", "AGC", "ASCH", "ASCUS", "CC", "EC", "FUNGI", 
                        "GEC", "HSIL", "LSIL", "MC", "RC", "SC", "SCC", "TRI", "VIRUS"]
__C.xception.class_num = 16

# __C.xception.classes = ["ACTINO", "ADC", "AGC1", "AGC2", "ASCH", "ASCUS", "CC", "EC", "FUNGI", 
#                         "GEC", "HSIL", "LSIL", "MC", "RC", "SC", "SCC", "TRI", "VIRUS"]
# __C.xception.class_num = 18
__C.xception.det2 = 0.1   # used in gen output csv file
__C.xception.min_job_length = 16
__C.xception.min_overlap_ratio = 0.6


# decision tree
__C.decision_tree = edict()
__C.decision_tree.classes_files = os.path.join(curr_path, "dataset_files/Classes.txt")
__C.decision_tree.model = os.path.join(curr_path, "dataset_files/dst.model")


# xgboost param
__C.xgboost = edict()
__C.xgboost.pkl_file = os.path.join(curr_path, "dataset_files/XGBClassifier.pkl")
__C.xgboost.classes = ["NORMAL", "ASCUS", "LSIL", "ASCH", "HSIL", "SCC"]
# xception 输出有效统计项
__C.xgboost.NORMAL = ["MC", "RC", "SC", "GEC"]

# process param
__C.process = edict()
__C.process.angle = 0

#
# data param
#
__C.data = edict()
__C.data.angle = 0


#
# slice param
#
__C.slice = edict()
# 切图-宽
__C.slice.WIDTH = 608
# 切图-高
__C.slice.HEIGHT = 608
# 切图步长
__C.slice.DELTA = 608
# 切图比例-开始
__C.slice.AVAILABLE_PATCH_START_RATIO = 0.1
# 切图比例-结束
__C.slice.AVAILABLE_PATCH_END_RATIO = 0.9
# 过滤低价值图像阈值
__C.slice.THRESH = 10.0
# 切图进程数量
__C.slice.SLICE_PROCESS_NUM = cpu_count() - 4

# 仅截取大图中间指定大小区域
__C.center = edict()
# 切图数量
__C.center.PATCH_NUM = 128
# 切图尺寸-宽
__C.center.PATCH_WIDTH = 224
# 切图尺寸-高
__C.center.PATCH_HEIGHT = 224
# 切图步长
__C.center.DELTA = 224

# 生产环境细胞分割默认参数
__C.algo = edict()
__C.algo.patch_lens = 30
__C.algo.thresh = .1
__C.algo.hier_thresh = .1
__C.algo.nms = .1
__C.algo.DEFAULT_WIDTH = 299
__C.algo.DEFAULT_HEIGHT = 299

# 返回值编码
__C.code = edict()
# success
__C.code.success = 0
# fail
__C.code.fail = -1

# lbp后端相关

__C.lbp = edict()
__C.lbp.progress_url = "http://proxy/algorithm/tasks/"

