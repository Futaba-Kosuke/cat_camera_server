import numpy as np
from PIL import Image

import torch
from torch import nn, optim

import torchvision
from torchvision import transforms, models

class Classification:

    def __init__ (self, model_path, classes):
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        self.net = models.densenet161()
        last_in_features = self.net.classifier.in_features
        # self.net.classifier = nn.Linear(last_in_features, len(classes))
        self.net.classifier = nn.Linear(last_in_features, 3)
        self.net = self.net.to(device)

        self.net.load_state_dict(torch.load(model_path, map_location=device))

        self.classes = classes

        self.transform = torchvision.transforms.Compose([
            transforms.Resize((200, 200)),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

    def predict (self, img_np):
        with torch.no_grad():
            img_pil = Image.fromarray(img_np)
            x = torch.reshape(self.transform(img_pil), [1, 3, 200, 200])
            y = self.net(x)
            _, predicted = torch.max(y, 1)
            return self.classes[predicted]
