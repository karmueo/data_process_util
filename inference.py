from PIL import Image

import torch
from torchvision import transforms

from efficientnet_pytorch import EfficientNet

idx_to_class = {1: "bird",
                0: "drone"}

NUM_CLASSES = 2


model_name = 'efficientnet-b4'
image_size = 224  # 224
# Open image
img = Image.open(
    'drone_test.jpg')

# Preprocess image
tfms = transforms.Compose([transforms.Resize((image_size, image_size)),
                           transforms.ToTensor()])
img = tfms(img).unsqueeze(0)

# --- 加载训练好的模型 ---
model = EfficientNet.from_pretrained(model_name, num_classes=NUM_CLASSES)
model.load_state_dict(torch.load('efficientnet_110.pth'))
model.eval()  # 必须设置为评估模式

with torch.no_grad():
    logits = model(img)
preds = torch.topk(logits, k=2).indices.squeeze(0).tolist()

print('-----')
for idx in preds:
    label = idx_to_class[idx]
    prob = torch.softmax(logits, dim=1)[0, idx].item()
    print('{:<75} ({:.2f}%)'.format(label, prob*100))
