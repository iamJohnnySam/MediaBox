import random
import numpy as np

from brains.job import Job
from tools import params
from shared_tools import logger
from PIL import Image

if params.is_module_available('cctv'):
    import tflite_runtime.interpreter as tflite


class ImageClassifier:
    def __init__(self, job: Job, nn_path, nn_name="A00", threshold=0.6):
        self.job = job
        self.output_data = None
        self.nn_name = nn_name
        self.threshold = threshold

        if params.is_module_available('cctv'):
            # self.model = tf.lite.Interpreter(model_path=nn_path)
            self.model = tflite.Interpreter(model_path=nn_path)
            self.model.allocate_tensors()
            self.input_details = self.model.get_input_details()
            self.output_details = self.model.get_output_details()
            logger.log(self.job.job_id, "Convolutional Neural Network initiated for channel " + nn_name)
        else:
            logger.log(self.job.job_id, "Convolutional Neural Network for channel " + nn_name +
                       "not started as not in operation mode.")

    def classify(self, att_path):
        img = Image.open(att_path)
        img = np.float32(img)
        img = np.expand_dims(img, axis=0)

        if params.is_module_available('cctv'):
            self.model.set_tensor(self.input_details[0]['index'], img)
            self.model.invoke()
            self.output_data = self.model.get_tensor(self.output_details[0]['index'])
            output = self.output_data[0][0]
        else:
            output = random.random() * random.random()
            logger.log(self.job.job_id, f"CNN output set to {output} as not in operation mode")

        sus = True if output > self.threshold else False

        return output, sus
