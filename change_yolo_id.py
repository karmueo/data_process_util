"""
写一个python程序，输入yolo格式的标注文件夹，输入要修改的id，输入修改之后的id，遍历文件夹中所有的标注txt文件，修改类别id为指定id
"""
import os
import argparse


def validate_dir(path):
    """验证目录是否存在"""
    if not os.path.isdir(path):
        raise NotADirectoryError(f"目录不存在: {path}")


def process_label_file(file_path, old_id, new_id):
    """处理单个标注文件"""
    modified = False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:  # 保留空行
                new_lines.append(line)
                continue

            parts = stripped.split()
            if not parts:  # 跳过无效空行
                continue

            # 仅修改首列ID且匹配old_id的行
            if parts[0] == str(old_id):
                parts[0] = str(new_id)
                new_line = ' '.join(parts) + '\n'
                modified = True
            else:
                new_line = line  # 保留原始换行符

            new_lines.append(new_line)

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        return False
    except Exception as e:
        print(f"处理文件 {file_path} 失败: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="YOLO标注类别ID批量修改工具")
    parser.add_argument(
        "--label_dir", default="/home/tl/data/datasets/截图", help="标注文件夹路径")
    parser.add_argument("--old_id", type=int, default=0, help="原类别ID (整数)")
    parser.add_argument("--new_id", type=int, default=1, help="新类别ID (整数)")
    args = parser.parse_args()

    try:
        validate_dir(args.label_dir)
        total_files = 0
        modified_files = 0

        # 递归遍历所有子目录
        for root, dirs, files in os.walk(args.label_dir):
            for filename in files:
                if filename.endswith('.txt'):
                    total_files += 1
                    file_path = os.path.join(root, filename)
                    if process_label_file(file_path, args.old_id, args.new_id):
                        modified_files += 1

        print(f"\n操作完成！")
        print(f"扫描文件总数: {total_files}")
        print(f"修改标注文件数: {modified_files}")
        print(f"未修改文件数: {total_files - modified_files}")

    except Exception as e:
        print(f"错误: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
