"""
将YOLO数据集的图片和标注切分成四个子图（左上、左下、右上、右下）
支持重叠区域、保留原图、输出到新目录或覆盖原目录
并可以将生成的子图和对应的标注导出到指定文件夹（在该文件夹下创建 `images/` 和 `labels/` 子目录，通过 --export 选项）
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

import cv2


class YOLOImageSplitter:
    """YOLO图片和标注切分器"""

    SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    def __init__(
        self,
        root_dir: str,
        overlap_ratio: float = 0.1,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
        keep_original: bool = True,
        generate_center: bool = False,
        require_full_bbox: bool = False,
        export_dir: Optional[str] = None,
    ):
        """
        初始化切分器

        Args:
            root_dir: YOLO数据集根目录（包含images和labels文件夹）
            overlap_ratio: 重叠区域占全图的百分比 (0-0.5)
            output_dir: 输出目录，如果为None则覆盖原目录
            overwrite: 是否覆盖原目录（当output_dir为None时生效）
            keep_original: 是否保留原始图片和标注
            generate_center: 是否生成中心子图
            require_full_bbox: 是否要求检测框完全在子图内才保存子图
            export_dir: 如果指定则把新生成的子图和标注拷贝到该目录（会在目录下创建 images/ 和 labels/ 子目录）
        """
        self.root_dir = Path(root_dir)
        self.overlap_ratio = overlap_ratio
        self.output_dir = Path(output_dir) if output_dir else None
        self.overwrite = overwrite
        self.keep_original = keep_original
        self.generate_center = generate_center
        self.require_full_bbox = require_full_bbox
        # 将生成的新子图（包括图片和对应的标注）拷贝到 export_dir
        # export_dir 为 None 表示不执行额外拷贝
        self.export_dir = Path(export_dir) if export_dir else None

        self.images_dir = self.root_dir / "images"
        self.labels_dir = self.root_dir / "labels"

        # 统计信息
        self.total_images = 0
        self.total_split = 0
        self.total_new_images = 0
        self.total_new_annotations = 0

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

        if not (0 <= self.overlap_ratio <= 0.5):
            print(f"错误：重叠比例必须在0-0.5之间，当前值: {self.overlap_ratio}")
            return False

        if self.output_dir and self.output_dir.exists() and not self.overwrite:
            print(f"错误：输出目录已存在: {self.output_dir}")
            print("使用 --overwrite 参数覆盖，或指定新的输出目录")
            return False
        if self.export_dir and self.export_dir.exists() and not self.overwrite:
            print(f"错误：导出目录已存在: {self.export_dir}")
            print("使用 --overwrite 参数覆盖，或指定新的导出目录")
            return False

        return True

    def setup_output_dirs(self) -> Tuple[Path, Path]:
        """设置输出目录"""
        if self.output_dir:
            # 输出到新目录
            out_images_dir = self.output_dir / "images"
            out_labels_dir = self.output_dir / "labels"

            if self.overwrite and self.output_dir.exists():
                print(f"删除已存在的输出目录: {self.output_dir}")
                shutil.rmtree(self.output_dir)

            out_images_dir.mkdir(parents=True, exist_ok=True)
            out_labels_dir.mkdir(parents=True, exist_ok=True)
        else:
            # 覆盖原目录
            out_images_dir = self.images_dir
            out_labels_dir = self.labels_dir

        return out_images_dir, out_labels_dir

    def setup_export_dir(self) -> Optional[Tuple[Path, Path]]:
        """如果提供了 export_dir，则创建导出目录并创建 images/ 和 labels/ 子目录，
        并返回 (export_images_dir, export_labels_dir)，否则返回 None
        """
        if not self.export_dir:
            return None

        if self.overwrite and self.export_dir.exists():
            print(f"删除已存在的导出目录: {self.export_dir}")
            shutil.rmtree(self.export_dir)

        # 创建目录并子目录
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.export_images_dir = self.export_dir / "images"
        self.export_labels_dir = self.export_dir / "labels"
        self.export_images_dir.mkdir(parents=True, exist_ok=True)
        self.export_labels_dir.mkdir(parents=True, exist_ok=True)

        return self.export_images_dir, self.export_labels_dir

    def calculate_split_regions(
        self, img_width: int, img_height: int
    ) -> List[Tuple[str, int, int, int, int]]:
        """
        计算四个切分区域的坐标

        Args:
            img_width: 图片宽度
            img_height: 图片高度

        Returns:
            List of (name, x1, y1, x2, y2) for each region
        """
        # 计算重叠像素数
        overlap_w = int(img_width * self.overlap_ratio)
        overlap_h = int(img_height * self.overlap_ratio)

        # 计算分割点（中心点向两边扩展重叠区域的一半）
        mid_x = img_width // 2
        mid_y = img_height // 2

        left_split = mid_x - overlap_w // 2
        right_split = mid_x + overlap_w // 2
        top_split = mid_y - overlap_h // 2
        bottom_split = mid_y + overlap_h // 2

        regions = [
            ("top_left", 0, 0, right_split, bottom_split),
            ("top_right", left_split, 0, img_width, bottom_split),
            ("bottom_left", 0, top_split, right_split, img_height),
            ("bottom_right", left_split, top_split, img_width, img_height),
        ]

        # 如果生成中心子图，添加中心区域
        if self.generate_center:
            # 子图的尺寸等于四个角的子图尺寸
            sub_width = right_split  # 左上、左下子图的宽度
            sub_height = bottom_split  # 左上、右上子图的高度
            
            # 计算中心子图的坐标（中心点在原图中心）
            center_x1 = mid_x - sub_width // 2
            center_y1 = mid_y - sub_height // 2
            center_x2 = center_x1 + sub_width
            center_y2 = center_y1 + sub_height
            
            # 确保不超出原图边界
            center_x1 = max(0, center_x1)
            center_y1 = max(0, center_y1)
            center_x2 = min(img_width, center_x2)
            center_y2 = min(img_height, center_y2)
            
            regions.append(("center", center_x1, center_y1, center_x2, center_y2))

        return regions

    def convert_bbox_to_region(
        self,
        bbox: List[float],
        img_width: int,
        img_height: int,
        region_x1: int,
        region_y1: int,
        region_x2: int,
        region_y2: int,
    ) -> Tuple[bool, Optional[List[float]], bool]:
        """
        将YOLO格式的bbox转换到切分后的子图坐标系

        Args:
            bbox: YOLO格式 [x_center, y_center, width, height] (归一化)
            img_width, img_height: 原图尺寸
            region_x1, region_y1, region_x2, region_y2: 子图在原图中的区域

        Returns:
            (is_valid, new_bbox, is_full): 是否有效，新的YOLO格式bbox，是否完整
        """
        # 转换为像素坐标
        x_center = bbox[0] * img_width
        y_center = bbox[1] * img_height
        box_width = bbox[2] * img_width
        box_height = bbox[3] * img_height

        # 计算bbox的边界
        x1 = x_center - box_width / 2
        y1 = y_center - box_height / 2
        x2 = x_center + box_width / 2
        y2 = y_center + box_height / 2

        # 裁剪到子图区域
        clipped_x1 = max(x1, region_x1)
        clipped_y1 = max(y1, region_y1)
        clipped_x2 = min(x2, region_x2)
        clipped_y2 = min(y2, region_y2)

        # 检查是否有交集
        if clipped_x1 >= clipped_x2 or clipped_y1 >= clipped_y2:
            return False, None, False

        # 计算裁剪后的面积占原bbox的比例
        original_area = box_width * box_height
        clipped_area = (clipped_x2 - clipped_x1) * (clipped_y2 - clipped_y1)
        area_ratio = clipped_area / original_area if original_area > 0 else 0

        # 如果裁剪后面积太小（小于原面积的10%），则丢弃
        if area_ratio < 0.1:
            return False, None, False

        # 转换到子图坐标系
        new_x1 = clipped_x1 - region_x1
        new_y1 = clipped_y1 - region_y1
        new_x2 = clipped_x2 - region_x1
        new_y2 = clipped_y2 - region_y1

        # 子图尺寸
        region_width = region_x2 - region_x1
        region_height = region_y2 - region_y1

        # 转换为YOLO格式（归一化）
        new_x_center = (new_x1 + new_x2) / 2 / region_width
        new_y_center = (new_y1 + new_y2) / 2 / region_height
        new_width = (new_x2 - new_x1) / region_width
        new_height = (new_y2 - new_y1) / region_height

        # 边界检查
        new_x_center = max(0, min(1, new_x_center))
        new_y_center = max(0, min(1, new_y_center))
        new_width = max(0, min(1, new_width))
        new_height = max(0, min(1, new_height))

        return True, [new_x_center, new_y_center, new_width, new_height], area_ratio >= 1.0

    def split_image_and_labels(
        self,
        image_path: Path,
        label_path: Path,
        out_images_dir: Path,
        out_labels_dir: Path,
    ) -> int:
        """
        切分单个图片和对应的标注

        Args:
            image_path: 图片路径
            label_path: 标注路径
            out_images_dir: 输出图片目录
            out_labels_dir: 输出标注目录

        Returns:
            生成的子图数量
        """
        # 读取图片
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"  警告：无法读取图片 {image_path}")
            return 0

        img_height, img_width = img.shape[:2]
        image_name = image_path.stem
        image_ext = image_path.suffix

        # 读取标注
        annotations = []
        if label_path.exists():
            with open(label_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        bbox = [float(x) for x in parts[1:5]]
                        annotations.append((class_id, bbox))

        # 计算切分区域
        regions = self.calculate_split_regions(img_width, img_height)

        split_count = 0
        for region_name, x1, y1, x2, y2 in regions:
            # 切分图片
            cropped_img = img[y1:y2, x1:x2]

            # 生成新文件名
            new_image_name = f"{image_name}_{region_name}{image_ext}"
            new_label_name = f"{image_name}_{region_name}.txt"

            new_image_path = out_images_dir / new_image_name
            new_label_path = out_labels_dir / new_label_name

            # 处理标注
            new_annotations = []
            has_full_bbox = False
            for class_id, bbox in annotations:
                is_valid, new_bbox, is_full = self.convert_bbox_to_region(
                    bbox, img_width, img_height, x1, y1, x2, y2
                )
                if is_valid:
                    new_annotations.append((class_id, new_bbox))
                    if is_full:
                        has_full_bbox = True

            # 如果需要完整bbox但没有，则跳过保存
            if self.require_full_bbox and not has_full_bbox:
                continue

            # 保存图片
            cv2.imwrite(str(new_image_path), cropped_img)

            # 保存标注
            with open(new_label_path, "w", encoding="utf-8") as f:
                for class_id, bbox in new_annotations:
                    line = f"{class_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n"
                    f.write(line)

            split_count += 1
            self.total_new_annotations += len(new_annotations)

            # 如果指定了导出目录，将生成的子图和label分别拷贝到 export/images 和 export/labels 子目录
            if self.export_dir and hasattr(self, 'export_images_dir') and hasattr(self, 'export_labels_dir'):
                try:
                    # 拷贝图片
                    shutil.copy2(new_image_path, self.export_images_dir / new_image_path.name)
                    # 拷贝标注
                    if new_label_path.exists():
                        shutil.copy2(new_label_path, self.export_labels_dir / new_label_path.name)
                except Exception as e:
                    print(f"  警告：导出文件到 {self.export_dir} 失败: {e}")

        self.total_new_images += split_count
        return split_count

    def process(self):
        """处理所有图片和标注"""
        if not self.validate_inputs():
            return

        print("=" * 70)
        print("YOLO图片和标注切分工具")
        print("=" * 70)
        print(f"根目录: {self.root_dir}")
        print(f"重叠比例: {self.overlap_ratio * 100:.1f}%")
        print(f"保留原图: {'是' if self.keep_original else '否'}")
        print(f"生成中心子图: {'是' if self.generate_center else '否'}")
        print(f"要求完整检测框: {'是' if self.require_full_bbox else '否'}")

        # 设置输出目录
        out_images_dir, out_labels_dir = self.setup_output_dirs()
        # 如果指定了导出目录，创建导出目录并子目录 images/ labels/
        export_dirs = None
        if self.export_dir:
            export_dirs = self.setup_export_dir()

        if self.output_dir:
            print(f"输出目录: {self.output_dir}")
        else:
            print(f"输出目录: {self.root_dir} (覆盖模式)")

        # 如果保留原图，复制原图到输出目录和/或导出目录
        if self.keep_original:
            print("\n复制原始图片和标注...")
            if self.output_dir:
                for img_file in self.images_dir.iterdir():
                    if img_file.suffix.lower() in self.SUPPORTED_IMAGE_EXTS:
                        shutil.copy2(img_file, out_images_dir / img_file.name)

                for label_file in self.labels_dir.iterdir():
                    if label_file.suffix.lower() == ".txt":
                        shutil.copy2(label_file, out_labels_dir / label_file.name)

            if self.export_dir and export_dirs:
                export_images_dir, export_labels_dir = export_dirs
                for img_file in self.images_dir.iterdir():
                    if img_file.suffix.lower() in self.SUPPORTED_IMAGE_EXTS:
                        shutil.copy2(img_file, export_images_dir / img_file.name)
                for label_file in self.labels_dir.iterdir():
                    if label_file.suffix.lower() == ".txt":
                        shutil.copy2(label_file, export_labels_dir / label_file.name)

        # 收集所有图片
        image_files = sorted(
            [
                f
                for f in self.images_dir.iterdir()
                if f.suffix.lower() in self.SUPPORTED_IMAGE_EXTS
            ]
        )

        if not image_files:
            print(f"\n错误：在 {self.images_dir} 中没有找到图片文件")
            return

        self.total_images = len(image_files)
        print(f"\n找到 {self.total_images} 个图片文件")
        print("\n开始切分...")

        # 处理每个图片
        for idx, image_path in enumerate(image_files, 1):
            print(f"[{idx}/{self.total_images}] {image_path.name}")

            label_path = self.labels_dir / f"{image_path.stem}.txt"

            split_count = self.split_image_and_labels(
                image_path, label_path, out_images_dir, out_labels_dir
            )

            if split_count > 0:
                self.total_split += 1
                print(f"  ✓ 生成 {split_count} 个子图")
            else:
                print("  ✗ 切分失败")

        # 如果不保留原图且在覆盖模式，删除原图
        if not self.keep_original and not self.output_dir:
            print("\n删除原始图片和标注...")
            for img_file in image_files:
                img_file.unlink()
                label_file = self.labels_dir / f"{img_file.stem}.txt"
                if label_file.exists():
                    label_file.unlink()

        # 打印总结
        print("\n" + "=" * 70)
        print("切分完成！")
        print("=" * 70)
        print(f"处理图片: {self.total_split}/{self.total_images}")
        print(f"生成子图: {self.total_new_images}")
        print(f"生成标注: {self.total_new_annotations}")
        if self.output_dir:
            print(f"输出目录: {self.output_dir}")
        else:
            print(f"输出目录: {self.root_dir}")

        if self.export_dir:
            if hasattr(self, 'export_images_dir') and hasattr(self, 'export_labels_dir'):
                print(f"导出目录 (images)：{self.export_images_dir}")
                print(f"导出目录 (labels)：{self.export_labels_dir}")
            else:
                print(f"导出目录: {self.export_dir}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="将YOLO数据集的图片和标注切分成四个子图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 切分到新目录，重叠10%，保留原图
  python split_images_yolo.py -i ./yolo_dataset -o ./yolo_split --overlap 0.1

  # 覆盖原目录，重叠15%，不保留原图
  python split_images_yolo.py -i ./yolo_dataset --overlap 0.15 --no-keep-original --overwrite

  # 切分到新目录，重叠20%（默认保留原图）
  python split_images_yolo.py -i ./yolo_dataset -o ./yolo_split --overlap 0.2

  生成四个角的子图 + 中心子图
  python split_images_yolo.py -i ./yolo_dataset -o ./yolo_split --overlap 0.1 --generate-center

  只保存包含完整检测框的子图
  python split_images_yolo.py -i ./yolo_dataset -o ./yolo_split --require-full-bbox
    # 生成子图并将生成的子图和对应标注导出到指定目录（将在目录下创建 images/ 和 labels/）
    python split_images_yolo.py -i ./yolo_dataset --export ./yolo_export_dir
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
        "-o",
        "--output",
        type=str,
        default=None,
        help="输出目录（如果不指定则覆盖原目录）",
    )

    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="将生成的子图和对应的标注导出到指定目录，默认会在该目录下创建 images/ 和 labels/ 子目录",
    )

    parser.add_argument(
        "--overlap",
        type=float,
        default=0.1,
        help="重叠区域占全图的百分比 (0-0.5)，默认0.1 (10%%)",
    )

    parser.add_argument(
        "--no-keep-original",
        action="store_true",
        help="不保留原始图片和标注（默认保留）",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="如果输出目录已存在，则覆盖",
    )

    parser.add_argument(
        "--generate-center",
        action="store_true",
        help="是否生成中心子图（中心点在原图中心，尺寸与四个角的子图相同）",
    )

    parser.add_argument(
        "--require-full-bbox",
        action="store_true",
        help="只保存包含完整检测框的子图（检测框完全在子图内）",
    )

    args = parser.parse_args()

    # 创建切分器
    splitter = YOLOImageSplitter(
        root_dir=args.input,
        overlap_ratio=args.overlap,
        output_dir=args.output,
        overwrite=args.overwrite,
        keep_original=not args.no_keep_original,
        generate_center=args.generate_center,
        require_full_bbox=args.require_full_bbox,
        export_dir=args.export,
    )

    # 执行切分
    splitter.process()


if __name__ == "__main__":
    main()
