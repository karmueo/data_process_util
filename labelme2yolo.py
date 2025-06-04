'''
遍历根目录下所有子文件夹，对于每一个子文件，调用命令labelme2yolo --json_dir <根目录>/子文件夹
'''
import os
import subprocess


def convert_labelme_to_yolo(root_dir):
    """
    遍历根目录下的所有子文件夹，对每个子文件夹执行 labelme2yolo 转换。

    参数:
        root_dir (str): 根目录路径（包含子文件夹的路径）。
    """
    # 检查根目录是否存在
    if not os.path.isdir(root_dir):
        print(f"错误：目录 '{root_dir}' 不存在！")
        return

    # 遍历根目录下的所有子文件夹
    for subdir in os.listdir(root_dir):
        subdir_path = os.path.join(root_dir, subdir)

        # 确保是目录（跳过文件）
        if not os.path.isdir(subdir_path):
            continue

        # 检查子文件夹中是否有 JSON 文件（LabelMe 标注文件）
        has_json = any(fname.endswith('.json')
                       for fname in os.listdir(subdir_path))
        if not has_json:
            print(f"跳过目录 '{subdir}'（未找到 JSON 文件）")
            continue

        # 构造 labelme2yolo 命令
        cmd = f"labelme2yolo --json_dir {subdir_path}"
        print(f"正在处理: {cmd}")

        # 执行命令
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"转换完成: {subdir}")
        except subprocess.CalledProcessError as e:
            print(f"转换失败（目录: {subdir}）: {e}")


if __name__ == "__main__":
    # 用户输入根目录路径
    root_dir = input("请输入根目录路径: ").strip()
    convert_labelme_to_yolo(root_dir)
