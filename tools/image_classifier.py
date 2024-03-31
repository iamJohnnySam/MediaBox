from datetime import datetime
import random
import numpy as np

import global_variables
import refs
from brains.job import Job
from tools import logger
from PIL import Image
import os
import shutil

if global_variables.operation_mode:
    import tflite_runtime.interpreter as tflite


class ImageClassifier:
    def __init__(self, job: Job, nn_path, nn_name="A00", save_random=0.75, threshold=0.6):
        self.job = job
        self.output_data = None
        self.nn_name = nn_name
        self.save_random = save_random
        self.threshold = threshold

        if global_variables.operation_mode:
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

        if global_variables.operation_mode:
            self.model.set_tensor(self.input_details[0]['index'], img)
            self.model.invoke()
            self.output_data = self.model.get_tensor(self.output_details[0]['index'])
            output = self.output_data[0][0]
        else:
            output = random.random() * random.random()
            logger.log(self.job.job_id, f"CNN output set to {output} as not in operation mode")

        if output > self.threshold:
            sus = True
            sav = os.path.join(refs.cctv_save, self.nn_name, "1")
        else:
            sus = False
            sav = os.path.join(refs.cctv_save, self.nn_name, "0")

        copy_destination = "None"
        if random.random() > self.save_random and global_variables.operation_mode:
            if not os.path.exists(sav):
                os.makedirs(sav)

            file_name = datetime.now().strftime("%Y-%m-%d, %H-%M-%S") + ".jpg"

            copy_destination = shutil.copyfile(att_path,
                                               os.path.join(sav, file_name))
            logger.log(self.job.job_id, "Image Saved - " + copy_destination)
        return output, sus, copy_destination
