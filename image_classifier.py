import tensorflow as tf
import numpy as np
import settings
from PIL import Image, ImageOps


def initiate_nn_models():
    global model1
    global model2
    global input_details1
    global input_details2
    global output_details1
    global output_details2

    model1 = tf.lite.Interpreter(model_path=settings.cctv_model1)
    model1.allocate_tensors()
    input_details1 = model1.get_input_details()
    output_details1 = model1.get_output_details()

    model2 = tf.lite.Interpreter(model_path=settings.cctv_model1)
    model2.allocate_tensors()
    input_details2 = model2.get_input_details()
    output_details2 = model2.get_output_details()


def classify(model, att_path):
    img = Image.open(att_path)
    img = ImageOps.grayscale(img)
    img = np.asarray(img, dtype="float32") / 255
    img = np.expand_dims(img, axis=0)

    if "A01" in model:
        model1.set_tensor(input_details1[0]['index'], img)
        model1.invoke()
        output_data = model1.get_tensor(output_details1[0]['index'])
        output = output_data[0][0]

        if output > 0.1:
            sus = True
        else:
            sus = False

    elif "A02" in model:
        model2.set_tensor(input_details2[0]['index'], img)
        model2.invoke()
        output_data = model2.get_tensor(output_details2[0]['index'])
        output = output_data[0][0]

        if output > 0.25:
            sus = True
        else:
            sus = False
    else:
        output = 0
        sus = False

    return output, sus
