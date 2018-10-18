"""
This script processes single images, pad it up to designated size, or if it is too big, 
split it into four pieces and pad from corresponding directions.
"""
import os
import cv2
from random import shuffle
from shutil import copy

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

def cut_and_pad(image_name, save_path, size):
	"""
	image_name: image full path name
	size: targe image size to save
	save_path: image save path
	"""
	def pad_center(img, size):
		h, w, _ = img.shape
		dh, dw = size-h, size-w
		top, bottom = dh//2, dh-dh//2
		left, right = dw//2, dw-dw//2
		img_new = cv2.copyMakeBorder(img, top=top, bottom=bottom, left=left, right=right, 
									 borderType=cv2.BORDER_CONSTANT, value=BLACK)
		return img_new

	def pad_top_left(img, size):
		h, w, _ = img.shape
		top, bottom = max(size-h, 0), 0
		left, right = max(size-w, 0), 0
		img_new = cv2.copyMakeBorder(img, top=top, bottom=bottom, left=left, right=right, 
									 borderType=cv2.BORDER_CONSTANT, value=BLACK)
		h_new, w_new, _ = img_new.shape
		return img_new[h_new-size:, w_new-size:]

	def pad_top_right(img, size):
		h, w, _ = img.shape
		top, bottom = max(size-h, 0), 0
		left, right = 0, max(size-w, 0)
		img_new = cv2.copyMakeBorder(img, top=top, bottom=bottom, left=left, right=right, 
									 borderType=cv2.BORDER_CONSTANT, value=BLACK)
		h_new, w_new, _ = img_new.shape
		return img_new[h_new-size:, :size]

	def pad_bottom_left(img, size):
		h, w, _ = img.shape
		top, bottom = 0, max(size-h, 0)
		left, right = max(size-w, 0), 0
		img_new = cv2.copyMakeBorder(img, top=top, bottom=bottom, left=left, right=right, 
									 borderType=cv2.BORDER_CONSTANT, value=BLACK)
		h_new, w_new, _ = img_new.shape
		return img_new[:size, w_new-size:]

	def pad_bottom_right(img, size):
		h, w, _ = img.shape
		top, bottom = 0, max(size-h, 0)
		left, right = 0, max(size-w, 0)
		img_new = cv2.copyMakeBorder(img, top=top, bottom=bottom, left=left, right=right, 
									 borderType=cv2.BORDER_CONSTANT, value=BLACK)
		h_new, w_new, _ = img_new.shape
		return img_new[:size, :size]

	img = cv2.imread(image_name)
	h, w, _ = img.shape
	basename = os.path.splitext(os.path.basename(image_name))[0]
	BLACK = (0, 0, 0)
	if max(h, w) < size:
		img_new = pad_center(img, size)
		cv2.imwrite(os.path.join(save_path, basename + "_0.jpg"), img_new)
	else:
		img_new = pad_top_left(img[:h//2, :w//2], size)
		cv2.imwrite(os.path.join(save_path, basename + "_1.jpg"), img_new)
		img_new = pad_top_right(img[:h//2, w//2:], size)
		cv2.imwrite(os.path.join(save_path, basename + "_2.jpg"), img_new)
		img_new = pad_bottom_left(img[h//2:, :w//2], size)
		cv2.imwrite(os.path.join(save_path, basename + "_3.jpg"), img_new)
		img_new = pad_bottom_right(img[h//2:, w//2:], size)
		cv2.imwrite(os.path.join(save_path, basename + "_4.jpg"), img_new)


def process(image_path, save_path, size):
	image_names = scan_files(image_path)
	for i in image_names:
		cut_and_pad(i, save_path, size)


if __name__ == "__main__":
	input_path = "/home/sakulaki/yolo-yuli/xxx/tct_data_samesize_0718"
	output_path = "/home/sakulaki/yolo-yuli/xxx/tct_data_samesize_0718_224"
	process(input_path, output_path, 224)
