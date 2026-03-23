import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
import timm
import os

LABELS = [
    'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration', 'Mass', 'Nodule', 'Pneumonia',
    'Pneumothorax', 'Consolidation', 'Edema', 'Emphysema', 'Fibrosis', 'Pleural_Thickening', 'Hernia'
]

class CGC_IEViT(nn.Module):
    def __init__(self, num_classes=14, pretrained=False):
        super(CGC_IEViT, self).__init__()
        
        self.cnn = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1, groups=32),
            nn.Conv2d(64, 64, kernel_size=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout2d(0.1),
            
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1, groups=64),
            nn.Conv2d(128, 128, kernel_size=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Dropout2d(0.1),
            
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1, groups=128),
            nn.Conv2d(256, 256, kernel_size=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Dropout2d(0.1)
        )
        
        self.vit = timm.create_model('vit_small_patch16_224', pretrained=pretrained, num_classes=0)
        self.patch_embed = nn.Conv2d(256, 384, kernel_size=4, stride=4)
        
        self.head = nn.Sequential(
            nn.Linear(self.vit.num_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        x = self.cnn(x)
        x = self.patch_embed(x)
        x = x.flatten(2).transpose(1, 2)
        
        B = x.shape[0]
        cls_tokens = self.vit.cls_token.expand(B, -1, -1)
        x = torch.cat((cls_tokens, x), dim=1)
        x = x + self.vit.pos_embed
        x = self.vit.pos_drop(x)
        
        x = self.vit.blocks(x)
        x = self.vit.norm(x)
        
        cls_output = x[:, 0]
        out = self.head(cls_output)
        return out

# --- 1. Load Model at Server Startup ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Loading deep learning model on {device}...")

model_path = os.path.join(os.path.dirname(__file__), "best_cgc_ievit.pth")
model = CGC_IEViT(num_classes=14, pretrained=False)

try:
    # map_location ensures it doesn't crash if the server CPU only
    model.load_state_dict(torch.load(model_path, map_location=device))
    print("Model weights loaded successfully!")
except Exception as e:
    print(f"WARNING: Make sure '{model_path}' is in the backend folder! Error: {e}")

model.to(device)
model.eval()

# --- 2. Image Transformations ---
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- 3. Replace the Dummy Predict Function ---
def predict(image_path: str):
    try:
        # Load and verify image
        image = Image.open(image_path).convert('RGB')
        input_tensor = transform(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probs = torch.sigmoid(outputs).cpu().numpy()[0]
            
        # Get highest probability
        max_prob = float(np.max(probs))
        max_index = int(np.argmax(probs))
        
        # If all probabilities are below 50%, classify as Normal
        if max_prob < 0.5:
            return "Normal / No Finding", round(1.0 - max_prob, 2)
            
        predicted_disease = LABELS[max_index]
        return predicted_disease, round(max_prob, 2)
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        return "Processing Error", 0.0
