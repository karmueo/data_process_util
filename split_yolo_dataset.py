import os
import random
import shutil
from pathlib import Path


def split_yolo_dataset(source_dir, target_dir, ratio=None, num_samples=None, seed=42):
    """
    从YOLO格式数据集中随机抽取图片和标注到新文件夹

    参数:
        source_dir (str): 源文件夹路径（包含images和labels子文件夹）
        target_dir (str): 目标文件夹路径
        ratio (float): 抽取比率（0-1之间）
        num_samples (int): 抽取的绝对数量
        seed (int): 随机种子（确保可重复性）
    """
    # 设置随机种子
    random.seed(seed)

    # 创建目标文件夹结构
    target_images = os.path.join(target_dir, 'images')
    target_labels = os.path.join(target_dir, 'labels')
    os.makedirs(target_images, exist_ok=True)
    os.makedirs(target_labels, exist_ok=True)

    # 获取所有图片文件名（不带后缀）
    image_files = [f.stem for f in Path(
        os.path.join(source_dir, 'images')).glob('*.jpg')]

    # 检查是否有对应的标注文件
    valid_pairs = []
    for img_stem in image_files:
        label_file = os.path.join(source_dir, 'labels', f'{img_stem}.txt')
        if os.path.exists(label_file):
            valid_pairs.append(img_stem)

    # 确定要抽取的数量
    if ratio is not None:
        num_samples = int(len(valid_pairs) * ratio)
    elif num_samples is None:
        raise ValueError("必须指定ratio或num_samples")

    # 随机抽样
    selected = random.sample(valid_pairs, min(num_samples, len(valid_pairs)))

    # 复制文件
    for img_stem in selected:
        # 复制图片
        src_img = os.path.join(source_dir, 'images', f'{img_stem}.jpg')
        dst_img = os.path.join(target_images, f'{img_stem}.jpg')
        shutil.copy2(src_img, dst_img)

        # 复制标注
        src_label = os.path.join(source_dir, 'labels', f'{img_stem}.txt')
        dst_label = os.path.join(target_labels, f'{img_stem}.txt')
        shutil.copy2(src_label, dst_label)

    print(f"成功复制 {len(selected)} 对图片和标注到 {target_dir}")


# 使用示例
if __name__ == "__main__":
    # 按比例抽取（20%）
    # split_yolo_dataset(
    #     source_dir='yolo',
    #     target_dir='yolo_sample_20percent',
    #     ratio=0.2
    # )

    # 或按绝对数量抽取（100对）
    split_yolo_dataset(
        source_dir='yolo',
        target_dir='yolo_sample_100',
        num_samples=100
    )
