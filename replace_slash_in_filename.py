import json
import os


def replace_slash_in_filename(input_file, output_file=None):
    """
    读取COCO JSON文件，修改所有file_name中的/为_，并保存

    Args:
        input_file (str): 输入的JSON文件路径
        output_file (str, optional): 输出的JSON文件路径。如果为None，则覆盖原文件
    """
    # 读取输入文件
    with open(input_file, 'r') as f:
        coco_data = json.load(f)

    # 修改所有file_name
    for image in coco_data['images']:
        image['file_name'] = image['file_name'].replace('/', '_')

    # 确定输出路径（如果未指定output_file，则覆盖原文件）
    save_path = output_file if output_file else input_file

    # 写入文件
    with open(save_path, 'w') as f:
        json.dump(coco_data, f, indent=2)

    print(f"处理完成，结果已保存到: {save_path}")


def replace_slash_in_filename_safe(input_file):
    """
    安全模式：自动在原文件名后添加_modified，避免覆盖原文件

    Args:
        input_file (str): 输入的JSON文件路径
    """
    # 生成输出文件名（自动添加_modified）
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_modified{ext}"

    # 调用主处理函数
    replace_slash_in_filename(input_file, output_file)


# 使用示例
if __name__ == "__main__":
    input_file = "/home/tl/data/datasets/yolo_bird/annotations/merged_train.json"  # 替换为你的JSON文件路径
    replace_slash_in_filename_safe(input_file)
