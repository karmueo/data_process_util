import os
import argparse
import cv2
from typing import Tuple, Optional, Collection


SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


def is_image_file(
    filename: str, exts: Optional[Collection[str]] = None
) -> bool:
    exts_set = set(map(str.lower, exts)) if exts else SUPPORTED_EXTS
    _, ext = os.path.splitext(filename)
    return ext.lower() in exts_set


def resize_with_padding(img, target_w: int, target_h: int):
    """保持比例缩放并用0填充到指定尺寸，支持灰度/三通道/四通道。"""
    if img is None:
        return None
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return None

    scale = min(target_w / w, target_h / h)
    new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))

    # 根据缩放方向选择插值算法
    if scale < 1:
        interp = cv2.INTER_AREA
    else:
        interp = cv2.INTER_LINEAR

    resized = cv2.resize(img, (new_w, new_h), interpolation=interp)

    pad_w = max(0, target_w - new_w)
    pad_h = max(0, target_h - new_h)
    top = pad_h // 2
    bottom = pad_h - top
    left = pad_w // 2
    right = pad_w - left

    # 根据通道数决定边框颜色（均为0），统一为元组，避免类型检查告警
    if len(resized.shape) == 2:  # 灰度
        channels = 1
    else:
        channels = resized.shape[2]
    value = tuple([0] * channels)

    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=value
    )
    # 保障尺寸精确（避免四舍五入引起的1像素误差）
    if padded.shape[1] != target_w or padded.shape[0] != target_h:
        padded = cv2.resize(
            padded, (target_w, target_h), interpolation=cv2.INTER_NEAREST
        )
    return padded


def process_image_inplace(
    img_path: str, target_w: int, target_h: int
) -> Tuple[bool, str]:
    """将图片按等比+填充缩放到指定尺寸，原地覆盖保存。
    返回 (是否修改, 错误信息或空)。
    """
    try:
        # 尝试保留通道（包括alpha）
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return False, "读取失败"

        # 若已是目标尺寸则跳过
        if img.shape[1] == target_w and img.shape[0] == target_h:
            return False, "已是目标尺寸"

        out = resize_with_padding(img, target_w, target_h)
        if out is None:
            return False, "处理失败"

        dir_name = os.path.dirname(img_path)
        base_name = os.path.basename(img_path)
        name_only, ext = os.path.splitext(base_name)
        # 临时文件使用原扩展的小写，提升编码器识别概率
        ext_lower = ext.lower()
        tmp_path = os.path.join(dir_name, f".{name_only}.tmp{ext_lower}")

        # 先写临时文件，再原子替换
        ok = cv2.imwrite(tmp_path, out)
        if not ok:
            # 临时文件可能未写入成功
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False, "写入临时文件失败"

        os.replace(tmp_path, img_path)
        return True, ""
    except Exception as e:
        return False, str(e)


def walk_and_process(
    root: str, target_w: int, target_h: int, dry_run: bool = False
):
    total = 0
    changed = 0
    skipped = 0
    failed = 0

    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not is_image_file(fname):
                continue
            total += 1
            path = os.path.join(dirpath, fname)
            if dry_run:
                print(f"预览: {path}")
                continue
            modified, msg = process_image_inplace(path, target_w, target_h)
            if modified:
                changed += 1
                print(f"[OK] {path}")
            else:
                if msg == "已是目标尺寸":
                    skipped += 1
                elif msg:
                    failed += 1
                    print(f"[失败] {path} - {msg}")
                else:
                    skipped += 1

    print("\n统计：")
    print(f"  总图片数:   {total}")
    if not dry_run:
        print(f"  已修改:     {changed}")
        print(f"  已跳过:     {skipped}")
        print(f"  失败:       {failed}")


def main():
    parser = argparse.ArgumentParser(
        description="递归将目录下所有图片按等比缩放并零填充到指定分辨率，原地覆盖保存"
    )
    parser.add_argument('-r', '--root', required=True, help='根目录路径')
    parser.add_argument('-W', '--width', type=int, required=True, help='目标宽度')
    parser.add_argument('-H', '--height', type=int, required=True, help='目标高度')
    parser.add_argument('--dry-run', action='store_true', help='仅预览将处理的文件，不写入')

    args = parser.parse_args()

    if args.width <= 0 or args.height <= 0:
        print("错误：宽高必须为正整数")
        return
    if not os.path.isdir(args.root):
        print(f"错误：根目录不存在 {args.root}")
        return

    walk_and_process(args.root, args.width, args.height, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
