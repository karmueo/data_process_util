import os
import shutil
import random
import argparse
import glob
from tqdm import tqdm


def get_image_files(input_dir):
    """
    获取指定目录下的所有图片文件
    支持的格式: jpg, jpeg, png, bmp, tiff, tif, gif, webp
    """
    image_extensions = [
        '*.jpg', '*.jpeg', '*.png', '*.bmp',
        '*.tiff', '*.tif', '*.gif', '*.webp'
    ]
    image_files = []

    for ext in image_extensions:
        # 不区分大小写的匹配
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))
        image_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    # 使用set去重，防止因大小写匹配导致重复
    return sorted(list(set(image_files)))


def split_and_move_images(input_dir, output_dir, ratio, seed):
    """
    随机分割图片并移动到新目录
    """
    # 设置随机种子，确保结果可复现
    random.seed(seed)

    # 检查输入目录是否存在
    if not os.path.isdir(input_dir):
        print(f"错误: 输入目录 {input_dir} 不存在")
        return

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有图片文件
    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"错误: 目录 {input_dir} 中没有找到图片文件")
        return

    total_files = len(image_files)
    num_to_move = int(total_files * ratio)

    print(f"在 {input_dir} 中找到 {total_files} 个图片文件")
    print(f"根据比例 {ratio}，计划移动 {num_to_move} 个文件到 {output_dir}")

    # 随机选择要移动的文件
    files_to_move = random.sample(image_files, num_to_move)

    # 移动文件
    moved_count = 0
    for file_path in tqdm(files_to_move, desc="移动文件", unit="file"):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(output_dir, filename)
        try:
            shutil.move(file_path, dest_path)
            moved_count += 1
        except Exception as e:
            print(f"错误: 移动 {filename} 失败 - {e}")

    print(f"\n操作完成! 成功移动 {moved_count} 个文件。")
    print(f"源文件夹 {input_dir} 剩余: {total_files - moved_count} 个文件。")
    print(f"目标文件夹 {output_dir} 现在有: {len(get_image_files(output_dir))} 个文件。")


def valid_ratio(value):
    """校验比例参数是否合法"""
    try:
        fvalue = float(value)
        if fvalue <= 0 or fvalue >= 1:
            raise argparse.ArgumentTypeError(
                f"比例 {fvalue} 无效, 必须在 (0, 1) 之间"
            )
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的比例值: {value}")
    return fvalue


def main():
    parser = argparse.ArgumentParser(
        description="分割图片文件夹。从输入文件夹随机剪切指定比例的图片到输出文件夹。"
    )
    parser.add_argument(
        "-i", "--input_dir",
        required=True,
        help="包含原始图片的输入文件夹路径"
    )
    parser.add_argument(
        "-o", "--output_dir",
        required=True,
        help="用于存放分割出的图片的目标文件夹路径"
    )
    parser.add_argument(
        "-r", "--ratio",
        type=valid_ratio,
        required=True,
        help="要剪切的图片比例 (0 到 1 之间, 例如 0.2 表示 20%%)"
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=42,
        help="随机种子，用于保证每次分割结果一致"
    )

    args = parser.parse_args()

    split_and_move_images(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        ratio=args.ratio,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
