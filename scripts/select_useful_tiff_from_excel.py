import json


def load_dict(file_path):
    with open(file_path) as f:
        lines = f.readlines()

        dict_ = {}
        for line in lines:
            key, value = line.replace('\n', '').split('\t')
            value = json.loads(value)
            dict_[key.replace(' ', '-')] = value['zhu'] if value['zhu'] != 42 else value['doctor']

        return dict_


if __name__ == '__main__':
    dict_ = load_dict('DIAGNOSE_RESULT_DICT.txt')
    CLASSES = ['AGC', 'VIRUS', 'EC', 'FUNGI', 'ACTINO']
    COUNT = [0] * len(CLASSES)

    for key, value in dict_.items():
        if value in CLASSES:
            COUNT[CLASSES.index(value)] += 1

    print(CLASSES)
    print(COUNT)




