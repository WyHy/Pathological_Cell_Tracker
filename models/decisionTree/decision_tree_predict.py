from sklearn.externals import joblib

from utils import load_classes
from config.config import cfg


class DecisionTreePredict(object):
    def __init__(self):
        self.classes = load_classes(cfg.decision_tree.classes_files)
        self.model = joblib.load(cfg.decision_tree.model)

    def predict(self, dict_):
        X = [0] * len(self.classes)
        for key, lst in dict_.items():
            for item in lst:
                index = self.classes.index(item[3])
                X[index] += 1

        Y_predict = self.model.predict_proba(X)
        indexes = [i for i, item in enumerate(Y_predict) if float(item) > 0]

        result = [self.classes[index] for index in indexes]

        return "+".join(result)
