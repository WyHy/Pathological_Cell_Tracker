import os
import sys
from config.config import *
from common.utils import FilesScanner, ImageSlice
from models.darknet.darknet_predict import DarknetPredict
from models.xception.xception_preprocess import XceptionPreprocess
from models.xception.xception_predict import XceptionPredict
from models.xception.xception_postprocess import XceptionPostprocess
from models.xgboost.xgboost_preprocess import XgboostPreprocess
from models.xgboost.xgboost_predict import XgboostPredict
import datetime

import openslide
import shutil


class LBP:
    def __init__(self, tif_name, file_path, cell_path):
        self.tif_name = tif_name
        self.file_path = file_path
        self.cell_path = cell_path

    def run(self):
        basename = os.path.splitext(os.path.basename(self.tif_name))[0]
        # slice slide
        slice_res = ImageSlice(self.tif_name, self.file_path).get_slices()
        tif_images = FilesScanner(slice_res['done'][0], postfix=".jpg").get_files()
        # print(tif_images)

        # run darknet
        seg_results = DarknetPredict().predict(tif_images)

        # save segment result into csv
        xcep_pre = XceptionPreprocess(self.tif_name)
        seg_csv = os.path.join(self.file_path, basename + "_seg.csv")
        xcep_pre.write_csv(seg_results, seg_csv)

        # generate numpy array, it is the input of second stage classification algorithm
        cell_numpy, cell_index = xcep_pre.gen_np_array_csv(seg_csv=seg_csv)

        # run classification
        predictions = XceptionPredict().predict(cell_numpy)
        print(len(cell_index), len(predictions))

        # summarize two stages' result and generate a final csv
        clas = XceptionPostprocess()
        clas_dict = clas.convert_all(predictions=predictions, cell_index=cell_index)
        clas_csv = os.path.join(self.file_path, basename + "_clas.csv")
        clas.write_csv(clas_dict, clas_csv)

        # # generate cell jpgs, based on clas_dict
        # clas.cut_cells(self.tif_name, clas_dict, self.cell_path)
        # # add classification det probability to jpg name
        # clas.cut_cells_p(self.tif_name, clas_dict, self.cell_path)
        # add classification det probability to jpg name and add marked class_i if jpg is already is marked
        clas.cut_cells_p_marked(self.tif_name, clas_dict, self.cell_path, factor=0.2, N=2)

        # # run xgboost
        # clas_csv_in = clas_csv
        # clas_csv_out = os.path.join(self.file_path, basename + "_xgbo.csv")
        # XgboostPreprocess().convert(clas_csv_in, clas_csv_out)
        # print(XgboostPredict().predict(clas_csv_out))


LOCAL_TEMP_FILE_PATH = '/tmp/metadata/lbp-algo'
def copy_remote_file_to_local(remote_file_path):
    basename = os.path.basename(remote_file_path)
    local_file_path = os.path.join(LOCAL_TEMP_FILE_PATH, basename)

    print("COPY FILE ...\nFROM %s\nTO %s" % (remote_file_path, local_file_path))
    t0 = datetime.datetime.now()
    shutil.copy(remote_file_path, local_file_path)
    t1 = datetime.datetime.now()
    print("DONE. cost %s" % (t1 - t0))

    return local_file_path


def get_unrunned(src_tifs, des_tifs):
    src = FilesScanner(tif_path, postfix=".tif").get_files() \
        + FilesScanner(tif_path, postfix=".kfb").get_files()
    src_dict = {fullname:os.path.splitext(os.path.basename(fullname))[0] for fullname in src}
    des = os.listdir(des_tifs)

    des_names = ['_'.join(item.split('.')[0].split('_')[:-1]) for item in des]

    done_num = 0
    for fullname, basename in src_dict.items():
        if basename in des_names:
            done_num += 1


    print("CURRENT PROGRESS %s / %s." % (done_num, len(src_dict)))

    for fullname, basename in src_dict.items():
        if not des:
            return fullname

        if basename in des_names:
            pass
        else:
            return fullname

        # for i, derivativename in enumerate(des):
        #     if basename in derivativename:
        #         break
        #     if i == len(des)-1:
        #         return fullname

    sys.exit(1)


if __name__ == "__main__":
    # multiple runs
    tif_path = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/checked_cells/manual_labelled_checked/label_kfb_tif/label_data"
    file_path = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/auto_cellCutting/window_cellCutting/labelled_for_cellCutting_tmp"
    cell_path = "/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/auto_cellCutting/window_cellCutting/labelled_for_cellCutting_cells"
    tif_name = get_unrunned(tif_path, file_path)

    # tif_name = copy_remote_file_to_local(tif_name)
   
    if tif_name:
        print("Processing %s..." % tif_name)
        LBP(os.path.join(tif_path, tif_name), file_path, cell_path).run()
        # try:
        #     LBP(os.path.join(tif_path, tif_name), file_path, cell_path).run()
        # except openslide.lowlevel.OpenSlideUnsupportedFormatError:
        #     print('======>   Can not open image file')

        # os.remove(tif_name)

    else:
        print('ALL JOB DONE !')


    # # single run
    # tif_name = "/home/sakulaki/yolo-yuli/one_stop_test/tif/XB1800118.tif"
    # file_path = "./data_result"
    # cell_path = "./data_result/cells"
    # LBP(tif_name, file_path, cell_path).run()
