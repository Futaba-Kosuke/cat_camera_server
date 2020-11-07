import sys
import json
import base64
import requests
import cv2
import os
import glob

url = sys.argv[1]

def numpy_to_base64(img_np):
    _, temp = cv2.imencode('.jpeg', img_np)
    img_base64 = base64.b64encode(temp)
    return img_base64

paths = glob.glob(os.path.join('./datasets', '*', '**', '*'), recursive=True)

payload = {
    'data_list': [{}] * len(paths),
}
for i, path in enumerate(paths):
    img = cv2.imread(path)
    img_base64 = numpy_to_base64(img)
    data = {
        'img': img_base64.decode('utf-8'),
        'label': os.path.basename(os.path.dirname(path))
    }
    payload['data_list'][i] = data

payload = json.dumps(payload).encode("utf-8")

headers = {"Content-Type": "application/json"}

response = requests.post('{}/training'.format(url), headers=headers, data=payload)
print(response)
