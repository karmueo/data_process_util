"""
清理经过split_images_yolo.py处理的YOLO数据集
去掉所有的原始图片和标注，只留下切分后的四个子图及其标注
或者删除切分后的子图，只留下原始图片和标注
支持预览模式和删除模式
"""

import argparse
import shutil
from pathlib import Path
from typing import Set, Tuple, List, Optional


class SplitYOLOCleaner:
    """split_images_yolo.py处理结果的清理器"""

    SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    SPLIT_SUFFIXES = {
        "_top_left",
        "_top_right",
        "_bottom_left",
        "_bottom_right",
        "_tl",
        "_tr",
        "_bl",
        "_br",
        "_center",
    }

    def __init__(self, root_dir: str, dry_run: bool = True, backup_dir: Optional[str] = None, keep_original: bool = False):
        """
        初始化清理器

        Args:
            root_dir: YOLO数据集根目录（包含images和labels文件夹）
            dry_run: 如果为True，只显示要删除的文件不实际删除
            backup_dir: 备份目录，如果指定则移动文件到此目录，而不是删除
            keep_original: 如果为True，删除切分后的子图，只保留原始图片和标注
        """
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.backup_dir = Path(backup_dir) if backup_dir else None
        self.keep_original = keep_original
        self.images_dir = self.root_dir / "images"
        self.labels_dir = self.root_dir / "labels"

        # 统计信息
        self.files_to_delete = []

    def validate_inputs(self) -> bool:
        """验证输入参数"""
        if not self.root_dir.exists():
            print(f"错误：根目录不存在: {self.root_dir}")
            return False

        if not self.images_dir.exists():
            print(f"错误：images目录不存在: {self.images_dir}")
            return False

        if not self.labels_dir.exists():
            print(f"错误：labels目录不存在: {self.labels_dir}")
            return False

        return True

    def identify_split_images(self) -> Set[str]:
        """
        识别所有的切分后的子图（由split_images_yolo.py生成）

        Returns:
            切分后的子图名称集合（不含扩展名）
        """
        split_images = set()

        for image_file in self.images_dir.iterdir():
            if image_file.suffix.lower() not in self.SUPPORTED_IMAGE_EXTS:
                continue

            # 检查文件名是否以_top_left/_top_right/_bottom_left/_bottom_right结尾
            stem = image_file.stem
            for suffix in self.SPLIT_SUFFIXES:
                if stem.endswith(suffix):
                    split_images.add(image_file.name)
                    break

        return split_images

    def find_files_to_delete(self, split_images: Set[str]) -> List[Path]:
        """
        根据模式识别要删除的文件

        Args:
            split_images: 切分后的子图名称集合

        Returns:
            要删除的文件列表
        """
        files_to_delete = []

        if self.keep_original:
            # 删除切分后的子图及其标注
            for split_image in split_images:
                image_path = self.images_dir / split_image
                if image_path.exists():
                    files_to_delete.append(image_path)

                # 对应的标注文件
                stem = Path(split_image).stem
                label_path = self.labels_dir / f"{stem}.txt"
                if label_path.exists():
                    files_to_delete.append(label_path)
        else:
            # 删除原始图片和标注（原有逻辑）
            original_images, original_labels = self.find_original_files(split_images)
            files_to_delete.extend(original_images)
            files_to_delete.extend(original_labels)

        return files_to_delete

    def find_original_files(self, split_images: Set[str]) -> Tuple[List[Path], List[Path]]:
        """
        识别要删除的原始图片和标注（原有逻辑）

        Args:
            split_images: 切分后的子图名称集合

        Returns:
            (原始图片列表, 原始标注列表)
        """
        original_images = []
        original_labels = []

        # 获取所有图片文件名（不含扩展名）
        all_image_stems = set()
        for image_file in self.images_dir.iterdir():
            if image_file.suffix.lower() in self.SUPPORTED_IMAGE_EXTS:
                all_image_stems.add(image_file.stem)

        # 获取所有切分后子图的原始名称（不含_suffix）
        split_image_originals = set()
        for split_image in split_images:
            stem = Path(split_image).stem
            # 移除_top_left/_top_right/_bottom_left/_bottom_right后缀
            for suffix in self.SPLIT_SUFFIXES:
                if stem.endswith(suffix):
                    original_stem = stem[: -len(suffix)]
                    split_image_originals.add(original_stem)
                    break

        # 找出原始图片（存在于all_image_stems但对应的切分图片存在于split_images）
        for stem in split_image_originals:
            if stem in all_image_stems:
                # 找到对应的完整文件路径
                for image_file in self.images_dir.iterdir():
                    if image_file.stem == stem and image_file.suffix.lower() in self.SUPPORTED_IMAGE_EXTS:
                        original_images.append(image_file)
                        break

        # 找出原始标注
        for image_path in original_images:
            label_path = self.labels_dir / f"{image_path.stem}.txt"
            if label_path.exists():
                original_labels.append(label_path)

        return original_images, original_labels

    def preview(self):
        """预览要删除或移动的文件"""
        print("=" * 70)
        if self.keep_original:
            action_desc = "预览要删除的切分后子图"
        else:
            action_desc = "预览要删除的原始图片和标注"
        if self.backup_dir:
            print(f"{action_desc}（将移动到 {self.backup_dir}）")
        else:
            print(f"{action_desc}（将删除）")
        print("=" * 70)

        # 识别切分后的子图
        split_images = self.identify_split_images()

        if not split_images:
            print("未找到任何切分后的子图")
            print("请确保已经运行过split_images_yolo.py")
            return

        print(f"找到 {len(split_images)} 个切分后的子图")

        # 找出要删除的文件
        self.files_to_delete = self.find_files_to_delete(split_images)

        if not self.files_to_delete:
            if self.keep_original:
                print("\n未找到要删除的切分后子图")
                print("所有切分后子图可能已经被清理过了")
            else:
                print("\n未找到要删除的原始图片和标注")
                print("所有文件可能已经被清理过了")
            return

        print("\n" + "=" * 70)
        print(f"要处理的文件 ({len(self.files_to_delete)} 个):")
        print("=" * 70)
        for file_path in sorted(self.files_to_delete):
            size_kb = file_path.stat().st_size / 1024
            print(f"  {file_path.name:<50} ({size_kb:>8.2f} KB)")

        total_size = sum(p.stat().st_size for p in self.files_to_delete) / (1024 * 1024)

        print("\n" + "=" * 70)
        action = "移动" if self.backup_dir else "删除"
        print(f"总计将{action}: {len(self.files_to_delete)} 个文件")
        print(f"总大小: {total_size:.2f} MB")
        print("=" * 70)

    def cleanup(self):
        """删除或移动文件"""
        print("=" * 70)
        if self.keep_original:
            mode_desc = "保留原始图片和标注"
        else:
            mode_desc = "保留切分后子图"
        if self.backup_dir:
            print(f"清理YOLO数据集 - {mode_desc} - 移动模式")
        else:
            print(f"清理YOLO数据集 - {mode_desc} - 删除模式")
        print("=" * 70)

        # 先预览
        self.preview()

        if not self.files_to_delete:
            print("\n没有文件需要处理")
            return

        if self.dry_run:
            print("\n[演练模式] 不会实际执行操作")
            return

        # 如果是移动模式，创建备份目录
        if self.backup_dir:
            backup_images_dir = self.backup_dir / "images"
            backup_labels_dir = self.backup_dir / "labels"
            
            print("\n创建备份目录...")
            backup_images_dir.mkdir(parents=True, exist_ok=True)
            backup_labels_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ 备份目录已创建: {self.backup_dir}")

            print("\n移动文件...")
            for file_path in self.files_to_delete:
                try:
                    # 根据文件类型决定目标目录
                    if file_path.suffix.lower() in self.SUPPORTED_IMAGE_EXTS:
                        dest_path = backup_images_dir / file_path.name
                    else:
                        dest_path = backup_labels_dir / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    print(f"✓ 移动: {file_path.name}")
                except Exception as e:
                    print(f"✗ 移动失败: {file_path.name} - {str(e)}")

            print("\n" + "=" * 70)
            print("移动完成！")
            print("=" * 70)
            print(f"已移动文件: {len(self.files_to_delete)} 个")
            print(f"备份位置: {self.backup_dir}")
            print("=" * 70)
        else:
            print("\n确认删除...")

            # 删除文件
            for file_path in self.files_to_delete:
                try:
                    file_path.unlink()
                    print(f"✓ 删除: {file_path.name}")
                except Exception as e:
                    print(f"✗ 删除失败: {file_path.name} - {str(e)}")

            print("\n" + "=" * 70)
            print("清理完成！")
            print("=" * 70)
            print(f"已删除文件: {len(self.files_to_delete)} 个")
            print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="清理经过split_images_yolo.py处理的YOLO数据集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 预览要删除的文件（默认）
  python cleanup_split_yolo.py -i ./yolo_split

  # 预览模式（显式指定）
  python cleanup_split_yolo.py -i ./yolo_split --dry-run

  # 实际删除原始图片和标注
  python cleanup_split_yolo.py -i ./yolo_split --delete

  # 移动原始图片和标注到备份文件夹（预览模式）
  python cleanup_split_yolo.py -i ./yolo_split -b ./backup

  # 实际移动原始图片和标注到备份文件夹
  python cleanup_split_yolo.py -i ./yolo_split -b ./backup --move

  # 删除切分后的子图，只保留原始图片和标注（预览）
  python cleanup_split_yolo.py -i ./yolo_split --keep-original

  # 实际删除切分后的子图，只保留原始图片和标注
  python cleanup_split_yolo.py -i ./yolo_split --keep-original --delete
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="YOLO数据集根目录（包含images和labels文件夹）",
    )

    parser.add_argument(
        "-b",
        "--backup",
        type=str,
        default=None,
        help="备份目录，指定此参数将移动文件到该目录而不是删除",
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="实际删除文件（不指定此参数时仅预览）",
    )

    parser.add_argument(
        "--move",
        action="store_true",
        help="实际移动文件到备份目录（与-b参数配合使用，不指定时仅预览）",
    )

    parser.add_argument(
        "--keep-original",
        action="store_true",
        help="删除切分后的子图，只保留原始图片和标注（默认删除原始图片，保留子图）",
    )

    args = parser.parse_args()

    # 检查参数冲突
    if args.delete and args.backup:
        print("错误：--delete 和 --backup 不能同时使用")
        return

    # 创建清理器
    dry_run = not (args.delete or args.move)  # 如果指定了--delete或--move，则dry_run为False
    cleaner = SplitYOLOCleaner(root_dir=args.input, dry_run=dry_run, backup_dir=args.backup, keep_original=args.keep_original)

    # 验证输入
    if not cleaner.validate_inputs():
        return

    # 执行清理
    cleaner.cleanup()


if __name__ == "__main__":
    main()
