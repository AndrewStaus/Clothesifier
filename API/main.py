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

LABELS = [         # Class labels
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

interpreter = Interpreter('model.tflite') # tflite interpreter to run model
app = FastAPI() # api framework
handler = Mangum(app) # handler wrapper for AWS Lambda

def _set_input_tensor(interpreter: Interpreter, X: np.ndarray) -> None:
    interpreter.allocate_tensors()
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = X

def predict(interpreter: Interpreter, X: np.ndarray) -> np.ndarray:
    '''## Predict Image Class
    Get the model prediction for an image.
    
    ### Arguments:
    - interpreter -- TFLite model interpreter
    - X -- Data for the model to predict
    
    ### Returns:
    - The model prediction'''
    _set_input_tensor(interpreter, X)
    interpreter.invoke()
    output_details = interpreter.get_output_details()[0]
    y = interpreter.get_tensor(output_details['index'])[0]
    return y

def process(image: io.BytesIO) -> np.ndarray:
    '''## Process Image File

    Process a common image file into a format that the ml model can ingest.
    - Convert to black and white
    - Pad image so that it is square
    - Resize to 28, 28
    - Invert so that black is 255 and white is 0
    - Subtract the minimum pixel value from all pixels, so that the minimum value is 0
    - Normalize all values between 0 and 1 by dividing by the largest value
    - Reshape to (28, 28, 1) (x, y, chanel)
    
    ### Arguments:
    - image -- A common image file in format .jpg, .png, .gif... etc.
    
    ### Returns:
    - A numpy array of shape (28, 28, 1)'''
    image = Image.open(image)
    image = image.convert('L') # convert to black and white

    # pad image to be square

    # use the most commonly occurring color as the padding background
    # if the original image has a flat background, this should work well
    # may have issues if there is a complex background
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
    # end pad

    image = image.resize((28,28)) # resize to 28 by 28
    image = invert(image) # invert color

    X = np.array(image) # convert to numpy array
    X = X - X.min() # reduce all values so that the lowest value is 0
    X = X / X.max() # normalize values to be between 0 and 1, increasing contrast and fitting model requirements
    X = np.reshape(X, (28, 28, 1)) # reshape

    return X

# result class for JSON conversion
class Result(BaseModel):
    category: str
    confs: List[Dict] = []

@app.post("/image")
async def post_image(filedata: str = Form(...)):
    '''## Post Image

    The normal API endpoint.  Accepts a Base64 encoded image file of a piece of clothing
    and will return JSON formatted class prediction for the image.  For best results:
    - The picture should be a 1:1 aspect ratio
    - Clothing should fill as much of the frame as possible
    - Background should be flat, and a lighter color than the clothing
    
    Example JS code for frontend:
        async function uploadFile(base64String) {
            clearResults();
            var $alert = $('.alert');
            let formData = new FormData();
            formData.append("filename", 'image')
            formData.append("filedata", base64String)
            $.ajax('https://xxlkbgor75nvr7qw256z2xnrdm0ppqai.lambda-url.us-east-2.on.aws/image', {
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                        
                success: function (data) {
                    $alert.hide();
                    document.getElementById('result').innerHTML = data.category
                    updateTable(data.confs)
                    },
                error: function () {
                    $alert.show();
                    }
            });
        }
        
    ### Arguments:
        - filedata -- Base64 encoded string containing the file data

    ### Returns:
        - JSON formatted predictions {'category':str, 'confs':[{str:float}]}
    
    ### Exception
        - Raise HTTPException
    '''

    try:
        image_as_bytes = str.encode(filedata)  # convert string to bytes
        image_recovered = base64.b64decode(image_as_bytes)  # decode base64string
        image = io.BytesIO(image_recovered) # convert to file
        X = process(image) # convert file to ndarray formatted for the model
        
        pred = predict(interpreter, X) # get class prediction
        category = LABELS[pred.argmax()] # label of highest confidence

        # reformat confidences for JSON
        confs = []
        for i, confidence in enumerate(pred):
            dic = {}
            dic["name"] = LABELS[i]
            dic["conf"] = round(confidence * 100, 2)
            confs.append(dic)
        # sort confidences in descending order
        confs.sort(key=lambda x: -x['conf'])
        # encode to json
        json = jsonable_encoder(Result(category=category, confs=confs))
        # respond to API post with json
        return JSONResponse(content=json)
    except Exception as e:
        # respond to API post with error code 500, and the details of the error for debugging
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def get_root():
    '''## Get Root

    Returns a welcome message when a get request is received on the root endpoint.
    This is a simple way to check to see if the API is running.

    ### Returns:
        - JSON welcome message
    '''

    return {'message':[
        'Welcome to Clothesifier API',
        'Git Page: https://github.com/AndrewStaus/Clothesifier',
        'Website: https://andrewstaus.github.io/Clothesifier/'
        ]}