import os
import re

def rename_files(folder_path, prefix="img_", new_format="{:05d}.jpg"):
    """
    重命名文件夹中的文件，从 0.jpg, 1.jpg... 改为 img_00001.jpg, img_00002.jpg...
    
    参数:
        folder_path: 目标文件夹路径
        prefix: 新文件名前缀 (默认为 "img_")
        new_format: 新文件名格式 (默认为 "{:05d}.jpg")
    """
    # 获取文件夹中所有.jpg文件
    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
    
    # 按数字顺序排序文件
    files.sort(key=lambda x: int(re.search(r'(\d+)\.jpg$', x).group(1)))
    
    # 重命名每个文件
    for i, old_name in enumerate(files, start=1):
        # 构造新文件名 (如 img_00001.jpg)
        new_name = f"{prefix}{new_format.format(i)}"
        
        # 完整的旧路径和新路径
        old_path = os.path.join(folder_path, old_name)
        new_path = os.path.join(folder_path, new_name)
        
        # 重命名文件
        os.rename(old_path, new_path)
        print(f"Renamed: {old_name} -> {new_name}")

if __name__ == "__main__":
    # 使用示例
    target_folder = input("请输入文件夹路径: ").strip()
    
    if os.path.isdir(target_folder):
        rename_files(target_folder)
        print("重命名完成！")
    else:
        print("错误: 指定的路径不是有效文件夹")