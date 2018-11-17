import requests
import time
from lbp_algo_tiff_worker_for_demo import slides_diagnose_worker

jwt_cache = {}
HOST = '192.168.2.148'


def get_jwt(open_id):
    if open_id not in jwt_cache:
        login_url = 'http://%s/api/v1/auth_token/' % HOST
        response = requests.post(login_url, json={'username': 'convert', 'password': 'tsimage666'})
        if response.status_code != 200:
            raise Exception('can not logins', response.json())
        jwt_cache[open_id] = 'JWT {}'.format(response.json()['token'])
    return jwt_cache[open_id]


def get_game_status(tiff_dir_path, resource_save_path):
    header = {"Authorization": "JWT %s" % get_jwt('convert')}

    while 1:
        response = requests.get('http://%s/api/v1/game/' % HOST, headers=header)
        if response.status_code == 200 and response.json():
            data = response.json()
            status = data['status']
            if status == 1:
                slides_diagnose_worker(tiff_dir_path, resource_save_path)
            else:
                time.sleep(3)
                print("Waiting for game start ...")
                continue
        else:
            raise Exception(response.json())


if __name__ == '__main__':
    tiff_dir_path = "/home/cnn/Development/DATA/TRAIN_DATA/TIFFS/201811132110_FULL_TEST/TIFFS/"
    resource_save_path = "/home/cnn/Development/DATA/TRAIN_DATA/TIFFS/201811132110_FULL_TEST/"
    get_game_status(tiff_dir_path, resource_save_path)


