import torch
from efficientnet_pytorch import EfficientNet


class EfficientNetWithSoftmax(torch.nn.Module):
    """在原始模型输出后添加Softmax层"""

    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model

    def forward(self, x):
        # 原始输出 [batch, num_classes]
        logits = self.base_model(x)
        # 添加Softmax (dim=1对应类别维度)
        return torch.softmax(logits, dim=1)


# --- 配置参数 ---
MODEL_NAME = 'efficientnet-b4'
NUM_CLASSES = 2
INPUT_SIZE = 224
ONNX_PATH = 'efficientnet_110_with_softmax.onnx'

# --- 加载训练好的模型 ---
model = EfficientNet.from_pretrained(MODEL_NAME, num_classes=NUM_CLASSES)
model.load_state_dict(torch.load('efficientnet_110.pth'))
model.eval()  # 必须设置为评估模式

# --- 封装带Softmax的模型 ---
model_with_softmax = EfficientNetWithSoftmax(model)
model_with_softmax.eval()

# --- 关闭内存优化的Swish ---
model_with_softmax.base_model.set_swish(memory_efficient=False)

# --- 生成虚拟输入 ---
dummy_input = torch.randn(1, 3, INPUT_SIZE, INPUT_SIZE)

# --- 导出ONNX ---
torch.onnx.export(
    model_with_softmax,
    dummy_input,
    ONNX_PATH,
    input_names=['input'],
    output_names=['probabilities'],  # 输出名称改为probabilities
    dynamic_axes={
        'input': {0: 'batch_size'},
        'probabilities': {0: 'batch_size'}
    },
    opset_version=12,
    do_constant_folding=True  # 启用常量折叠优化
)

# --- 验证输出 ---
with torch.no_grad():
    output = model_with_softmax(dummy_input)
    print("输出验证：")
    print(f"总和: {output.sum().item():.4f} (应接近1.0)")
    print(f"最大概率: {output.max().item():.4f}")
