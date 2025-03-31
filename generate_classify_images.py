import os
import cv2
import uuid
from pathlib import Path


def crop_and_save_objects(root_dir, padding=0.0):
    """
    从YOLO标注文件中读取目标坐标，截取图片中的物体，按类别保存到不同文件夹（支持边界扩展）

    参数:
        root_dir (str): 根目录路径，包含images和labels子目录
        padding (float): 目标框扩展比例（例如0.1表示上下左右各扩展目标尺寸的10%）
    """
    # 定义路径
    images_dir = os.path.join(root_dir, 'images')
    labels_dir = os.path.join(root_dir, 'labels')
    output_dir = os.path.join(root_dir, 'cropped_objects')

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 遍历所有图片文件
    for img_file in os.listdir(images_dir):
        if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            # 构造对应标签文件路径
            base_name = os.path.splitext(img_file)[0]
            label_file = os.path.join(labels_dir, f"{base_name}.txt")

            if not os.path.exists(label_file):
                continue  # 跳过没有对应标签的图片

            # 读取图片
            img_path = os.path.join(images_dir, img_file)
            image = cv2.imread(img_path)
            if image is None:
                print(f"警告：无法读取图片 {img_path}")
                continue

            # 获取图片尺寸
            img_h, img_w = image.shape[:2]

            # 读取标签文件
            with open(label_file, 'r') as f:
                lines = f.readlines()

            # 处理每个目标
            for idx, line in enumerate(lines):
                parts = line.strip().split()
                if len(parts) != 5:
                    continue  # 跳过格式错误的行

                # 解析YOLO格式数据
                class_id = parts[0]
                x_center = float(parts[1]) * img_w
                y_center = float(parts[2]) * img_h
                width = float(parts[3]) * img_w
                height = float(parts[4]) * img_h

                # 计算原始边界框坐标
                x1 = int(x_center - width/2)
                y1 = int(y_center - height/2)
                x2 = int(x_center + width/2)
                y2 = int(y_center + height/2)

                # 计算扩展量（基于原始目标尺寸）
                pad_w = int(width * padding)
                pad_h = int(height * padding)

                # 应用padding扩展
                x1 = max(0, x1 - pad_w)          # 左边界扩展
                x2 = min(img_w, x2 + pad_w)       # 右边界扩展
                y1 = max(0, y1 - pad_h)          # 上边界扩展
                y2 = min(img_h, y2 + pad_h)      # 下边界扩展

                # 截取目标区域
                cropped = image[y1:y2, x1:x2]
                if cropped.size == 0:
                    continue  # 跳过无效区域

                # 创建类别目录
                class_dir = os.path.join(output_dir, str(class_id))
                Path(class_dir).mkdir(parents=True, exist_ok=True)

                # 生成唯一文件名
                unique_name = f"{uuid.uuid4().hex}.jpg"
                save_path = os.path.join(class_dir, unique_name)

                # 保存截取图片
                cv2.imwrite(save_path, cropped)
                print(f"已保存: {save_path}")


if __name__ == "__main__":
    # 使用示例（带10%的边界扩展）
    root_directory = "drone+bird_3.20/yolo/all"
    crop_and_save_objects(root_directory, padding=0.2)  # 设置padding比例
