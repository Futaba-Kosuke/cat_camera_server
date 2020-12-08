from flask import Flask, request
from flask_cors import CORS

import os
import sys
import base64
import datetime
import json
import requests
import urllib

import numpy as np
import cv2

from firebase.firebase import Firebase
from classification.classification import Classification

app = Flask(__name__)
CORS(app)

firebase = Firebase()

MODEL_PATH = 'classification/densenet.pth'

# 起動時に最新のモデルに更新
densenet_ref = firebase.get_document_ref(collection='model', document='densenet')
densenet_info = densenet_ref.get().to_dict()
if densenet_info['is_enable'] and ( densenet_info['is_update'] or not os.path.isfile(MODEL_PATH) ):
    file_name = MODEL_PATH
    file_url = densenet_info['url']
    urllib.request.urlretrieve(file_url, file_name)

    densenet_ref.set({
        'is_enable': True,
        'is_update': False,
        'url': densenet_info['url'],
        'labels': densenet_info['labels']
    })

if os.path.isfile(MODEL_PATH):
    classification = Classification(model_path=MODEL_PATH, classes=densenet_info['labels'])

# 訓練用サーバーの URL を指定
train_url = sys.argv[1]

# base64画像 -> numpy画像
def base64_to_numpy(img_base64):
    img_bytes = base64.b64decode(img_base64)
    temp = np.frombuffer(img_bytes, np.uint8)
    img_np = cv2.imdecode(temp, cv2.IMREAD_ANYCOLOR)
    return img_np

# numpy画像 -> base64画像
def numpy_to_base64(img_np):
    _, temp = cv2.imencode('.jpeg', img_np)
    img_base64 = base64.b64encode(temp)
    return img_base64

# 接続テスト用
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

# FireStorage & Firestore へのデータのアップロード
@app.route('/upload', methods=['POST'])
def upload_from_base64():

    data = request.data.decode('utf-8')
    data = json.loads(data)

    img_base64 = data['img_base64']
    cat_boxes = data['cat_boxes']

    img_np = base64_to_numpy(img_base64)

    labels = [None] * len(cat_boxes)
    if os.path.isfile(MODEL_PATH):
        for i, box in enumerate(cat_boxes):
            labels[i] = classification.predict(img_np[int(box['y_min']): int(box['y_max']), int(box['x_min']): int(box['x_max'])])

    print(labels)

    # 画像を一旦サーバー上に保存
    file_name = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    file_path = './firebase/{}.jpeg'.format(file_name)
    cv2.imwrite(file_path, img_np)
 
    # ファイルを送信
    firebase.upload_file(file_path=file_path, cat_boxes=cat_boxes, labels=labels)

    # 一時保存したファイルの削除
    os.remove(file_path)

    return '200'

# GPUサーバーで学習を行う
@app.route('/training', methods=['POST'])
def training_cats():
    data_json = request.data.decode('utf-8')
    data_dict = json.loads(data_json)
    data_dict['cred'] = json.load(open('./firebase/cred.json', 'r'))

    # 送信するJsonを生成
    payload = json.dumps(data_dict).encode('utf-8')

    # POSTするデータの型をJsonに変更
    headers = { 'Content-Type': 'application/json' }

    # GPUサーバーに送信
    response = requests.post('{}/training'.format(train_url), data=payload, headers=headers)

    print(response)

    # 最新モデルに更新
    densenet_ref = firebase.get_document_ref(collection='model', document='densenet')
    densenet_info = densenet_ref.get().to_dict()
    if densenet_info['is_enable'] and ( densenet_info['is_update'] or not os.path.isfile(MODEL_PATH) ):
        file_name = MODEL_PATH
        file_url = densenet_info['url']
        urllib.request.urlretrieve(file_url, file_name)

        densenet_ref.set({
            'is_enable': True,
            'is_update': False,
            'url': densenet_info['url'],
            'labels': densenet_info['labels']
        })

    return '200'

app.run()
