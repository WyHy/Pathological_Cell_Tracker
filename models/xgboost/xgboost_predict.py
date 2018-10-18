# from sklearn.model_selection import train_test_split
# from sklearn import metrics
# from sklearn.feature_extraction.text import CountVectorizer,TfidfTransformer
from pandas import read_csv
from sklearn.externals import joblib
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score

import sys

sys.path.append('.')
sys.path.append('../')
sys.path.append('../../')
from config.config import cfg


class XgboostPredict:

    def predict(self, csv_file):
        pkl_file = cfg.xgboost.pkl_file
        dataset = read_csv(csv_file, index_col=0)
        classes = cfg.xgboost.classes
        X = dataset.iloc[:, 1:]
        y = dataset.iloc[:, 0]
        x_test = X
        y_test = y
        with open(pkl_file, 'rb') as f:
            model = joblib.load(f)

        def confusion_accuracy(x_test, y_true, model):
            y_pred = model.predict(x_test)
            cm = confusion_matrix(y_true=y_true, y_pred=y_pred)
            cr = classification_report(y_true=y_true, y_pred=y_pred)
            acc = accuracy_score(y_true=y_true, y_pred=y_pred)
            print('Model name:', model.__class__.__name__)
            print(model.__class__.__name__ + ' confusion_matrix:\n', cm)
            print(model.__class__.__name__ + ' classification_report:\n', cr)
            print(model.__class__.__name__ + ' classification_report:', acc)
            print(
                model.__class__.__name__ + ' classification_report: predict {}, accuracy {}'.format(classes[y_pred[0]],
                                                                                                    acc))
            return classes[y_pred[0]]

        return confusion_accuracy(x_test, y_test, model)
