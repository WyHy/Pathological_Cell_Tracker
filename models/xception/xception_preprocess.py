import os
import csv
import numpy as np
import openslide
from common.tslide.tslide import TSlide
from config.config import cfg
import re

from utils import get_tiff_dict


class XceptionPreprocess:
    def __init__(self, input_file):
        """
            input_file: input .kfb/.tif full path name
        """
        self.input_file = input_file
        self.pattern = re.compile(r'(.*?)_(\d+)_(\d+)$')

    def write_csv(self, results, csv_fullname):
        """
        :param results: dict generated after running darknet predict: {x_y: [(class_i, det, (x,y,w,h)),]}
        :param csv_fullname: csv full path name
        :write format: in each row: x_y, class_i, det, x, y, w, h
        """
        with open(csv_fullname, "w") as f:
            writer = csv.writer(f)
            for x_y, boxes in results.items():
                for box in boxes:
                    writer.writerow([x_y, box[0], box[1], box[2][0], box[2][1], box[2][2], box[2][3]])

    def read_csv(self, csv_fullname):
        """
            csv_fullname: csv full path name
            return: a python dictionary: {x_y: [(class_i, det, (x,y,w,h)),]}
        """
        dict_ = {}
        with open(csv_fullname, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                box = (row[1], float(row[2]),
                       (float(row[3]), float(row[4]), float(row[5]), float(row[6])))
                if not row[0] in dict_:
                    dict_[row[0]] = [box]
                else:
                    dict_[row[0]].append(box)
        return dict_

    def gen_np_array_mem(self, results, classes=cfg.darknet.classes, det=cfg.xception.det1, size=cfg.xception.size):
        """
        :param classes: [class_i,]
        :param det: the threshold of det to use certain box or not, from darknet prediction
        :param size: image size to cut, default to 299, which is used in Xception/inception
        :param results: dict generated after running darknet predict: {x_y: [(class_i, det, (x,y,w,h)),]}
        :return:
            numpy array: numpy array of each cell, in order
            cell_index: {index: [x_y, [class_i, det, (x,y,w,h)]]},
                        index is index in numpy array,
                           x_y is jpg image name, it represents cell source,
                        box = [class_i, det, (x,y,w,h)] is cell info from darknet
        """

        def resize_img(img, size):

            # pad zero with short side
            img_croped = img.crop(
                (
                    -((size - img.size[0]) / 2),
                    -((size - img.size[1]) / 2),
                    img.size[0] + (size - img.size[0]) / 2,
                    img.size[1] + (size - img.size[1]) / 2
                )
            )
            # now, yolo output is square, only need resize

            img_resized = img_croped.resize((size, size))
            return img_resized

        try:
            slide = openslide.OpenSlide(self.input_file)
        except:
            slide = TSlide(self.input_file)

        cell_list = []
        cell_index = {}
        index = 0
        for x_y, boxes in results.items():
            for box in boxes:
                if box[0] in classes and box[1] > det:
                    x = int(x_y.split('_')[0]) + int(box[2][0])
                    y = int(x_y.split('_')[1]) + int(box[2][1])
                    w = int(box[2][2])
                    h = int(box[2][3])
                    cell = slide.read_region((x, y), 0, (w, h)).convert("RGB")
                    cell_list.append(np.array(resize_img(cell, size)))
                    cell_index[index] = [x_y, list(box)]
                    index += 1
        slide.close()
        # return np.asarray(cell_list), cell_index
        return cell_list, cell_index

    def gen_np_array_csv(self, seg_csv, classes=cfg.darknet.classes, det=cfg.xception.det1, size=cfg.xception.size):
        """
        :param classes: [class_i,]
        :param det: the threshold of det to use certain box or not, from darknet prediction
        :param size: image size to cut, default to 299, which is used in Xception/inception
        :param seg_csv: dict read from csv file, that stores images and results data of darknet
        :return:
            numpy array: numpy array of each cell, in order
            cell_index: {index: [x_y, [class_i, det, (x,y,w,h)]]},
                        index is index in numpy array,
                           x_y is jpg image name, it represents cell source,
                        box = [class_i, det, (x,y,w,h)] is cell info from darknet
        """

        seg_dict = self.read_csv(seg_csv)
        return self.gen_np_array_mem(results=seg_dict, classes=classes, det=det, size=size)

    def gen_np_array_mem_(self, results, classes=cfg.darknet.classes, det=cfg.xception.det1, size=cfg.xception.size):

        def resize_img(img, size):
            img_croped = img.crop(
                (
                    -((size - img.size[0]) / 2),
                    -((size - img.size[1]) / 2),
                    img.size[0] + (size - img.size[0]) / 2,
                    img.size[1] + (size - img.size[1]) / 2
                )
            )
            img_resized = img_croped.resize((size, size))

            return img_resized

        tiff_dict = get_tiff_dict()
        if self.input_file not in tiff_dict:
            raise Exception("XCEPTION PREPROCESS %s NOT FOUND" % self.input_file)

        try:
            try:
                slide = openslide.OpenSlide(tiff_dict[self.input_file])
            except:
                slide = TSlide(tiff_dict[self.input_file])
        except:
            raise Exception('TIFF FILE OPEN FAILED => %s' % self.input_file)

        cell_list = []
        cell_index = {}
        index = 0
        for x_y, boxes in results.items():
            for box in boxes:
                if box[0] in classes and box[1] > det:
                    # print(x_y)
                    _, x, y = re.findall(self.pattern, x_y)[0]
                    # print("1=> %s, %s" % (x, y))
                    x = int(x) + int(box[2][0])
                    y = int(y) + int(box[2][1])
                    w = int(box[2][2])
                    h = int(box[2][3])
                    # print("2=> %s, %s" % (x, y))

                    # center_x = x + int(w / 2 + 0.5)
                    # center_y = y + int(h / 2 + 0.5)
                    # w_ = max(w, h)
                    # h_ = w_

                    # x_ = center_x - int(w_ / 2 + 0.5)
                    # y_ = center_y - int(h_ / 2 + 0.5)

                    # x_ = 0 if x_ < 0 else x_
                    # y_ = 0 if y_ < 0 else y_

                    cell = slide.read_region((x, y), 0, (w, h)).convert("RGB")
                    # cell = slide.read_region((x_, y_), 0, (w_, h_)).convert("RGB")
                    # image_name = "%s_%s_%s_%s.jpg" % (x, y, w, h)
                    # cell.save(os.path.join('/home/tsimage/Development/DATA/middle_cells', image_name))

                    cell_list.append(np.array(resize_img(cell, size)))
                    cell_index[index] = [x_y, list(box)]
                    index += 1

        slide.close()
        # return np.asarray(cell_list), cell_index
        return cell_list, cell_index

    def gen_np_array_csv_(self, seg_csv, classes=cfg.darknet.classes, det=cfg.xception.det1, size=cfg.xception.size):
        seg_dict = self.read_csv(seg_csv)
        return self.gen_np_array_mem_(results=seg_dict, classes=classes, det=det, size=size)
