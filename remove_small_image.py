import os
from PIL import Image


def delete_small_images(root_dir, min_resolution):
    """
    删除根目录下所有子文件夹中尺寸不达标的图片
    :param root_dir: 根目录路径（包含多个分类子文件夹）
    :param min_resolution: 最小分辨率（长或宽）
    """
    # 支持的图片格式
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

    # 遍历根目录下的所有子文件夹和文件
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            # 检查是否为图片文件
            if file.lower().endswith(image_extensions):
                file_path = os.path.join(subdir, file)
                try:
                    # 打开图片并获取尺寸
                    with Image.open(file_path) as img:
                        width, height = img.size
                        # 判断长或宽是否小于阈值
                        if width < min_resolution or height < min_resolution:
                            os.remove(file_path)
                            print(f"已删除：{file_path}（尺寸：{width}x{height}）")
                except Exception as e:
                    print(f"处理失败：{file_path}，错误原因：{e}")


if __name__ == "__main__":
    # 用户输入参数
    root_folder = input("请输入根目录路径：")
    min_res = int(input("请输入最小分辨率（单位：像素）："))

    # 执行删除操作
    delete_small_images(root_folder, min_res)
    print("处理完成！")
