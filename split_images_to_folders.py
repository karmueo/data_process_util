import os
import shutil
import argparse
import glob


def get_image_files(input_dir):
    """
    获取指定目录下的所有图片文件
    支持的格式: jpg, jpeg, png, bmp, tiff, tif, gif
    """
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp',
                        '*.tiff', '*.tif', '*.gif']
    image_files = []

    for ext in image_extensions:
        # 不区分大小写的匹配
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))
        image_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    return sorted(image_files)


def split_images_to_folders(input_dir, num_splits, output_base_dir=None):
    """
    将输入目录下的图片文件平均分成指定份数，分别移动到对应文件夹

    Args:
        input_dir: 输入目录路径
        num_splits: 分割份数
        output_base_dir: 输出基础目录，如果为None则使用输入目录的父目录
    """
    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录 {input_dir} 不存在")
        return

    # 获取所有图片文件
    image_files = get_image_files(input_dir)

    if not image_files:
        print(f"错误: 目录 {input_dir} 中没有找到图片文件")
        return

    print(f"找到 {len(image_files)} 个图片文件")

    # 设置输出基础目录
    if output_base_dir is None:
        output_base_dir = os.path.dirname(os.path.abspath(input_dir))

    # 获取输入目录名称作为前缀
    input_dir_name = os.path.basename(os.path.abspath(input_dir))

    # 计算每份的文件数量
    files_per_split = len(image_files) // num_splits
    remainder = len(image_files) % num_splits

    print(f"将 {len(image_files)} 个文件分成 {num_splits} 份")
    print(f"每份基本文件数: {files_per_split}")
    if remainder > 0:
        print(f"前 {remainder} 份各多分配 1 个文件")

    # 创建输出目录并移动文件
    start_idx = 0
    for i in range(num_splits):
        # 创建输出目录
        output_dir = os.path.join(output_base_dir, f"{input_dir_name}{i+1}")
        os.makedirs(output_dir, exist_ok=True)

        # 计算当前份的文件数量（前remainder份多分配一个文件）
        current_split_size = files_per_split + (1 if i < remainder else 0)
        end_idx = start_idx + current_split_size

        # 获取当前份的文件列表
        current_files = image_files[start_idx:end_idx]

        print(f"\n处理第 {i+1} 份 ({len(current_files)} 个文件) -> {output_dir}")

        # 移动文件
        for file_path in current_files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(output_dir, filename)

            try:
                shutil.move(file_path, dest_path)
                print(f"  移动: {filename}")
            except Exception as e:
                print(f"  错误: 移动 {filename} 失败 - {e}")

        start_idx = end_idx

    print(f"\n完成! 图片文件已分割到 {num_splits} 个文件夹中")


def main():
    parser = argparse.ArgumentParser(
        description="将指定文件夹下的图片文件平均分成指定份数，分别移动到对应文件夹"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="输入目录路径 (例如: /data/)"
    )
    parser.add_argument(
        "-n", "--num_splits",
        type=int,
        required=True,
        help="分割份数 (例如: 4)"
    )
    parser.add_argument(
        "-o", "--output_base",
        help="输出基础目录 (可选，默认为输入目录的父目录)"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="仅显示分割计划，不实际移动文件"
    )

    args = parser.parse_args()

    # 验证参数
    if args.num_splits <= 0:
        print("错误: 分割份数必须大于 0")
        return

    if args.dry_run:
        print("=== 干运行模式 - 仅显示分割计划 ===")
        # 这里可以添加预览逻辑
        image_files = get_image_files(args.input)
        if image_files:
            print(f"将要处理 {len(image_files)} 个图片文件")
            files_per_split = len(image_files) // args.num_splits
            remainder = len(image_files) % args.num_splits
            for i in range(args.num_splits):
                current_split_size = files_per_split + \
                    (1 if i < remainder else 0)
                print(f"文件夹 {i+1}: {current_split_size} 个文件")
    else:
        # 执行实际分割
        split_images_to_folders(
            input_dir=args.input,
            num_splits=args.num_splits,
            output_base_dir=args.output_base
        )


if __name__ == "__main__":
    main()
