from common.utils import ImageSlice, ImageSliceInMemory, FilesScanner

if __name__ == '__main__':
    """
    多进程切图示例代码
    """
    # input_file_path = '/home/sakulaki/yolo-yuli/one_stop_test/tif/XB1800118.tif'
    # output_file_path = '/tmp/metadata/lbp/output/'
    #
    # worker = ImageSlice(input_file_path, output_file_path)
    # print(worker.get_slices())

    # 直接返回 image numpy list
    # for item in FilesScanner('/home/sakulaki/yolo-yuli/uncomplete/').get_files():

    input_file_path = '/home/sakulaki/yolo-yuli/one_stop_test/tif/XB1800118.tif'
    worker = ImageSliceInMemory(input_file_path)
    err_code, results = worker.get_slices()
    if err_code == 0:
        print(type(results))
        print(len(results))
    else:
        print('ERROR', results)


