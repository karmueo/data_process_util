import os
import shutil
import random
import argparse


def validate_directory_structure(root_dir):
    """检查根目录是否包含images和labels子目录"""
    required_dirs = ['images', 'labels']
    for dir_name in required_dirs:
        dir_path = os.path.join(root_dir, dir_name)
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"目录 {dir_path} 不存在")


def valid_ratio(value):
    """校验训练集比例是否合法"""
    fvalue = float(value)
    if fvalue <= 0 or fvalue >= 1:
        raise argparse.ArgumentTypeError("train_ratio 必须在0到1之间")
    return fvalue


def get_matched_files(root_dir):
    """获取所有匹配的图片和标注文件"""
    images_dir = os.path.join(root_dir, 'images')
    labels_dir = os.path.join(root_dir, 'labels')
    image_files = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

    for filename in os.listdir(images_dir):
        file_path = os.path.join(images_dir, filename)
        if os.path.isfile(file_path):
            # 检查文件扩展名
            ext = os.path.splitext(filename)[1].lower()
            if ext not in image_extensions:
                continue
            # 提取基础文件名
            base_name = os.path.splitext(filename)[0]
            # 检查标注文件是否存在
            label_filename = f"{base_name}.txt"
            label_path = os.path.join(labels_dir, label_filename)
            if os.path.isfile(label_path):
                image_files.append((filename, base_name))
            else:
                print(f"警告：跳过无标注的图片 {filename}")
    return image_files


def split_files(file_list, train_ratio):
    """随机分割文件列表为训练集和验证集"""
    random.shuffle(file_list)
    split_idx = int(len(file_list) * train_ratio)
    return file_list[:split_idx], file_list[split_idx:]


def create_dirs(target_dir):
    """创建目标目录结构"""
    dirs = ['train/images', 'train/labels', 'val/images', 'val/labels']
    for d in dirs:
        os.makedirs(os.path.join(target_dir, d), exist_ok=True)


def copy_dataset_files(root_dir, target_dir, files, mode):
    """复制文件到目标目录"""
    src_img_dir = os.path.join(root_dir, 'images')
    src_lbl_dir = os.path.join(root_dir, 'labels')
    dst_img_dir = os.path.join(target_dir, mode, 'images')
    dst_lbl_dir = os.path.join(target_dir, mode, 'labels')

    for img_filename, base_name in files:
        # 复制图片
        shutil.copy2(
            os.path.join(src_img_dir, img_filename),
            os.path.join(dst_img_dir, img_filename)
        )
        # 复制标签
        lbl_filename = f"{base_name}.txt"
        shutil.copy2(
            os.path.join(src_lbl_dir, lbl_filename),
            os.path.join(dst_lbl_dir, lbl_filename)
        )


def main():
    parser = argparse.ArgumentParser(description="数据集划分工具")
    parser.add_argument('--root_dir',
                        default="yolo/all/",
                        help='包含images/labels的根目录')
    parser.add_argument('--train_ratio',
                        type=valid_ratio,
                        default=0.9,
                        help='训练集比例 (0-1)')
    parser.add_argument('--output_dir',
                        default='yolo/train_val/',
                        help='输出目录路径')
    parser.add_argument('--seed', type=int, default=53, help='随机种子')
    args = parser.parse_args()

    # 初始化随机种子
    random.seed(args.seed)

    try:
        # 校验目录结构
        validate_directory_structure(args.root_dir)

        # 获取有效文件列表
        matched_files = get_matched_files(args.root_dir)
        if not matched_files:
            raise ValueError("未找到有效的图片-标注文件对")

        # 分割数据集
        train_files, val_files = split_files(matched_files, args.train_ratio)
        print(f"找到 {len(matched_files)} 对有效文件")
        print(f"训练集: {len(train_files)} 验证集: {len(val_files)}")

        # 创建目录结构
        create_dirs(args.output_dir)

        # 复制文件
        copy_dataset_files(args.root_dir, args.output_dir,
                           train_files, 'train')
        copy_dataset_files(args.root_dir, args.output_dir, val_files, 'val')

        print(f"\n数据集已成功划分到: {os.path.abspath(args.output_dir)}")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()
