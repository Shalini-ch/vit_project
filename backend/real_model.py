import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np
import os
import timm

LABELS = [
    'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration', 'Mass', 'Nodule', 'Pneumonia',
    'Pneumothorax', 'Consolidation', 'Edema', 'Emphysema', 'Fibrosis', 'Pleural_Thickening', 'Hernia'
]

# ==========================================
# 1. Custom CGC_IEViT Architecture
# ==========================================
class GraphConvolution(nn.Module):
    def __init__(self, in_features, out_features, bias=True):
        super(GraphConvolution, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.weight)
        if self.bias is not None:
            nn.init.zeros_(self.bias)

    def forward(self, text, adj):
        support = torch.matmul(text, self.weight)
        output = torch.matmul(adj, support)
        if self.bias is not None:
            return output + self.bias
        else:
            return output

class CGC_IEViT(nn.Module):
    def __init__(self, num_classes=14):
        super(CGC_IEViT, self).__init__()
        
        # Load pre-trained ViT as base
        self.vit = timm.create_model('vit_base_patch16_224', pretrained=False, num_classes=0)  
        self.vit_dim = self.vit.num_features 
        
        # CGViT components
        self.gc1 = GraphConvolution(self.vit_dim, 512)
        self.gc2 = GraphConvolution(512, 256)
        
        self.classifier = nn.Sequential(
            nn.Linear(self.vit_dim + 256, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )

        # Static Adjacency matrix for 1 node
        self.adj = nn.Parameter(torch.ones(1, 1), requires_grad=False)

    def forward(self, x):
        img_features = self.vit(x) 
        img_features_gcn = img_features.unsqueeze(1) 
        adj_batch = self.adj.unsqueeze(0).expand(x.size(0), -1, -1)
        
        x_gcn = F.relu(self.gc1(img_features_gcn, adj_batch))
        x_gcn = F.relu(self.gc2(x_gcn, adj_batch))
        
        x_gcn = x_gcn.squeeze(1) 
        fused_features = torch.cat((img_features, x_gcn), dim=1)
        
        out = self.classifier(fused_features)
        return out

# ==========================================
# 2. Load New Kaggle Weights at Server Startup
# ==========================================
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Loading CGC_IEViT model on {device}...")

# THIS MUST MATCH YOUR KAGGLE DOWNLOAD!
model_path = os.path.join(os.path.dirname(__file__), "best_cgc_ievit.pth")

# Instantiate the model architecture
model = CGC_IEViT(num_classes=14)

try:
    # Load the Kaggle weights
    state_dict = torch.load(model_path, map_location=device)
    
    # Check if 'model_state_dict' key exists (from our Kaggle training script)
    if 'model_state_dict' in state_dict:
        model.load_state_dict(state_dict['model_state_dict'], strict=False)
    else:
        model.load_state_dict(state_dict, strict=False)
        
    print("New CGC_IEViT 22-Epoch weights loaded successfully!!")
except Exception as e:
    print(f"WARNING: Weights failed to load! Is '{model_path}' in the backend folder? Error: {e}")

model.to(device)
model.eval()

# ==========================================
# 3. Process Image
# ==========================================
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ==========================================
# 4. FastApi Prediction Endpoint Logic
# ==========================================
def predict(image_path: str):
    try:
        image = Image.open(image_path).convert('RGB')
        input_tensor = transform(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probs = torch.sigmoid(outputs).cpu().numpy()[0]
            
        max_prob = float(np.max(probs))
        max_index = int(np.argmax(probs))
        
        if max_prob < 0.5:
            return "Normal / No Finding", round((1.0 - max_prob) * 100, 2)
            
        predicted_disease = LABELS[max_index]
        return predicted_disease, round(max_prob * 100, 2)
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        return "Processing Error", 0.0
