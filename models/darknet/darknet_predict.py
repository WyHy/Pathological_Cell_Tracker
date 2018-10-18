from models.darknet.darknet import *
from config.config import cfg


class DarknetPredict:

    def __init__(self, thresh=.5, hier_thresh=.5, nms=.45, gpu='0'):

        os.environ["CUDA_VISIBLE_DEVICES"] = gpu

        self.thresh = thresh
        self.hier_thresh = hier_thresh
        self.nms = nms

        self.gen_datacfg_file()

        self.net = load_net(cfg.darknet.cfg_file.encode('utf-8'), cfg.darknet.weights_file.encode('utf-8'), 0)
        self.meta = load_meta(cfg.darknet.datacfg_file.encode('utf-8'))

    def gen_datacfg_file(self):
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

    def predict(self, images):
        def rm_duplicates(boxes):
            boxes_new = []
            for box in boxes:
                if len(boxes_new) == 0:
                    boxes_new.append(box)
                is_dup = False
                for box_new in boxes_new:
                    if abs(box[2][0] - box_new[2][0]) < 1.0 and abs(box[2][1] - box_new[2][1]) < 1.0:
                        is_dup = True
                if not is_dup:
                    boxes_new.append(box)
            return boxes_new

        results = {}
        for image in images:
            #   results.append(detect_with_rawdata(self.net, self.meta, image, self.thresh, self.hier_thresh, self.nms))
            results[os.path.splitext(os.path.basename(image))[0]] = detect(self.net, self.meta, image, self.thresh,
                                                                           self.hier_thresh, self.nms)
        results_new = {}
        for x_y, boxes in results.items():
            if len(boxes) == 0:
                continue
            results_new[x_y] = []
            boxes = rm_duplicates(boxes)
            for box in boxes:
                box_new = [box[0],
                           box[1],
                           [box[2][0] - box[2][2] / 2,
                            box[2][1] - box[2][3] / 2,
                            box[2][2],
                            box[2][3]]]
                results_new[x_y].append(box_new)
        return results_new
