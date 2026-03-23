import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np
import os

LABELS = [
    'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration', 'Mass', 'Nodule', 'Pneumonia',
    'Pneumothorax', 'Consolidation', 'Edema', 'Emphysema', 'Fibrosis', 'Pleural_Thickening', 'Hernia'
]

# ==========================================
# 1. Custom IEViT Architecture
# ==========================================
class PatchEmbedding(nn.Module):
    def __init__(self, img_size=224, patch_size=16, in_channels=3, embed_dim=768):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2
        self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        x = self.proj(x)
        x = x.flatten(2)
        x = x.transpose(1, 2)
        return x

class MLP(nn.Module):
    def __init__(self, in_features, hidden_features, out_features, drop=0.):
        super().__init__()
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

class Attention(nn.Module):
    def __init__(self, dim, num_heads=8, qkv_bias=False, attn_drop=0., proj_drop=0.):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** -0.5

        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

    def forward(self, x):
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x

class TransformerEncoderLayer(nn.Module):
    def __init__(self, dim, num_heads, mlp_ratio=4., qkv_bias=False, drop=0., attn_drop=0.):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias, attn_drop=attn_drop, proj_drop=drop)
        self.norm2 = nn.LayerNorm(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = MLP(in_features=dim, hidden_features=mlp_hidden_dim, out_features=dim, drop=drop)

    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x

class CNNBranch(nn.Module):
    def __init__(self, in_channels=3, out_channels=768):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        
        self.layer1 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(256, out_channels, kernel_size=3, stride=2, padding=1),
             nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        return x

class IEViT(nn.Module):
    def __init__(self, img_size=224, patch_size=16, in_channels=3, num_classes=14, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4., qkv_bias=True, drop_rate=0., attn_drop_rate=0.):
        super().__init__()
        
        self.patch_embed = PatchEmbedding(img_size=img_size, patch_size=patch_size, in_channels=in_channels, embed_dim=embed_dim)
        num_patches = self.patch_embed.n_patches
        
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, embed_dim))
        self.pos_drop = nn.Dropout(p=drop_rate)
        
        self.blocks = nn.ModuleList([
            TransformerEncoderLayer(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, drop=drop_rate, attn_drop=attn_drop_rate)
            for _ in range(depth)
        ])
        
        self.norm = nn.LayerNorm(embed_dim)
        self.cnn = CNNBranch(in_channels=in_channels, out_channels=embed_dim)
        self.head = nn.Linear(embed_dim * 2, num_classes) 

    def forward(self, x):
        B = x.shape[0]
        
        # ViT Path
        x_vit = self.patch_embed(x)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x_vit = torch.cat((cls_tokens, x_vit), dim=1)
        x_vit = x_vit + self.pos_embed
        x_vit = self.pos_drop(x_vit)
        
        for blk in self.blocks:
            x_vit = blk(x_vit)
            
        x_vit = self.norm(x_vit)
        cls_out = x_vit[:, 0]
        
        # CNN Path
        x_cnn = self.cnn(x)
        x_cnn = F.adaptive_avg_pool2d(x_cnn, (1, 1)).flatten(1)
        
        # Fusion & Classification
        combined_features = torch.cat((cls_out, x_cnn), dim=1)
        logits = self.head(combined_features)
        
        return logits

def ievit_base_patch16_224(pretrained=False, **kwargs):
    model = IEViT(
        img_size=224, patch_size=16, embed_dim=768, depth=12, num_heads=12, mlp_ratio=4, qkv_bias=True,
        **kwargs)
    return model

# ==========================================
# 2. Load Old Weights at Server Startup
# ==========================================
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Loading custom IEViT model on {device}...")

# MAKE SURE YOUR FILE MATCHES THIS NAME EXACTLY:
model_path = os.path.join(os.path.dirname(__file__), "old_ievit_weights.pth")
model = ievit_base_patch16_224(pretrained=False, num_classes=14)

try:
    model.load_state_dict(torch.load(model_path, map_location=device))
    print("Old IEViT weights loaded successfully! Ready for testing.")
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
            return "Normal / No Finding", round(1.0 - max_prob, 2)
            
        predicted_disease = LABELS[max_index]
        return predicted_disease, round(max_prob, 2)
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        return "Processing Error", 0.0
