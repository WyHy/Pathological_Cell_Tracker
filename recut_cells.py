import os
import re
import csv
from PIL import Image
import xml.dom.minidom
from shapely import geometry
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
import openslide
from common.tslide.tslide import TSlide
from common.utils import FilesScanner


def isRightN(jpgname, N):
    img = Image.open(jpgname)
    img_w, img_h = img.size
    p = re.compile("w[0-9]+_h[0-9]+")
    m = p.search(jpgname)
    if m:
        w, h = m.group(0).split('_')
        w, h = int(w[1:]), int(h[1:])
        if abs(img_w - N*w) < 2 and abs(img_h - N*h) < 2:
            return True
    return False


def scan_files(directory, prefix=None, postfix=None):
    files_list = []
    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root, special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root, special_file))
            else:
                files_list.append(os.path.join(root, special_file))
    return files_list


def need_recut(files, no_need_csv):
    no_need_list = []
    with open(no_need_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in csv_reader:
            no_need_list.append(line)
    need_list = []
    for file in files:
        basename = os.path.splitext(os.path.basename(file))[0]
        if not basename in no_need_list:
            need_list.append(file)
    return need_list


def read_labels_csv(labels_csv):
    """
    :param labels_csv: basename_clas.csv
    :return: [[x, y, w, h, p, label],]
    """
    labels = []
    with open(labels_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in csv_reader:
            # skip header
            if line[0] == "x_y":
                continue
            x, y = line[0].split('_')
            x, y = int(x), int(y)
            xmin, ymin = int(float(line[5])), int(float(line[6]))
            xmax, ymax = int(float(line[7])), int(float(line[8]))
            p = float(line[4])
            label = line[3]
            box = [x+xmin, y+ymin, xmax-xmin, ymax-ymin, p, label]
            labels.append(box)
    return labels


def read_labels_xml(xmlname):
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
        marked_box[1] = [(float(coordinate.getAttribute('X')), float(coordinate.getAttribute('Y'))) for coordinate in coordinates]
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
                                         predicted_box[0]+predicted_box[2],
                                         predicted_box[1]+predicted_box[3])
        if marked_box_obj.intersection(predicted_box_obj).area / (marked_box_obj.area + predicted_box_obj.area - marked_box_obj.intersection(predicted_box_obj).area) >= factor:
            return marked_box[0]
            
    return ""


def cut_cells(filename, labels_csv, save_path, factor, N):
    labels = read_labels_csv(labels_csv)
    marked_boxes = read_labels_xml(os.path.splitext(filename)[0]+".xml")

    try:
        slide = openslide.OpenSlide(filename)
    except:
        slide = TSlide(filename)

    basename = os.path.splitext(os.path.basename(filename))[0]
    parent_d = os.path.basename(os.path.dirname(filename))
    save_path = os.path.join(save_path, parent_d, basename)
    for box in labels:
        x, y, w, h, p, label = box
        marked_class_i = is_overlapped(marked_boxes, box, factor)
        if marked_class_i:
            image_name = "1-p{:.4f}_markedAs_{}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(p, marked_class_i, basename, x, y, w, h, N)
        else:
            image_name = "1-p{:.4f}_{}_x{}_y{}_w{}_h{}_{}x.jpg".format(p, basename, x, y, w, h, N)
        save_path_i = os.path.join(save_path, label)
        os.makedirs(save_path_i, exist_ok=True)
        image_fullname = os.path.join(save_path_i, image_name)
        x_N, y_N = int(x + (1-N)*w/2), int(y + (1-N)*h/2)
        w_N, h_N = int(N * w), int(N * h)
        slide.read_region((x_N, y_N), 0, (w_N, h_N)).convert("RGB").save(image_fullname)
    slide.close()


def get_tif_labels_csv(tifname, csv_path):
    all_csvs = FilesScanner(csv_path, postfix="clas.csv").get_files()
    for c in all_csvs:
        basename = os.path.splitext(os.path.basename(tifname))[0]
        if basename in c:
            return c
    return ""


def main(tif_path, no_need_csv, csv_path, cell_path, factor=0.3, N=4):
    tifnames = FilesScanner(tif_path, postfix=".tif").get_files() \
             + FilesScanner(tif_path, postfix=".kfb").get_files()
    need_list = need_recut(tifnames, no_need_csv)

    executor = ProcessPoolExecutor(max_workers=cpu_count()-4)
    tasks = []
    for tifname in tifnames:
        labels_csv = get_tif_labels_csv(tifname, csv_path)
        if not labels_csv:
            print("cannot find clas.csv of {}".format(tifname))
            continue

        tasks.append(executor.submit(cut_cells, tifname, labels_csv, cell_path, factor, N))
        # cut_cells(tifname, labels_csv, cell_path, factor, N)
        print("processing: {}".format(tifname))

    job_count = len(tasks)
    for future in as_completed(tasks):
        job_count -= 1
        print("One job done, rest job count: {}".format(job_count))



if __name__ == "__main__":
    tif_path = "/media/tsimage/新加卷/label_kfb_tif/stage2_labelimg"
    file_path = "/media/tsimage/新加卷/label_kfb_tif/unlabelled_for_cellCutting_tmp"
    cell_path = "/media/tsimage/新加卷/label_kfb_tif/unlabelled_for_cellCutting_cells"

    no_need_csv = "/media/tsimage/新加卷/label_kfb_tif/do_not_recut_marked.csv"
    factor = 0.3
    N = 4

    main(tif_path, no_need_csv, file_path, cell_path, factor, N)
