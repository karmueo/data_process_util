import os
import shutil
import random
import argparse
from tqdm import tqdm


def validate_arguments(root_dir, split_ratio):
    """验证输入参数有效性"""
    if not os.path.isdir(root_dir):
        raise ValueError(f"根目录不存在: {root_dir}")
    if not (0 < split_ratio < 1):
        raise ValueError("分割比例必须在0到1之间")


def get_category_dirs(root_dir):
    """获取所有类别子目录"""
    return [d for d in os.listdir(root_dir)
            if os.path.isdir(os.path.join(root_dir, d))]


def split_category_files(category_dir, split_ratio, seed):
    """分割单个类别的文件"""
    # 获取所有图片文件
    image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    all_files = [f for f in os.listdir(category_dir)
                 if os.path.splitext(f)[1].lower() in image_exts]

    # 打乱并分割
    random.seed(seed)
    random.shuffle(all_files)
    split_idx = int(len(all_files) * split_ratio)

    return all_files[:split_idx], all_files[split_idx:]


def create_directory_structure(base_path, categories):
    """创建目标目录结构"""
    for split in ['train', 'val']:
        for category in categories:
            os.makedirs(os.path.join(
                base_path, split, category), exist_ok=True)


def copy_split_files(src_root, dest_root, category, files, split_name):
    """复制分割后的文件"""
    for filename in tqdm(files, desc=f'{category} {split_name}', unit='file'):
        src_path = os.path.join(src_root, category, filename)
        dest_path = os.path.join(dest_root, split_name, category, filename)
        shutil.copy2(src_path, dest_path)


def main():
    parser = argparse.ArgumentParser(description='数据集分割工具')
    parser.add_argument('--root_dir',
                        type=str,
                        default='drone+bird_3.20/yolo/all/cropped_objects',
                        help='包含数字类别子目录的根目录')
    parser.add_argument('--split_ratio',
                        type=float,
                        default=0.95,
                        help='训练集比例 (0-1)，如0.8表示80%训练，20%验证')
    parser.add_argument('--output',
                        default='drone+bird_3.20/yolo/all/split_dataset',
                        help='输出目录路径，默认: split_dataset')
    parser.add_argument('--seed',
                        type=int,
                        default=41,
                        help='随机种子，默认')
    args = parser.parse_args()

    try:
        # 参数校验
        validate_arguments(args.root_dir, args.split_ratio)

        # 获取类别目录
        categories = get_category_dirs(args.root_dir)
        if not categories:
            raise ValueError("根目录下未找到数字命名的类别子目录")

        # 创建输出目录结构
        create_directory_structure(args.output, categories)

        # 处理每个类别
        stats = {'train': 0, 'val': 0}
        for category in categories:
            category_path = os.path.join(args.root_dir, category)
            train_files, val_files = split_category_files(
                category_path, args.split_ratio, args.seed
            )

            # 复制训练集
            copy_split_files(args.root_dir, args.output, category,
                             train_files, 'train')
            # 复制验证集
            copy_split_files(args.root_dir, args.output, category,
                             val_files, 'val')

            stats['train'] += len(train_files)
            stats['val'] += len(val_files)

        # 输出统计信息
        print(f"\n完成！数据集已分割到: {os.path.abspath(args.output)}")
        print(f"总图片数: {stats['train'] + stats['val']}")
        print(f"训练集 ({args.split_ratio*100:.1f}%): {stats['train']}")
        print(f"验证集 ({(1-args.split_ratio)*100:.1f}%): {stats['val']}")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()
