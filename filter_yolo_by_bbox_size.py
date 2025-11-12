"""
YOLO标注框大小过滤工具

此脚本根据检测框的尺寸过滤YOLO格式的标注数据。
它会删除超出最大值或低于最小值尺寸阈值的标注框，并删除对应的图片。

为了安全验证，脚本会在删除前将带有删除标记的检测框的预览图片保存到指定文件夹。

用法示例：

1. 基本用法（删除过小或过大的框）：
   python filter_yolo_by_bbox_size.py /path/to/dataset --min_w 20 --min_h 10 --max_w 128 --max_h 64

2. 干运行模式（仅生成预览，不删除文件）：
   python filter_yolo_by_bbox_size.py /path/to/dataset --dry_run

3. 自定义预览目录：
   python filter_yolo_by_bbox_size.py /path/to/dataset --preview_dir ./my_preview

4. 删除太小的框（最小50x50像素）：
   python filter_yolo_by_bbox_size.py /path/to/dataset --min_w 50 --min_h 50

5. 删除太大的框（最大200x200像素）：
   python filter_yolo_by_bbox_size.py /path/to/dataset --max_w 200 --max_h 200

6. 严格的尺寸范围（只保留80-120像素的框）：
   python filter_yolo_by_bbox_size.py /path/to/dataset --min_w 80 --min_h 80 --max_w 120 --max_h 120

数据集结构要求：
dataset/
├── images/          # 图片文件夹
│   ├── image1.jpg
│   ├── image2.png
│   └── ...
└── labels/          # YOLO标注文件夹
    ├── image1.txt
    ├── image2.txt
    └── ...
"""

import argparse
from pathlib import Path
from typing import List, Tuple

import cv2


def load_yolo_annotation(
    label_file: Path,
) -> List[Tuple[int, float, float, float, float]]:
    """
    Load YOLO annotation from a txt file.

    Args:
        label_file: Path to the YOLO label file

    Returns:
        List of tuples: (class_id, x_center, y_center, width, height)
        where x_center, y_center, width, height are normalized to [0, 1]
    """
    annotations = []
    if not label_file.exists():
        return annotations

    with open(label_file, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    annotations.append((class_id, x_center, y_center, width, height))
                except ValueError:
                    continue

    return annotations


def save_yolo_annotation(
    label_file: Path, annotations: List[Tuple[int, float, float, float, float]]
) -> None:
    """
    Save YOLO annotations to a txt file.

    Args:
        label_file: Path to save the YOLO label file
        annotations: List of tuples: (class_id, x_center, y_center, width, height)
    """
    with open(label_file, "w") as f:
        for class_id, x_center, y_center, width, height in annotations:
            f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")


def filter_annotations(
    annotations: List[Tuple[int, float, float, float, float]],
    image_width: int,
    image_height: int,
    min_w: int,
    min_h: int,
    max_w: int,
    max_h: int,
) -> Tuple[List[Tuple[int, float, float, float, float]], List[int]]:
    """
    Filter YOLO annotations based on bounding box size constraints.

    Args:
        annotations: List of YOLO annotations
        image_width: Width of the image in pixels
        image_height: Height of the image in pixels
        min_w: Minimum bounding box width in pixels
        min_h: Minimum bounding box height in pixels
        max_w: Maximum bounding box width in pixels
        max_h: Maximum bounding box height in pixels

    Returns:
        Tuple of (filtered_annotations, indices_of_removed)
    """
    filtered_annotations = []
    removed_indices = []

    for idx, (class_id, x_center, y_center, width, height) in enumerate(annotations):
        # Convert normalized coordinates to pixel coordinates
        bbox_w_px = width * image_width
        bbox_h_px = height * image_height

        # Check if bounding box meets size constraints
        if min_w <= bbox_w_px <= max_w and min_h <= bbox_h_px <= max_h:
            filtered_annotations.append((class_id, x_center, y_center, width, height))
        else:
            removed_indices.append(idx)

    return filtered_annotations, removed_indices


def draw_bboxes_on_image(
    image_path: Path,
    annotations: List[Tuple[int, float, float, float, float]],
    removed_indices: List[int],
    output_path: Path,
) -> None:
    """
    Draw bounding boxes on image and save to output file.

    Args:
        image_path: Path to the image
        annotations: List of YOLO annotations
        removed_indices: Indices of annotations to be removed
        output_path: Path to save the preview image
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return

    height, width, _ = img.shape

    # Draw remaining annotations in green
    for idx, (class_id, x_center, y_center, bbox_w, bbox_h) in enumerate(annotations):
        if idx not in removed_indices:
            x_min = int((x_center - bbox_w / 2) * width)
            y_min = int((y_center - bbox_h / 2) * height)
            x_max = int((x_center + bbox_w / 2) * width)
            y_max = int((y_center + bbox_h / 2) * height)
            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(
                img,
                f"Keep-{class_id}",
                (x_min, y_min - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

    # Draw removed annotations in red
    for idx in removed_indices:
        class_id, x_center, y_center, bbox_w, bbox_h = annotations[idx]
        x_min = int((x_center - bbox_w / 2) * width)
        y_min = int((y_center - bbox_h / 2) * height)
        x_max = int((x_center + bbox_w / 2) * width)
        y_max = int((y_center + bbox_h / 2) * height)
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
        cv2.putText(
            img,
            f"Delete-{class_id}",
            (x_min, y_min - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img)


def process_yolo_dataset(
    root_dir: Path,
    min_w: int,
    min_h: int,
    max_w: int,
    max_h: int,
    preview_dir: Path,
    dry_run: bool = False,
) -> None:
    """
    Process YOLO dataset and filter annotations by bounding box size.

    Args:
        root_dir: Root directory containing 'images' and 'labels' folders
        min_w: Minimum bounding box width in pixels
        min_h: Minimum bounding box height in pixels
        max_w: Maximum bounding box width in pixels
        max_h: Maximum bounding box height in pixels
        preview_dir: Directory to save preview images
        dry_run: If True, only generate previews without actual deletion
    """
    images_dir = root_dir / "images"
    labels_dir = root_dir / "labels"

    if not images_dir.exists() or not labels_dir.exists():
        print(f"Error: 'images' or 'labels' folder not found in {root_dir}")
        return

    # Supported image extensions
    supported_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    # Find all images
    image_files = []
    for ext in supported_exts:
        image_files.extend(images_dir.glob(f"*{ext}"))
        image_files.extend(images_dir.glob(f"*{ext.upper()}"))

    image_files = sorted(set(image_files))  # Remove duplicates and sort

    total_images = len(image_files)
    deleted_images = 0
    deleted_annotations = 0
    kept_images = 0
    kept_annotations = 0

    print(f"\nProcessing {total_images} images...")
    print(
        f"Size constraints: min_w={min_w}, min_h={min_h}, max_w={max_w}, max_h={max_h}"
    )
    print(f"Dry run mode: {dry_run}\n")

    for image_path in image_files:
        # Find corresponding label file
        label_name = image_path.stem + ".txt"
        label_path = labels_dir / label_name

        if not label_path.exists():
            print(f"Warning: No label file for {image_path.name}")
            continue

        # Load image and annotations
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Warning: Cannot read image {image_path}")
            continue

        image_height, image_width, _ = img.shape
        annotations = load_yolo_annotation(label_path)

        # Filter annotations
        filtered_annotations, removed_indices = filter_annotations(
            annotations, image_width, image_height, min_w, min_h, max_w, max_h
        )

        # Generate preview
        preview_path = preview_dir / image_path.name
        draw_bboxes_on_image(image_path, annotations, removed_indices, preview_path)

        # Check if image should be deleted
        if len(filtered_annotations) == 0 and len(annotations) > 0:
            # All annotations were removed, delete the image
            if not dry_run:
                image_path.unlink()
                label_path.unlink()
            deleted_images += 1
            deleted_annotations += len(annotations)
            print(
                f"[DELETE] {image_path.name}: All {len(annotations)} annotations removed"
            )
        elif len(removed_indices) > 0:
            # Some annotations were removed, update label file
            if not dry_run:
                save_yolo_annotation(label_path, filtered_annotations)
            deleted_annotations += len(removed_indices)
            kept_annotations += len(filtered_annotations)
            print(
                f"[UPDATE] {image_path.name}: Removed {len(removed_indices)} annotations, "
                f"kept {len(filtered_annotations)}"
            )
        else:
            # No changes
            kept_images += 1
            kept_annotations += len(annotations)

    # Print summary
    print("\n" + "=" * 60)
    print("Processing Summary:")
    print(f"  Total images processed: {total_images}")
    print(f"  Deleted images: {deleted_images}")
    print(
        f"  Kept images: {kept_images + (total_images - deleted_images - kept_images)}"
    )
    print(f"  Deleted annotations: {deleted_annotations}")
    print(f"  Kept annotations: {kept_annotations}")
    print(f"  Preview images saved to: {preview_dir}")
    if dry_run:
        print("  (DRY RUN MODE - No actual files were deleted)")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Filter YOLO annotations by bounding box size"
    )
    parser.add_argument(
        "root_dir",
        type=Path,
        help="Root directory containing 'images' and 'labels' folders",
    )
    parser.add_argument(
        "--min_w",
        type=int,
        default=5,
        help="Minimum bounding box width in pixels (default: 5)",
    )
    parser.add_argument(
        "--min_h",
        type=int,
        default=5,
        help="Minimum bounding box height in pixels (default: 5)",
    )
    parser.add_argument(
        "--max_w",
        type=int,
        default=64,
        help="Maximum bounding box width in pixels (default: 64)",
    )
    parser.add_argument(
        "--max_h",
        type=int,
        default=64,
        help="Maximum bounding box height in pixels (default: 64)",
    )
    parser.add_argument(
        "--preview_dir",
        type=Path,
        default=Path("./yolo_filter_preview"),
        help="Directory to save preview images (default: ./yolo_filter_preview)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: only generate previews without actual deletion",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.root_dir.exists():
        print(f"Error: Root directory {args.root_dir} does not exist")
        return

    if args.min_w < 1 or args.min_h < 1 or args.max_w < 1 or args.max_h < 1:
        print("Error: All size constraints must be positive integers")
        return

    if args.min_w > args.max_w or args.min_h > args.max_h:
        print("Error: Minimum size constraints cannot exceed maximum")
        return

    process_yolo_dataset(
        args.root_dir,
        args.min_w,
        args.min_h,
        args.max_w,
        args.max_h,
        args.preview_dir,
        args.dry_run,
    )


if __name__ == "__main__":
    main()
