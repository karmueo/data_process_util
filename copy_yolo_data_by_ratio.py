"""
从YOLO标注根目录中复制指定比例或数量的图片和标注到新文件夹

功能：
1. 按比例或指定数量从YOLO目录复制图片和标注
2. 保持目录结构
3. 支持随机采样或顺序采样

使用示例：
# 复制30%的数据
python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --ratio 0.3

# 复制100张图片
python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --count 100

# 顺序采样（不随机）
python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --ratio 0.3 --no_shuffle
"""

import os
import argparse
import shutil
import random
from typing import List, Tuple


def find_image_label_pairs(yolo_root: str) -> List[Tuple[str, str, str]]:
    """
    查找YOLO目录中的图片-标注对
    
    Args:
        yolo_root: YOLO根目录
        
    Returns:
        列表，每个元素为 (filename_without_ext, image_path, label_path)
        如果标注不存在，label_path为None
    """
    images_dir = os.path.join(yolo_root, 'images')
    labels_dir = os.path.join(yolo_root, 'labels')
    
    if not os.path.exists(images_dir):
        print(f"错误: images目录不存在: {images_dir}")
        return []
    
    pairs = []
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp']
    
    # 遍历images目录
    for root, dirs, files in os.walk(images_dir):
        for file in files:
            # 检查是否是图片文件
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_path = os.path.join(root, file)
                filename_without_ext = os.path.splitext(file)[0]
                
                # 构建对应的标注路径（保持相对目录结构）
                rel_path = os.path.relpath(root, images_dir)
                label_dir = os.path.join(labels_dir, rel_path)
                label_path = os.path.join(label_dir, filename_without_ext + '.txt')
                
                # 检查标注是否存在
                if os.path.exists(label_path):
                    pairs.append((filename_without_ext, image_path, label_path))
                else:
                    # 标注不存在，label_path设为None
                    pairs.append((filename_without_ext, image_path, None))
    
    return pairs


def copy_yolo_pairs(pairs: List[Tuple[str, str, str]],
                    source_root: str,
                    target_root: str,
                    copy_only_labeled: bool = False) -> dict:
    """
    复制图片-标注对到目标目录
    
    Args:
        pairs: 图片-标注对列表
        source_root: 源YOLO根目录
        target_root: 目标YOLO根目录
        copy_only_labeled: 是否只复制有标注的图片
        
    Returns:
        复制统计信息
    """
    images_src_dir = os.path.join(source_root, 'images')
    labels_src_dir = os.path.join(source_root, 'labels')
    images_dst_dir = os.path.join(target_root, 'images')
    labels_dst_dir = os.path.join(target_root, 'labels')
    
    stats = {
        'images_copied': 0,
        'labels_copied': 0,
        'images_without_labels': 0
    }
    
    for filename, image_path, label_path in pairs:
        # 如果只复制有标注的，且当前无标注，则跳过
        if copy_only_labeled and label_path is None:
            continue
        
        # 计算相对路径，保持目录结构
        image_rel_path = os.path.relpath(image_path, images_src_dir)
        image_dst_path = os.path.join(images_dst_dir, image_rel_path)
        
        # 创建目标目录
        os.makedirs(os.path.dirname(image_dst_path), exist_ok=True)
        
        # 复制图片
        shutil.copy2(image_path, image_dst_path)
        stats['images_copied'] += 1
        
        # 复制标注（如果存在）
        if label_path and os.path.exists(label_path):
            label_rel_path = os.path.relpath(label_path, labels_src_dir)
            label_dst_path = os.path.join(labels_dst_dir, label_rel_path)
            os.makedirs(os.path.dirname(label_dst_path), exist_ok=True)
            shutil.copy2(label_path, label_dst_path)
            stats['labels_copied'] += 1
        else:
            stats['images_without_labels'] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='从YOLO标注根目录中复制指定比例或数量的图片和标注到新文件夹',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 复制30%的数据（随机采样）
  python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --ratio 0.3
  
  # 复制100张图片
  python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --count 100
  
  # 顺序采样（不随机）
  python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --ratio 0.3 --no_shuffle
  
  # 只复制有标注的图片
  python copy_yolo_data_by_ratio.py --source_dir /path/to/source --target_dir /path/to/target --ratio 0.5 --only_labeled
        """
    )
    
    parser.add_argument('--source_dir', type=str, required=True,
                        help='源YOLO根目录')
    parser.add_argument('--target_dir', type=str, required=True,
                        help='目标YOLO根目录')
    
    # 互斥参数组：ratio 或 count
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ratio', type=float,
                       help='复制的比例 (0.0-1.0)，例如 0.3 表示复制30%%的数据')
    group.add_argument('--count', type=int,
                       help='复制的数量，例如 100 表示复制100张图片')
    
    parser.add_argument('--no_shuffle', action='store_true',
                        help='不随机采样，按顺序复制')
    parser.add_argument('--only_labeled', action='store_true',
                        help='只复制有标注的图片')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子，用于可重复的随机采样 (默认: 42)')
    
    args = parser.parse_args()
    
    # 验证参数
    if not os.path.exists(args.source_dir):
        print(f"错误: 源目录不存在: {args.source_dir}")
        return
    
    if args.ratio is not None and (args.ratio <= 0 or args.ratio > 1):
        print(f"错误: ratio必须在 (0, 1] 范围内")
        return
    
    if args.count is not None and args.count <= 0:
        print(f"错误: count必须大于0")
        return
    
    if os.path.exists(args.target_dir):
        print(f"警告: 目标目录已存在: {args.target_dir}")
        confirm = input("是否继续？可能会覆盖已有文件 (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("操作已取消")
            return
    
    print("=" * 80)
    print("YOLO数据复制工具")
    print("=" * 80)
    print(f"源目录: {args.source_dir}")
    print(f"目标目录: {args.target_dir}")
    if args.ratio:
        print(f"复制比例: {args.ratio * 100:.1f}%")
    else:
        print(f"复制数量: {args.count}")
    print(f"随机采样: {'否' if args.no_shuffle else '是'}")
    print(f"只复制有标注: {'是' if args.only_labeled else '否'}")
    if not args.no_shuffle:
        print(f"随机种子: {args.seed}")
    print("=" * 80)
    
    # 查找所有图片-标注对
    print("\n正在扫描源目录...")
    all_pairs = find_image_label_pairs(args.source_dir)
    
    if not all_pairs:
        print("错误: 源目录中没有找到任何图片")
        return
    
    # 统计有标注和无标注的数量
    labeled_pairs = [p for p in all_pairs if p[2] is not None]
    unlabeled_pairs = [p for p in all_pairs if p[2] is None]
    
    print(f"找到 {len(all_pairs)} 张图片")
    print(f"  - 有标注: {len(labeled_pairs)}")
    print(f"  - 无标注: {len(unlabeled_pairs)}")
    
    # 如果只复制有标注的，使用labeled_pairs
    if args.only_labeled:
        pairs_to_sample = labeled_pairs
        print(f"\n只复制有标注的图片，共 {len(pairs_to_sample)} 张")
    else:
        pairs_to_sample = all_pairs
    
    # 计算需要复制的数量
    if args.ratio:
        copy_count = int(len(pairs_to_sample) * args.ratio)
    else:
        copy_count = min(args.count, len(pairs_to_sample))
    
    if copy_count == 0:
        print("错误: 计算得到的复制数量为0")
        return
    
    print(f"\n将复制 {copy_count} 张图片")
    
    # 采样
    if args.no_shuffle:
        selected_pairs = pairs_to_sample[:copy_count]
    else:
        random.seed(args.seed)
        selected_pairs = random.sample(pairs_to_sample, copy_count)
    
    # 复制文件
    print("\n开始复制文件...")
    stats = copy_yolo_pairs(selected_pairs, args.source_dir, args.target_dir, args.only_labeled)
    
    # 显示统计信息
    print("\n" + "=" * 80)
    print("复制统计:")
    print("=" * 80)
    print(f"图片已复制: {stats['images_copied']}")
    print(f"标注已复制: {stats['labels_copied']}")
    print(f"无标注图片: {stats['images_without_labels']}")
    print("=" * 80)
    print(f"\n复制完成！数据已保存到: {args.target_dir}")


if __name__ == '__main__':
    main()
