from tflite_runtime.interpreter import Interpreter
from fastapi import FastAPI, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from mangum import Mangum
from PIL import Image
from PIL.ImageOps import invert
import numpy as np
import io

LABELS = {0: 'T-shirt/top', 1: 'Trouser', 2: 'Pullover', 3: 'Dress', 4: 'Coat',
          5: 'Sandal',      6: 'Shirt',   7: 'Sneaker',  8: 'Bag',   9: 'Ankle boot'}

app = FastAPI()


handler = Mangum(app)
INTR = Interpreter('model.tflite')

def set_input_tensor(interpreter, image):
    interpreter.allocate_tensors()
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image

def predict(interpreter, image):
    set_input_tensor(interpreter, image)
    interpreter.invoke()
    output_details = interpreter.get_output_details()[0]
    scores = interpreter.get_tensor(output_details['index'])[0]
    return scores

def process(file):
    content = file.file.read()
    image = Image.open(io.BytesIO(content))
    # pad image to be square
    width, height = image.size
    if width == height:
        square = image
    elif width > height:
        square = Image.new(image.mode, (width, width), (255,255,255))
        square.paste(image, (0, (width - height) // 2))
    else:
        square = Image.new(image.mode, (height, height), (255,255,255))
        square.paste(image, ((height - width) // 2, 0))
    image = square

    
    image = image.resize((28,28)) # resize to 28 by 28
    image = image.convert('L') # convert to black and white
    image = invert(image) # invert color

    image = np.array(image) # convert to numpy array
    image = image / 255 # normalize values to be between 0 and 1
    image = np.reshape(image, (28, 28, 1)) # reshape

    return image


class Result(BaseModel):
    category: str
    confs: List[Dict] = []

@app.post("/image")
async def get_image(file: UploadFile):
    image = process(file)
    print
    pred = predict(INTR, image)
    category = LABELS[pred.argmax()]

    confs = []
    for i, confidence in enumerate(pred):
        d = {}
        d["name"] = LABELS[i]
        d["conf"] = round(confidence * 100, 2)
        confs.append(d)
    confs.sort(key=lambda x: -x['conf'])
    json = jsonable_encoder(Result(category=category, confs=confs))
    return JSONResponse(content=json)

@app.get("/")
def root():
    return {'message':['Welcome to Clothesifier API', 'Git Page: https://github.com/AndrewStaus/Clothesifier', 'Website:']}