import os
import shutil


def copy_images_with_folder_name(source_dir, target_dir):
    """
    将源文件夹下所有子文件夹中的图片复制到目标文件夹，并重命名为：子文件夹名_图片名
    :param source_dir: 源文件夹路径（包含子文件夹）
    :param target_dir: 目标文件夹路径
    """
    # 确保目标文件夹存在
    os.makedirs(target_dir, exist_ok=True)

    # 遍历源文件夹下的所有子文件夹
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # 检查文件是否为图片（可根据需要扩展支持的格式）
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                # 获取子文件夹名
                folder_name = os.path.basename(root)
                # 新文件名：子文件夹名_原图片名
                new_name = f"{folder_name}_{file}"
                # 源文件路径
                src_path = os.path.join(root, file)
                # 目标文件路径
                dst_path = os.path.join(target_dir, new_name)

                # 复制文件
                shutil.copy2(src_path, dst_path)
                print(f"Copied: {src_path} -> {dst_path}")


if __name__ == "__main__":
    # 设置源文件夹和目标文件夹路径
    source_directory = "/home/tl/data/datasets/mmaction2/110_I_RAWFRAMES/val/bird"  # 替换为你的源文件夹路径
    target_directory = "/home/tl/data/datasets/classify/IR/val/bird"  # 替换为你的目标文件夹路径

    # 执行复制
    copy_images_with_folder_name(source_directory, target_directory)
    print("所有图片复制完成！")
