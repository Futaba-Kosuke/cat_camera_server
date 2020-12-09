import sys
import json
import base64
import requests
import cv2
import os
import glob

url = sys.argv[1]

with open('./data.json', 'r') as f:
    payload = json.load(f)

payload = json.dumps(payload).encode("utf-8")
print(payload, type(payload))

headers = {"Content-Type": "application/json"}

response = requests.post('{}/training'.format(url), headers=headers, data=payload)
print(response)
