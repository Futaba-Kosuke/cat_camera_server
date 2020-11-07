from flask import Flask, request
from flask_cors import CORS

import os
import sys
import base64
import datetime
import json
import requests

import numpy as np
import cv2

from firebase.firebase import Firebase

app = Flask(__name__)
CORS(app)

firebase = Firebase()

train_url = sys.argv[1]

def base64_to_numpy(img_base64):
    # base64をnumpyに変換
    img_bytes = base64.b64decode(img_base64)
    temp = np.frombuffer(img_bytes, np.uint8)
    img_np = cv2.imdecode(temp, cv2.IMREAD_ANYCOLOR)
    return img_np

def numpy_to_base64(img_np):
    # numpyをbase64に変換
    _, temp = cv2.imencode('.jpeg', img_np)
    img_base64 = base64.b64encode(temp)
    return img_base64

@app.route('/test', methods=['GET', 'POST'])
def func_test():
    try:
        if request.method == 'GET':
            return request.args.get('query', '')
        elif request.method == 'POST':
            return request.json
        else:
            return abort(400)
    except Exception as e:
        return str(e)

@app.route('/upload', methods=['POST'])
def upload_from_base64():
    img_base64 = request.form['img_base64']

    img_np = base64_to_numpy(img_base64)

    file_name = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    file_path = './firebase/{}.jpeg'.format(file_name)
    cv2.imwrite(file_path, img_np)
 
    firebase.upload_file(file_path=file_path)

    os.remove(file_path)

    return '200'

@app.route('/training', methods=['POST'])
def training_cats():
    data_json = request.data.decode('utf-8')
    data_dict = json.loads(data_json)
    data_dict['cred'] = json.load(open('./firebase/cred.json', 'r'))

    payload = json.dumps(data_dict).encode('utf-8')

    headers = { 'Content-Type': 'application/json' }

    response = requests.post('{}/training'.format(train_url), data=payload, headers=headers)

    print(response)

    return '200'

app.run()
