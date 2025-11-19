#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 YOLO 空标注文件脚本

功能:
- 遍历指定图片文件夹，针对每个图片在同级的 `labels/` 文件夹下生成同名的 `.txt` 空文件 (YOLO 标签格式)。
- 支持递归遍历（保持目录结构），支持试运行 (dry-run) 和覆盖选项。

示例:
    # 默认：在 /path/to/backgrounds 同级创建 labels/，仅处理 images 下第一层文件
    python generate_empty_yolo_labels.py /path/to/backgrounds

    # 递归处理子目录并保留目录结构
    python generate_empty_yolo_labels.py /path/to/backgrounds --recursive

    # 指定 labels 的目标目录（相对或绝对）
    python generate_empty_yolo_labels.py /path/to/backgrounds --label_dir /path/to/labels

    # 试运行，只显示将创建哪些文件
    python generate_empty_yolo_labels.py /path/to/backgrounds --dry_run

    # 强制覆盖已存在的 label 文件（将会清空文件）
    python generate_empty_yolo_labels.py /path/to/backgrounds --overwrite

    # 常见图片扩展名可通过 --exts 指定
    python generate_empty_yolo_labels.py /path/to/backgrounds --exts .jpg .png .jpeg

注意:
- 若以递归方式遍历，脚本会在 labels 目标目录中创建对应的子目录结构以保持一一映射（例如: images/sub/img1.jpg -> labels/sub/img1.txt）。
- 默认情况下，若标签文件已存在脚本不会覆盖，除非使用 --overwrite 参数。

"""

from pathlib import Path
import argparse
import sys
import os


def parse_args():
    parser = argparse.ArgumentParser(
        description='生成 YOLO 空标注文件 (labels/*.txt)')
    parser.add_argument('images_dir', metavar='IMAGES_DIR', type=str,
                        help='要遍历的图片文件夹路径')
    parser.add_argument('--label_dir', type=str, default=None,
                        help='labels 目录（默认: images_dir 的同级 labels/）')
    parser.add_argument('--recursive', action='store_true',
                        help='递归遍历 images_dir，保持子目录结构')
    parser.add_argument('--exts', nargs='+', default=['.jpg', '.jpeg', '.png', '.bmp'],
                        help='图片扩展名列表（可多值），默认: .jpg .jpeg .png .bmp')
    parser.add_argument('--dry_run', action='store_true', help='试运行，仅显示将创建的文件，不实际创建')
    parser.add_argument('--overwrite', action='store_true', help='覆盖已存在的 label 文件（将被清空）')
    parser.add_argument('--verbose', action='store_true', help='详细打印处理信息')
    return parser.parse_args()


def is_image_file(path: Path, exts):
    return path.is_file() and path.suffix.lower() in exts


def find_images(images_dir: Path, recursive: bool, exts):
    if recursive:
        return [p for p in images_dir.rglob('*') if is_image_file(p, exts)]
    else:
        return [p for p in images_dir.iterdir() if is_image_file(p, exts)]


def main():
    args = parse_args()
    images_dir = Path(args.images_dir).expanduser().resolve()
    if not images_dir.exists() or not images_dir.is_dir():
        print(f"错误: 指定的图片目录不存在或不是文件夹: {images_dir}")
        sys.exit(2)

    # 选择 labels 目录（默认: images_dir.parent / 'labels'）
    if args.label_dir:
        labels_root = Path(args.label_dir).expanduser().resolve()
    else:
        labels_root = images_dir.parent / 'labels'

    # 如果 labels_root 在 images_dir 的内部，我们仍然支持，但会警告
    try:
        # 如果 labels_root 是 images_dir 的子目录，打印警告（避免递归时相互影响）
        labels_root.relative_to(images_dir)
        print(f"警告: labels 目录似乎在 images 目录内部 ({labels_root}). 这可能造成递归影响。")
    except ValueError:
        pass

    exts = set([e.lower() if e.startswith('.') else '.' + e.lower() for e in args.exts])

    images = find_images(images_dir, args.recursive, exts)
    if not images:
        print(f"未找到任何满足扩展名 {sorted(exts)} 的图片 (目录: {images_dir})")
        sys.exit(0)

    to_create = []

    for img in images:
        # compute relative path to preserve structure if recursive
        try:
            rel = img.relative_to(images_dir)
        except Exception:
            # fallback: use only filename
            rel = img.name
        # determine label path
        label_rel = Path(rel).with_suffix('.txt')
        label_path = labels_root / label_rel
        to_create.append((img, label_path))

    created = 0
    skipped = 0
    overwritten = 0

    for img_path, lbl_path in to_create:
        if not args.dry_run:
            # ensure parent dir exists
            lbl_parent = lbl_path.parent
            if not lbl_parent.exists():
                os.makedirs(lbl_parent, exist_ok=True)

        if lbl_path.exists():
            if args.overwrite:
                if args.dry_run:
                    print(f"[DRY] 覆盖: {lbl_path}")
                else:
                    # truncate file to 0 bytes
                    open(lbl_path, 'w').close()
                    overwritten += 1
                    if args.verbose:
                        print(f"覆盖: {lbl_path}")
            else:
                skipped += 1
                if args.verbose or args.dry_run:
                    print(f"跳过 (已存在): {lbl_path}")
        else:
            if args.dry_run:
                print(f"[DRY] 创建: {lbl_path}")
            else:
                open(lbl_path, 'w').close()
                created += 1
                if args.verbose:
                    print(f"创建: {lbl_path}")

    print("-" * 60)
    if args.dry_run:
        print("试运行模式：没有修改文件系统")
    print(f"总图片: {len(images)}")
    print(f"创建的 label 文件: {created}")
    print(f"覆盖的 label 文件: {overwritten}")
    print(f"跳过的（已存在）: {skipped}")
    print(f"labels 根目录: {labels_root}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
