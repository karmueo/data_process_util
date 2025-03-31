import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from efficientnet_pytorch import EfficientNet
from PIL import Image


class CustomDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.image_paths = []
        self.labels = []
        self.classes = os.listdir(root_dir)
        self.class_to_idx = {cls_name: i for i,
                             cls_name in enumerate(self.classes)}
        for cls_name in self.classes:
            cls_dir = os.path.join(root_dir, cls_name)
            for img_name in os.listdir(cls_dir):
                self.image_paths.append(os.path.join(cls_dir, img_name))
                self.labels.append(self.class_to_idx[cls_name])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert('RGB')
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        return image, label


def test(root_dir,
         pretrained_model="efficientnet-b4",
         model_path="efficientnet_110.pth",
         batch_size=1,
         num_workers=1):
    data_transforms = {
        'test': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    test_dataset = CustomDataset(
        root_dir=os.path.join(root_dir, "test"),
        transform=data_transforms['test'])

    test_loader = DataLoader(test_dataset, batch_size=batch_size,
                             shuffle=False, num_workers=num_workers)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    num_classes = len(test_dataset.classes)

    model = EfficientNet.from_pretrained(pretrained_model,
                                         num_classes=num_classes)
    model.load_state_dict(torch.load(model_path))

    model = model.to(device)

    # 验证阶段
    model.eval()
    running_corrects = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            prob = torch.softmax(outputs, dim=1)
            _, preds = torch.max(prob, 1)
            running_corrects += torch.sum(preds == labels.data)

    epoch_acc = running_corrects.double() / len(test_loader.dataset)
    print(
        f'Accuracy: {epoch_acc:.4f}')

    # 保存模型
    torch.save(model.state_dict(), 'efficientnet_110.pth')


if __name__ == '__main__':
    test(root_dir="classify")
