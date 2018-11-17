import os

import openslide
from tslide.tslide import TSlide


def matting_job(points_lst, slide_path, output):
    try:
        slide = openslide.OpenSlide(slide_path)
    except:
        slide = TSlide(slide_path)

    for point in points_lst:
        yolo_label = point['yolo_cell_class']
        yolo_accu = point['yolo_cell_det']
        xcp_label = point['xcp_cell_class']
        xcp_accu = point['xcp_cell_class_det']
        x = point['x']
        y = point['y']
        w = point['w']
        h = point['h']
        image_data = point['cell_image']

        basename, _ = os.path.splitext(os.path.basename(slide_path))
        save_path = os.path.join(output, basename, xcp_label)
        os.makedirs(save_path, exist_ok=True)
        image_name = "%.4f_%s_%.4f_%s_%s_%s_%s_.jpg" % (xcp_accu, yolo_label, yolo_accu, x, y, w, h)

        # get image data program
        image_data.save(os.path.join(save_path, image_name))

        # get image from slide
        image_name = "%.4f_%s_%.4f_%s_%s_%s_%s.jpg" % (xcp_accu, yolo_label, yolo_accu, x, y, w, h)
        slide.read_region((point['x'], point['y']), 0, (point['w'], point['h'])).convert("RGB").save(
            os.path.join(save_path, image_name))


if __name__ == '__main__':
    # points_lst = []
    # slide_path = ""
    # output = ""
    # matting_job(points_lst, slide_path, output)

    path = ''
    try:
        slide = openslide.OpenSlide(path)
    except:
        slide = TSlide(path)
