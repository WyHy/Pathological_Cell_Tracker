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

    type_lst = {}

    for key, value in dict_.items():
        if value in CLASSES:
            if value in type_lst:
                type_lst[value].append(key)
            else:
                type_lst[value] = [key]

            index = CLASSES.index(value)
            COUNT[index] += 1

    print(CLASSES)
    print(COUNT)

    for key, lst in type_lst.items():
        with open("work_tiff_list_20181102_%s.txt" % key, 'w') as o:
            o.write("%s" % ("\n".join(lst)))






