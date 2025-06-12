'''
历指定目录下的所有图片文件，将它们按中心裁剪为指定分辨率，并保存到目标文件夹
'''
import os
from PIL import Image


def center_crop_images(input_dir, target_width, target_height):
    """
    遍历输入目录下的图片，按中心裁剪为指定分辨率并保存到同级images目录
    同时在img_idx目录创建test_IRSTD-1K.txt文件记录文件名

    参数:
        input_dir (str): 输入图片目录路径
        target_width (int): 目标宽度
        target_height (int): 目标高度
    """
    # 获取输入目录的父目录路径
    parent_dir = os.path.dirname(input_dir)

    # 创建images输出目录
    images_dir = os.path.join(parent_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    # 创建img_idx目录和test_IRSTD-1K.txt文件
    img_idx_dir = os.path.join(parent_dir, 'img_idx')
    os.makedirs(img_idx_dir, exist_ok=True)
    txt_path = os.path.join(img_idx_dir, 'test_IRSTD-1K.txt')

    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

    # 用于收集所有处理过的文件名
    processed_files = []

    # 遍历输入目录
    for root, _, files in os.walk(input_dir):
        for file in files:
            # 检查文件是否为支持的图片格式
            if file.lower().endswith(supported_formats):
                input_path = os.path.join(root, file)
                try:
                    # 打开图片
                    with Image.open(input_path) as img:
                        # 获取原始尺寸
                        width, height = img.size

                        # 计算裁剪区域
                        left = (width - target_width) / 2
                        top = (height - target_height) / 2
                        right = (width + target_width) / 2
                        bottom = (height + target_height) / 2

                        # 确保裁剪区域不超出图片范围
                        left = max(0, left)
                        top = max(0, top)
                        right = min(width, right)
                        bottom = min(height, bottom)

                        # 执行裁剪
                        cropped_img = img.crop((left, top, right, bottom))

                        # 构建输出路径
                        output_path = os.path.join(images_dir, file)

                        # 保存裁剪后的图片
                        cropped_img.save(output_path)

                        # 记录文件名（不带后缀）
                        filename_without_ext = os.path.splitext(file)[0]
                        processed_files.append(filename_without_ext)

                        print(f"已处理: {input_path} -> {output_path}")

                except Exception as e:
                    print(f"处理图片 {input_path} 时出错: {e}")

    # 将处理过的文件名写入txt文件
    with open(txt_path, 'w') as f:
        for filename in processed_files:
            f.write(f"{filename}\n")

    print(f"图片裁剪完成! 结果保存在 {images_dir}")
    print(f"文件名列表已写入 {txt_path}")


if __name__ == "__main__":
    # 用户输入
    input_dir = input("请输入图片目录路径: ").strip()

    # 输入验证
    while True:
        try:
            target_width = int(input("请输入目标宽度(像素): "))
            target_height = int(input("请输入目标高度(像素): "))
            if target_width > 0 and target_height > 0:
                break
            else:
                print("宽度和高度必须为正整数，请重新输入。")
        except ValueError:
            print("请输入有效的整数。")

    # 执行裁剪
    center_crop_images(input_dir, target_width, target_height)
