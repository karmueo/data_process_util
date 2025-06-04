'''
输入根目录，遍历根目录下所有子目录，把子文件夹中所有的图片复制到指定的输出路径下，把子文件夹所有的标注json文件复制到指定的输出路径下，这两个路径默认情况下可以相同
'''
import os
import shutil


def copy_images_and_jsons(root_dir, output_dir=None, image_extensions=('.jpg', '.jpeg', '.png', '.bmp'), json_extension='.json'):
    """
    复制根目录下所有子文件夹中的图片和 JSON 文件到输出目录。

    参数:
        root_dir (str): 根目录路径（包含子文件夹的路径）。
        output_dir (str): 输出目录路径（默认与 root_dir 相同）。
        image_extensions (tuple): 图片文件扩展名列表。
        json_extension (str): JSON 文件扩展名。
    """
    # 设置默认输出目录
    if output_dir is None:
        output_dir = root_dir

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 遍历根目录下的所有子文件夹
    for subdir, _, files in os.walk(root_dir):
        # 跳过根目录自身（如果不需要）
        if subdir == root_dir:
            continue

        # 处理每个文件
        for file in files:
            file_path = os.path.join(subdir, file)

            # 复制图片文件
            if file.lower().endswith(image_extensions):
                output_image_path = os.path.join(output_dir, file)
                shutil.copy2(file_path, output_image_path)
                print(f"复制图片: {file} -> {output_image_path}")

            # 复制 JSON 文件
            elif file.endswith(json_extension):
                output_json_path = os.path.join(output_dir, file)
                shutil.copy2(file_path, output_json_path)
                print(f"复制标注: {file} -> {output_json_path}")


if __name__ == "__main__":
    # 用户输入根目录路径
    root_dir = input("请输入根目录路径: ").strip()

    # 可选：指定不同的输出路径（默认与 root_dir 相同）
    output_dir = input("请输入输出路径（直接回车使用根目录）: ").strip()
    if not output_dir:
        output_dir = None

    # 执行复制操作
    copy_images_and_jsons(root_dir, output_dir)
    print("操作完成！")
