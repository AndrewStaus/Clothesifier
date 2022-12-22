from tflite_runtime.interpreter import Interpreter
from fastapi import FastAPI, Form, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from mangum import Mangum
from PIL.ImageOps import invert
from PIL import Image
import numpy as np
import base64
import io

LABELS = [
    'T-shirt/top',  # 0
    'Trouser',      # 1
    'Pullover',     # 2
    'Dress',        # 3
    'Coat',         # 4
    'Sandal',       # 5
    'Shirt',        # 6
    'Sneaker',      # 7
    'Bag',          # 8
    'Ankle boot'    # 9
    ]

interpreter = Interpreter('model.tflite')
app = FastAPI()
handler = Mangum(app)

def _set_input_tensor(interpreter, image):
    interpreter.allocate_tensors()
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image

def predict(interpreter, image):
    _set_input_tensor(interpreter, image)
    interpreter.invoke()
    output_details = interpreter.get_output_details()[0]
    scores = interpreter.get_tensor(output_details['index'])[0]
    return scores

def process(content):

    image = Image.open(io.BytesIO(content))
    image = image.convert('L') # convert to black and white
    
    # pad image to be square
    pad_color = int(np.argmax(np.bincount(np.array(image).flatten())))
    width, height = image.size
    if width == height:
        square = image
    elif width > height:
        square = Image.new(image.mode, (width, width), (pad_color))
        square.paste(image, (0, (width - height) // 2))
    else:
        square = Image.new(image.mode, (height, height), (pad_color))
        square.paste(image, ((height - width) // 2, 0))
    image = square

    image = image.resize((28,28)) # resize to 28 by 28
    image = invert(image) # invert color

    image = np.array(image) # convert to numpy array
    image = image - image.min() # maximize contrast
    image = image / image.max() # normalize values to be between 0 and 1
    image = np.reshape(image, (28, 28, 1)) # reshape

    return image


class Result(BaseModel):
    category: str
    confs: List[Dict] = []

@app.post("/image")
async def get_image(filename: str = Form(...), filedata: str = Form(...)):
    try:
        image_as_bytes = str.encode(filedata)  # convert string to bytes
        img_recovered = base64.b64decode(image_as_bytes)  # decode base64string
        image = process(img_recovered)
        
        pred = predict(interpreter, image)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/")
def root():
    return {'message':[
        'Welcome to Clothesifier API',
        'Git Page: https://github.com/AndrewStaus/Clothesifier',
        'Website: https://andrewstaus.github.io/Clothesifier/'
        ]}