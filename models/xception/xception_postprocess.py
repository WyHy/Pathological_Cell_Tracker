import os
import csv
import numpy as np
import openslide
import xml.dom.minidom
from shapely import geometry
from config.config import cfg
from common.tslide.tslide import TSlide
from utils import get_tiff_dict
import re

pattern = re.compile(r'(.*?)_(\d+)_(\d+)$')


class XceptionPostprocess:

    def convert(self, predictions, cell_index, classes1=cfg.darknet.classes, classes2=cfg.xception.classes,
                det=cfg.xception.det2):
        """select predictions of stage2, only when those classes appear in classes1
        :param predictions: results returned by xception predict: [numpy_array(p1,p2,...,p18),]
        :param cell_index: cell_index: {index: (x_y, [class_i, det, (x,y,w,h)])}
        :param classes1: classes1 used in darknet
        :param classes2: classes2 used in stage2(xception/inception)
        :param det: the threshold of det to use
        :return: new dict: {x_y: [[class_i, det, class_i, det, (x,y,w,h)],]}
        """
        new_dict = {}
        for index, prediction in enumerate(predictions):
            i = np.argmax(prediction)
            class_i = classes2[i]
            if class_i in classes1 and prediction[i] > det:
                x_y = cell_index[index][0]
                cell_info = cell_index[index][1][:2] + [class_i, prediction[i]] + cell_index[index][1][2:]
                if not x_y in new_dict:
                    new_dict[x_y] = [cell_info, ]
                else:
                    new_dict[x_y].append(cell_info)
        return new_dict

    def convert_all(self, predictions, cell_index, classes2=cfg.xception.classes, det=cfg.xception.det2):
        """select predictions of stage2, all classes in classes2
        :param predictions: results returned by xception predict: [numpy_array(p1,p2,...,p18),]
        :param cell_index: cell_index: {index: (x_y, [class_i, det, (x,y,w,h)])}
        :param classes2: classes2 used in stage2(xception/inception)
        :param det: the threshold of det to use
        :return: new dict: {x_y: [[class_i, det, class_i, det, (x,y,w,h)],]}
        """
        new_dict = {}
        for index, prediction in enumerate(predictions):
            i = np.argmax(prediction)
            class_i = classes2[i]
            if prediction[i] > det:
                x_y = cell_index[index][0]
                cell_info = cell_index[index][1][:2] + [class_i, prediction[i]] + cell_index[index][1][2:]
                if not x_y in new_dict:
                    new_dict[x_y] = [cell_info, ]
                else:
                    new_dict[x_y].append(cell_info)
        return new_dict

    def write_csv(self, new_dict, clas_csv):
        """
        :param new_dict: {x_y: [[class_i, det, class_i, det, (x,y,w,h)],]}
        :param clas_csv: csv full path name to save stage1&2 results
        """
        with open(clas_csv, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["x_y", "segment", "det", "classify", "det", "xmin", "ymin", "xmax", "ymax"])
            for x_y, boxes in new_dict.items():
                for box in boxes:
                    writer.writerow([x_y, box[0], box[1], box[2], box[3],
                                     box[4][0], box[4][1], box[4][0] + box[4][2], box[4][1] + box[4][3]])

    def cut_cells(self, tifname, new_dict, save_path):
        """
        :param tifname: full path name of .tif/.kfb file
        :param new_dict: {x_y: [[class_i, det, class_i, det, (x,y,w,h)],]}
        :param save_path: image saving path (note: image is saved under class_i)
        :output format: save_path/diagnosis/tifbasename/class_i/tifname_x_y_w_h.jpg (note: x, y here is relative to wsi)
        """
        try:
            slide = openslide.OpenSlide(tifname)
        except:
            slide = TSlide(tifname)
        basename = os.path.splitext(os.path.basename(tifname))[0]
        for x_y, boxes in new_dict.items():
            for box in boxes:
                # image naming: tifname_x_y_w_h.jpg
                x = int(x_y.split('_')[0]) + int(box[4][0])
                y = int(x_y.split('_')[1]) + int(box[4][1])
                w = int(box[4][2])
                h = int(box[4][3])

                image_name = "{}_x{}_y{}_w{}_h{}.jpg".format(basename, x, y, w, h)
                save_path_i = os.path.join(save_path, str(box[2]))
                os.makedirs(save_path_i, exist_ok=True)
                image_fullname = os.path.join(save_path_i, image_name)
                slide.read_region((x, y), 0, (w, h)).convert("RGB").save(image_fullname)
        slide.close()

    def cut_cells_p(self, tifname, new_dict, save_path):
        """
        :param tifname: full path name of .tif/.kfb file
        :param new_dict: {x_y: [[class_i, det, class_i, det, (x,y,w,h)],]}
        :param save_path: image saving path (note: image is saved under class_i)
        :output format: save_path/class_i/tifname_x_y_w_h_p.jpg 
                        (note: x, y here is relative to wsi.
                               p is the value of the second det.
                               image size is twice the annotation box.)
        """
        try:
            slide = openslide.OpenSlide(tifname)
        except:
            slide = TSlide(tifname)
        basename = os.path.splitext(os.path.basename(tifname))[0]
        for x_y, boxes in new_dict.items():
            for box in boxes:
                # image naming: tifname_x_y_w_h_p.jpg
                x = int(x_y.split('_')[0]) + int(box[4][0])
                y = int(x_y.split('_')[1]) + int(box[4][1])
                w = int(box[4][2])
                h = int(box[4][3])
                image_name = "{}_x{}_y{}_w{}_h{}_p{:.4f}.jpg".format(basename, x, y, w, h, box[3])
                save_path_i = os.path.join(save_path, str(box[2]))
                os.makedirs(save_path_i, exist_ok=True)
                image_fullname = os.path.join(save_path_i, image_name)
                slide.read_region((x - w // 2, y - h // 2), 0, (2 * w, 2 * h)).convert("RGB").save(image_fullname)
        slide.close()

    def cut_cells_p_marked(self, tifname, new_dict, save_path, factor=0.3, N=4):
        """
        :param tifname: full path name of .tif/.kfb file
        :param new_dict: {x_y: [[class_i, det, class_i, det, (x,y,w,h)],]}
        :param save_path: image saving path (note: image is saved under class_i)
        :param factor: overlapping threshold, added marked info to image filename if overlapped
        :output format: save_path/diagnosis/tifbasename/class_i/tifname_x_y_w_h.jpg (note: x, y here is relative to wsi)
                        (note: x, y here is relative to wsi.
                               p is the value of the second det.
                               image size is twice the annotation box.
                               check if the cell is marked, add marked if so.)
        """

        # https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
        def get_labels(xmlname):
            """collect labeled boxes from asap xml
            :param xmlname: full path name of .xml file, got from .tif/.kfb file
            :output format: [[class_i, [(xi,yi),]],]
            """
            if not os.path.isfile(xmlname):
                return []
            classes = {"#aa0000": "HSIL", "#aa007f": "ASCH", "#005500": "LSIL", "#00557f": "ASCUS",
                       "#0055ff": "SCC", "#aa557f": "ADC", "#aa55ff": "EC", "#ff5500": "AGC1",
                       "#ff557f": "AGC2", "#ff55ff": "AGC3", "#00aa00": "FUNGI", "#00aa7f": "TRI",
                       "#00aaff": "CC", "#55aa00": "ACTINO", "#55aa7f": "VIRUS", "#ffffff": "NORMAL",
                       "#000000": "MC", "#aa00ff": "SC", "#ff0000": "RC", "#aa5500": "GEC"}
            DOMTree = xml.dom.minidom.parse(xmlname)
            collection = DOMTree.documentElement
            annotations = collection.getElementsByTagName("Annotation")
            marked_boxes = []
            for annotation in annotations:
                colorCode = annotation.getAttribute("Color")
                if not colorCode in classes:
                    continue
                marked_box = [classes[colorCode], []]
                coordinates = annotation.getElementsByTagName("Coordinate")
                marked_box[1] = [(float(coordinate.getAttribute('X')), float(coordinate.getAttribute('Y'))) for
                                 coordinate in coordinates]
                marked_boxes.append(marked_box)
            return marked_boxes

        def is_overlapped(marked_boxes, predicted_box, factor):
            """check if predicted box is marked already
            :param marked_boxes: [[class_i, [(xi,yi),]],]
            :param box: (x, y, w, h)
            :param factor: overlapping threshold, added marked info to image filename if overlapped
            """
            for marked_box in marked_boxes:
                marked_box_obj = geometry.Polygon(marked_box[1])
                predicted_box_obj = geometry.box(predicted_box[0],
                                                 predicted_box[1],
                                                 predicted_box[0] + predicted_box[2],
                                                 predicted_box[1] + predicted_box[3])
                if marked_box_obj.intersection(predicted_box_obj).area / (
                        marked_box_obj.area + predicted_box_obj.area - marked_box_obj.intersection(
                        predicted_box_obj).area) >= factor:
                    return marked_box[0]
            return ""

        try:
            slide = openslide.OpenSlide(tifname)
        except:
            slide = TSlide(tifname)
        basename = os.path.splitext(os.path.basename(tifname))[0]
        parent_d = os.path.basename(os.path.dirname(tifname))
        save_path = os.path.join(save_path, parent_d, basename)
        marked_boxes = get_labels(os.path.splitext(tifname)[0] + ".xml")
        for x_y, boxes in new_dict.items():
            for box in boxes:
                # image naming: tifname_x_y_w_h_p.jpg
                x = int(x_y.split('_')[0]) + int(box[4][0])
                y = int(x_y.split('_')[1]) + int(box[4][1])
                w = int(box[4][2])
                h = int(box[4][3])

                marked_class_i = is_overlapped(marked_boxes, (x, y, w, h), factor)
                if marked_class_i:
                    image_name = "1-p{:.4f}_markedAs_{}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(1 - box[3], marked_class_i,
                                                                                           basename, x, y, w, h, N)
                    save_path_i = os.path.join(save_path, box[2], "marked")
                else:
                    image_name = "1-p{:.4f}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(1 - box[3], basename, x, y, w, h, N)
                    save_path_i = os.path.join(save_path, box[2])
                os.makedirs(save_path_i, exist_ok=True)
                image_fullname = os.path.join(save_path_i, image_name)
                slide.read_region((int(x + (1 - N) * w / 2), int(y + (1 - N) * h / 2)), 0,
                                  (int(N * w), int(N * h))).convert("RGB").save(image_fullname)

        slide.close()

    def cut_cells_p_marked_(self, tifname, new_dict, save_path, factor=0.3, N=4):
        def get_labels(xmlname):
            if not os.path.isfile(xmlname):
                return []

            classes = {"#aa0000": "HSIL", "#aa007f": "ASCH", "#005500": "LSIL", "#00557f": "ASCUS",
                       "#0055ff": "SCC", "#aa55ff": "EC", "#ff5500": "AGC",
                       "#00aa00": "FUNGI", "#00aa7f": "TRI", "#00aaff": "CC", "#55aa00": "ACTINO",
                       "#55aa7f": "VIRUS", "#ffffff": "NORMAL", "#000000": "MC", "#aa00ff": "SC",
                       "#ff0000": "RC", "#aa5500": "GEC"}
            DOMTree = xml.dom.minidom.parse(xmlname)
            collection = DOMTree.documentElement
            annotations = collection.getElementsByTagName("Annotation")
            marked_boxes = []
            for annotation in annotations:
                colorCode = annotation.getAttribute("Color")
                if not colorCode in classes:
                    continue
                marked_box = [classes[colorCode], []]
                coordinates = annotation.getElementsByTagName("Coordinate")
                marked_box[1] = [(float(coordinate.getAttribute('X')), float(coordinate.getAttribute('Y'))) for
                                 coordinate in coordinates]
                marked_boxes.append(marked_box)
            return marked_boxes

        def is_overlapped(marked_boxes, predicted_box, factor):
            for marked_box in marked_boxes:
                marked_box_obj = geometry.Polygon(marked_box[1])
                predicted_box_obj = geometry.box(predicted_box[0],
                                                 predicted_box[1],
                                                 predicted_box[0] + predicted_box[2],
                                                 predicted_box[1] + predicted_box[3])
                if marked_box_obj.intersection(predicted_box_obj).area / (
                        marked_box_obj.area + predicted_box_obj.area - marked_box_obj.intersection(
                    predicted_box_obj).area) >= factor:
                    return marked_box[0]
            return ""

        tiff_dict = get_tiff_dict()
        if tifname not in tiff_dict:
            raise Exception("XCEPTION POSTPROCESS %s NOT FOUND" % tifname)

        try:
            slide = openslide.OpenSlide(tiff_dict[tifname])
        except:
            slide = TSlide(tiff_dict[tifname])

        basename = os.path.splitext(os.path.basename(tifname))[0]
        parent_d = os.path.basename(os.path.dirname(tifname))
        save_path = os.path.join(save_path, parent_d, basename)
        marked_boxes = get_labels(os.path.splitext(tifname)[0] + ".xml")
        for x_y, boxes in new_dict.items():
            for box in boxes:
                # image naming: tifname_x_y_w_h_p.jpg
                _, x, y = re.findall(pattern, x_y)[0]
                x = int(x) + int(box[4][0])
                y = int(y) + int(box[4][1])
                w = int(box[4][2])
                h = int(box[4][3])

                marked_class_i = is_overlapped(marked_boxes, (x, y, w, h), factor)
                if marked_class_i:
                    image_name = "1-p{:.4f}_markedAs_{}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(1 - box[3],
                                                                                           marked_class_i, basename,
                                                                                           x, y, w, h, N)
                    save_path_i = os.path.join(save_path, box[2], "marked")
                else:
                    image_name = "1-p{:.4f}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(1 - box[3], basename, x, y, w, h, N)
                    save_path_i = os.path.join(save_path, box[2])

                os.makedirs(save_path_i, exist_ok=True)
                image_fullname = os.path.join(save_path_i, image_name)
                slide.read_region((int(x + (1 - N) * w / 2), int(y + (1 - N) * h / 2)), 0,
                                  (int(N * w), int(N * h))).convert("RGB").save(image_fullname)

        slide.close()
