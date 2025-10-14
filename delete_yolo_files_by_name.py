"""
从YOLO标注根目录中删除指定文件名的图片和标注

功能：
1. 从源YOLO目录提取包含标注的文件名列表
2. 在目标YOLO目录中删除这些文件名对应的图片和标注

使用示例：
python delete_yolo_files_by_name.py --source_dir /path/to/source_yolo --target_dir /path/to/target_yolo
"""

import os
import argparse
from typing import Set


def get_labeled_filenames(yolo_root: str) -> Set[str]:
    """
    从YOLO根目录提取包含标注的文件名列表（不含扩展名）

    Args:
        yolo_root: YOLO标注根目录，包含images和labels文件夹

    Returns:
        包含标注的文件名集合（不含扩展名）
    """
    labels_dir = os.path.join(yolo_root, "labels")

    if not os.path.exists(labels_dir):
        print(f"警告: labels目录不存在: {labels_dir}")
        return set()

    labeled_files = set()

    # 遍历labels目录，获取所有标注文件
    for root, dirs, files in os.walk(labels_dir):
        for file in files:
            if file.endswith(".txt"):
                # 获取文件名（不含扩展名）
                filename = os.path.splitext(file)[0]
                labeled_files.add(filename)

    print(f"从 {yolo_root} 中找到 {len(labeled_files)} 个标注文件")
    return labeled_files


def delete_files_from_yolo(
    yolo_root: str, filenames_to_delete: Set[str], dry_run: bool = False
) -> dict:
    """
    从YOLO根目录中删除指定文件名的图片和标注

    Args:
        yolo_root: YOLO标注根目录，包含images和labels文件夹
        filenames_to_delete: 要删除的文件名集合（不含扩展名）
        dry_run: 是否只是预览而不实际删除

    Returns:
        删除统计信息
    """
    images_dir = os.path.join(yolo_root, "images")
    labels_dir = os.path.join(yolo_root, "labels")

    stats = {
        "images_deleted": 0,
        "labels_deleted": 0,
        "images_not_found": 0,
        "labels_not_found": 0,
    }

    # 常见的图片扩展名
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"]

    # 删除图片和标注
    for filename in filenames_to_delete:
        # 查找并删除图片
        image_deleted = False
        if os.path.exists(images_dir):
            for root, dirs, files in os.walk(images_dir):
                for ext in image_extensions:
                    image_file = filename + ext
                    if image_file in files:
                        image_path = os.path.join(root, image_file)
                        if dry_run:
                            print(f"[预览] 将删除图片: {image_path}")
                        else:
                            os.remove(image_path)
                            print(f"已删除图片: {image_path}")
                        stats["images_deleted"] += 1
                        image_deleted = True
                        break
                if image_deleted:
                    break

        if not image_deleted:
            stats["images_not_found"] += 1

        # 查找并删除标注
        label_deleted = False
        if os.path.exists(labels_dir):
            for root, dirs, files in os.walk(labels_dir):
                label_file = filename + ".txt"
                if label_file in files:
                    label_path = os.path.join(root, label_file)
                    if dry_run:
                        print(f"[预览] 将删除标注: {label_path}")
                    else:
                        os.remove(label_path)
                        print(f"已删除标注: {label_path}")
                    stats["labels_deleted"] += 1
                    label_deleted = True
                    break

        if not label_deleted:
            stats["labels_not_found"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="从YOLO标注根目录中删除指定文件名的图片和标注",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 从source_dir提取文件名，然后在target_dir中删除这些文件
  python delete_yolo_files_by_name.py --source_dir /path/to/source --target_dir /path/to/target
  
  # 预览模式（不实际删除）
  python delete_yolo_files_by_name.py --source_dir /path/to/source --target_dir /path/to/target --dry_run
        """,
    )

    parser.add_argument(
        "--source_dir",
        type=str,
        required=True,
        help="源YOLO根目录（从中提取文件名列表）",
    )
    parser.add_argument(
        "--target_dir", type=str, required=True, help="目标YOLO根目录（从中删除文件）"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="预览模式，只显示将要删除的文件，不实际删除",
    )

    args = parser.parse_args()

    # 验证目录存在
    if not os.path.exists(args.source_dir):
        print(f"错误: 源目录不存在: {args.source_dir}")
        return

    if not os.path.exists(args.target_dir):
        print(f"错误: 目标目录不存在: {args.target_dir}")
        return

    print("=" * 80)
    print("YOLO文件删除工具")
    print("=" * 80)
    print(f"源目录: {args.source_dir}")
    print(f"目标目录: {args.target_dir}")
    print(f"模式: {'预览模式（不会实际删除）' if args.dry_run else '删除模式'}")
    print("=" * 80)

    # 步骤1: 从源目录提取文件名列表
    print("\n[步骤 1/2] 从源目录提取文件名列表...")
    filenames_to_delete = get_labeled_filenames(args.source_dir)

    if not filenames_to_delete:
        print("警告: 源目录中没有找到任何标注文件，无需删除")
        return

    # 步骤2: 从目标目录删除文件
    print(f"\n[步骤 2/2] 从目标目录删除 {len(filenames_to_delete)} 个文件...")

    if not args.dry_run:
        confirm = input(
            f"\n确认要从 {args.target_dir} 中删除 {len(filenames_to_delete)} 个文件吗？(yes/no): "
        )
        if confirm.lower() not in ["yes", "y"]:
            print("操作已取消")
            return

    stats = delete_files_from_yolo(args.target_dir, filenames_to_delete, args.dry_run)

    # 显示统计信息
    print("\n" + "=" * 80)
    print("删除统计:")
    print("=" * 80)
    print(f"图片已删除: {stats['images_deleted']}")
    print(f"标注已删除: {stats['labels_deleted']}")
    print(f"图片未找到: {stats['images_not_found']}")
    print(f"标注未找到: {stats['labels_not_found']}")
    print("=" * 80)

    if args.dry_run:
        print("\n提示: 这是预览模式，没有实际删除文件。")
        print("      如需真正删除，请去掉 --dry_run 参数。")
    else:
        print("\n删除完成！")


if __name__ == "__main__":
    main()
