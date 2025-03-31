"""
 我的数据保护图片文件夹和标注文件夹，图片名称和标注名称对应，标注为yolo格式标注比如：0 0.511146 0.454667 0.022219 0.017037
。写一个python程序，输入标注的类别id比如0，提取该类别的所有图片和标注到一个新的文件夹下，并生成Images和laobes文件夹
"""
import os
import shutil
import argparse


def validate_paths(img_dir, label_dir):
    """验证输入目录是否存在"""
    if not os.path.exists(img_dir):
        raise FileNotFoundError(f"图片目录不存在: {img_dir}")
    if not os.path.exists(label_dir):
        raise FileNotFoundError(f"标注目录不存在: {label_dir}")


def create_output_dirs(output_dir):
    """创建输出目录结构"""
    os.makedirs(os.path.join(output_dir, "Images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)


def filter_files(class_id, img_dir, label_dir):
    """筛选包含指定类别的文件"""
    matched_files = []

    # 遍历标注目录
    for label_file in os.listdir(label_dir):
        if not label_file.endswith(".txt"):
            continue

        label_path = os.path.join(label_dir, label_file)

        # 检查标注文件是否包含目标类别
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 1 and parts[0] == str(class_id):
                    # 构建图片文件名（支持多种图片格式）
                    base_name = os.path.splitext(label_file)[0]
                    img_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
                    img_found = False

                    for ext in img_extensions:
                        img_file = base_name + ext
                        img_path = os.path.join(img_dir, img_file)
                        if os.path.exists(img_path):
                            matched_files.append((img_path, label_path))
                            img_found = True
                            break

                    if not img_found:
                        print(f"警告: 找不到 {base_name} 的图片文件")
                    break  # 找到至少一个目标类别即可
    return matched_files


def copy_files(files, output_dir):
    """复制文件到目标目录"""
    img_count = 0
    label_count = 0

    for img_src, label_src in files:
        # 复制图片
        img_name = os.path.basename(img_src)
        img_dest = os.path.join(output_dir, "Images", img_name)
        shutil.copy2(img_src, img_dest)
        img_count += 1

        # 复制标注
        label_name = os.path.basename(label_src)
        label_dest = os.path.join(output_dir, "labels", label_name)
        shutil.copy2(label_src, label_dest)
        label_count += 1

    return img_count, label_count


def main():
    parser = argparse.ArgumentParser(description="YOLO数据集类别提取工具")
    parser.add_argument("--class_id", type=int,
                        default=2, help="要提取的类别ID (整数)")
    parser.add_argument("--img_dir",
                        default="bird_717/images/Train", help="原始图片目录路径")
    parser.add_argument("--label_dir",
                        default="bird_717/labels/Train", help="原始标注目录路径")
    parser.add_argument("--output_dir",
                        default="bird_717/only_bird", help="输出目录路径")
    args = parser.parse_args()

    try:
        # 验证输入路径
        validate_paths(args.img_dir, args.label_dir)

        # 创建输出目录
        create_output_dirs(args.output_dir)

        # 筛选文件
        matched_files = filter_files(
            args.class_id, args.img_dir, args.label_dir)
        if not matched_files:
            print(f"未找到包含类别 {args.class_id} 的标注")
            return

        # 复制文件
        img_count, label_count = copy_files(matched_files, args.output_dir)

        # 输出统计信息
        print("\n操作完成！")
        print(f"找到 {len(matched_files)} 个有效样本")
        print(f"复制图片: {img_count} 张")
        print(f"复制标注: {label_count} 个")
        print(f"输出目录: {os.path.abspath(args.output_dir)}")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
