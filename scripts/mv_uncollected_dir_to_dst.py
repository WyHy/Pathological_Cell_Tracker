# coding:utf-8

import os
import shutil

alreadt_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181022/CELLS/TIFFS_READY_TO_CHECK_01'
already_collected = os.listdir(alreadt_path)

all_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181022/CELLS/TIFFS'
all_ = os.listdir(all_path)

dst_path = '/home/cnn/Development/DATA/CELL_CLASSIFIED_JOB_20181022/CELLS/TIFFS_READY_TO_CHECK'
for item in all_:
	if item not in already_collected:
		print('COPY %s to %s' % (item, dst_path))
		shutil.copytree(os.path.join(all_path, item), os.path.join(dst_path, item))