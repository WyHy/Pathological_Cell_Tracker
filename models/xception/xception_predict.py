from keras.models import *
from keras.layers import *
from keras.applications import *
from keras.preprocessing.image import *
import os
import sys
import math
sys.path.append('.')
sys.path.append('../')
sys.path.append('../../')
from config.config import cfg


class XceptionPredict:

    def __init__(self, gpu="0"):
        os.environ["CUDA_VISIBLE_DEVICES"] = gpu

        weights_file = cfg.xception.weights_file

        input_tensor = Input((299, 299, 3))
        x = Lambda(xception.preprocess_input)(input_tensor)
        base_model = Xception(input_tensor=x, weights=None, include_top=False)
        m_out = base_model.output
        p_out = GlobalAveragePooling2D()(m_out)
        fc_out = Dropout(1.0)(p_out)
        predictions = Dense(cfg.xception.class_num, activation='softmax')(fc_out)
        self.model = Model(inputs=base_model.input, outputs=predictions)
        self.model.load_weights(weights_file)

    def predict(self, cell_np, batch_size=20):
        predictions = []
        batches = math.ceil(len(cell_np)/batch_size)

        for i in range(batches):
            batch_data = cell_np[i * batch_size: (i + 1) * batch_size]
            predictions.extend((self.model).predict_on_batch(batch_data))

        return predictions
