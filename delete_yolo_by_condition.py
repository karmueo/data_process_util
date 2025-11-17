#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除YOLO格式标注和对应图片的工具
根据指定条件（如标注条数）删除标注文件和对应的图片文件，或按文件名后缀仅保留特定样本，删除其余样本。

使用方法:
    1) 基本参数
         --root_dir         YOLO数据集根目录（必须包含 images/ 与 labels/ 子目录）
         --condition        删除条件，支持多次传入，格式为: count<op><value>
                                                <op> ∈ { >, <, >=, <=, ==, != }，表达标注行数的比较
         --keep_suffix      仅保留文件名（不含扩展名）以该后缀结尾的样本；会删除其他样本
         --dry_run          试运行，不实际删除，仅打印将要删除的文件
         --backup_dir       备份目录。若提供，则把将删除的文件移动到该目录下的 images/ 与 labels/

    2) 目录结构要求
         <root_dir>/
             ├── images/
             │     ├── xxx.jpg|png|bmp...
             └── labels/
                         ├── xxx.txt

    3) 示例
         - 删除标注条数大于 1 的样本:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1"

         - 删除空标注（标注条数等于 0）的样本:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count==0"

         - 删除标注条数在 [2,5] 范围内的样本（多条件 AND 关系）:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>=2" --condition "count<=5"

         - 仅保留文件名以 _center 结尾的样本（删除其他图片及对应标注）:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --keep_suffix _center

         - 组合使用（删除“标注>1 且 文件名不以 _center 结尾”的样本）:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1" --keep_suffix _center

         - 试运行模式:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1" --dry_run

         - 备份模式（移动到备份目录而非直接删除）:
             python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1" --backup_dir /path/to/backup

注意:
    - 遍历以 labels/*.txt 为主，删除时会同步处理对应 images 下同名图片（支持扩展名: jpg/jpeg/png/bmp 及大小写变体）。
    - 提供 --keep_suffix 时，会删除“不以该后缀结尾”的样本（即仅保留匹配的样本）。可与 --condition 叠加（AND 关系）。
"""

import os
import argparse
from pathlib import Path
from typing import Callable, List, Tuple, Optional
import shutil


def count_annotations(label_file: str) -> int:
    """
    统计标注文件中的标注条数
    
    Args:
        label_file: 标注文件路径
        
    Returns:
        标注条数
    """
    if not os.path.exists(label_file):
        return 0
    
    with open(label_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return len(lines)


def get_image_extensions() -> List[str]:
    """获取支持的图片扩展名"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.JPG', '.JPEG', '.PNG', '.BMP']


def find_corresponding_image(label_path: str, images_dir: str) -> Optional[str]:
    """
    查找标注文件对应的图片文件
    
    Args:
        label_path: 标注文件路径
        images_dir: 图片目录
        
    Returns:
        对应的图片文件路径，如果不存在则返回None
    """
    label_name = Path(label_path).stem
    
    # 尝试不同的图片扩展名
    for ext in get_image_extensions():
        image_path = os.path.join(images_dir, label_name + ext)
        if os.path.exists(image_path):
            return image_path
    
    return None


def delete_files(root_dir: str, condition: Callable[[str], bool], 
                 dry_run: bool = False, backup_dir: Optional[str] = None) -> Tuple[int, int]:
    """
    删除满足条件的标注文件和对应的图片文件
    
    Args:
        root_dir: YOLO数据集根目录（包含images和labels文件夹）
        condition: 判断条件函数，输入标注文件路径，返回True表示需要删除
        dry_run: 是否为试运行模式，只打印不实际删除
        backup_dir: 备份目录，如果指定则移动文件到备份目录而不是删除
        
    Returns:
        (删除的标注文件数, 删除的图片文件数)
    """
    root_path = Path(root_dir)
    labels_dir = root_path / 'labels'
    images_dir = root_path / 'images'
    
    if not labels_dir.exists():
        raise ValueError(f"标注目录不存在: {labels_dir}")
    if not images_dir.exists():
        raise ValueError(f"图片目录不存在: {images_dir}")
    
    # 如果需要备份，创建备份目录
    if backup_dir and not dry_run:
        backup_path = Path(backup_dir)
        backup_labels_dir = backup_path / 'labels'
        backup_images_dir = backup_path / 'images'
        backup_labels_dir.mkdir(parents=True, exist_ok=True)
        backup_images_dir.mkdir(parents=True, exist_ok=True)
    else:
        backup_labels_dir = None
        backup_images_dir = None
    
    deleted_labels = 0
    deleted_images = 0
    
    # 遍历所有标注文件
    for label_file in labels_dir.glob('*.txt'):
        label_path = str(label_file)
        
        # 检查是否满足删除条件
        if condition(label_path):
            # 查找对应的图片文件
            image_path = find_corresponding_image(label_path, str(images_dir))
            
            if dry_run:
                print(f"[试运行] 将删除标注: {label_file.name}")
                if image_path:
                    print(f"[试运行] 将删除图片: {Path(image_path).name}")
                else:
                    print("[试运行] 未找到对应图片")
            else:
                # 实际删除或移动文件
                if backup_dir and backup_labels_dir and backup_images_dir:
                    # 移动到备份目录
                    shutil.move(label_path, str(backup_labels_dir / label_file.name))
                    print(f"已备份标注: {label_file.name}")
                    if image_path:
                        shutil.move(image_path, str(backup_images_dir / Path(image_path).name))
                        print(f"已备份图片: {Path(image_path).name}")
                else:
                    # 直接删除
                    os.remove(label_path)
                    print(f"已删除标注: {label_file.name}")
                    if image_path:
                        os.remove(image_path)
                        print(f"已删除图片: {Path(image_path).name}")
            
            deleted_labels += 1
            if image_path:
                deleted_images += 1
    
    return deleted_labels, deleted_images


def main():
    parser = argparse.ArgumentParser(
        description='根据指定条件删除YOLO格式标注和对应图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 删除标注条数大于1的文件
  python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1"
  
  # 删除标注条数等于0的文件（空标注）
  python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count==0"
  
  # 删除标注条数小于3的文件
  python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count<3"
  
  # 删除标注条数在指定范围内的文件
  python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>=2" --condition "count<=5"
  
  # 试运行模式（不实际删除，只显示将要删除的文件）
  python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1" --dry_run
  
  # 备份模式（移动到备份目录而不是删除）
  python delete_yolo_by_condition.py --root_dir /path/to/dataset --condition "count>1" --backup_dir /path/to/backup
  
    # 仅保留文件名以 _center 结尾的图片（删除其他图片及其标注）
    python delete_yolo_by_condition.py --root_dir /path/to/dataset --keep_suffix _center
        """)
    
    parser.add_argument('--root_dir', type=str, required=True,
                        help='YOLO数据集根目录（包含images和labels文件夹）')
    parser.add_argument('--condition', type=str, action='append', required=False,
                        help='删除条件，格式: count<op><value>，op可以是 >, <, >=, <=, ==, !=')
    parser.add_argument('--dry_run', action='store_true',
                        help='试运行模式，只显示将要删除的文件，不实际删除')
    parser.add_argument('--backup_dir', type=str, default=None,
                        help='备份目录，如果指定则移动文件到此目录而不是删除')
    parser.add_argument('--keep_suffix', type=str, default=None,
                        help='仅保留文件名（不含扩展名）以该后缀结尾的样本，删除其他图片及对应标注，例如: _center')
    
    args = parser.parse_args()
    
    # 解析条件
    def parse_condition(condition_str: str) -> Callable[[int], bool]:
        """解析条件字符串为判断函数"""
        condition_str = condition_str.strip()
        
        if not condition_str.startswith('count'):
            raise ValueError(f"条件必须以 'count' 开头: {condition_str}")
        
        condition_str = condition_str[5:].strip()  # 移除 'count'
        
        # 解析操作符和值
        ops = ['>=', '<=', '==', '!=', '>', '<']
        for op in ops:
            if op in condition_str:
                try:
                    value = int(condition_str.split(op)[1].strip())
                except (ValueError, IndexError):
                    raise ValueError(f"无法解析条件值: {condition_str}")
                
                if op == '>':
                    return lambda count: count > value
                elif op == '<':
                    return lambda count: count < value
                elif op == '>=':
                    return lambda count: count >= value
                elif op == '<=':
                    return lambda count: count <= value
                elif op == '==':
                    return lambda count: count == value
                elif op == '!=':
                    return lambda count: count != value
        
        raise ValueError(f"无法解析条件: {condition_str}")
    
    # 创建综合条件判断函数
    condition_funcs = [parse_condition(cond) for cond in args.condition] if args.condition else []
    keep_suffix = args.keep_suffix
    
    def combined_condition(label_path: str) -> bool:
        """综合判断所有条件（AND关系），并按keep_suffix过滤"""
        count = count_annotations(label_path)
        meets_count = all(func(count) for func in condition_funcs) if condition_funcs else True
        if keep_suffix:
            name_ok = not Path(label_path).stem.endswith(keep_suffix)
        else:
            name_ok = True
        return meets_count and name_ok
    
    # 执行删除
    print(f"数据集根目录: {args.root_dir}")
    cond_desc = ' AND '.join(args.condition) if args.condition else '(无)'
    print(f"删除条件: {cond_desc}")
    if args.dry_run:
        print("模式: 试运行（不会实际删除文件）")
    elif args.backup_dir:
        print(f"模式: 备份到 {args.backup_dir}")
    else:
        print("模式: 直接删除")
    print("-" * 60)
    
    try:
        deleted_labels, deleted_images = delete_files(
            args.root_dir, 
            combined_condition, 
            args.dry_run,
            args.backup_dir
        )
        
        print("-" * 60)
        print(f"完成! 删除了 {deleted_labels} 个标注文件和 {deleted_images} 个图片文件")
        
    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())