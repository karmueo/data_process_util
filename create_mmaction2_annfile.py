'''
输入的数据集根目录文件夹路径，该文件夹下会存放若干子文件夹，每一个子文件夹，每个文件夹代表一个视频分类类别，每个文件夹中存放对应该类别的视频文件。该python分别生成{根目录名}_train_list_videos.txt和{根目录名}_val_list_videos.txt，这两个.txt文件每一行表示一个样本视频，包括 filepath（相对根目录路径）和 label，用空格分隔，例如：
some/path/000.mp4 1
some/path/001.mp4 1
some/path/002.mp4 2
some/path/003.mp4 2
some/path/004.mp4 3
some/path/005.mp4 3

{根目录名}_train_list_videos.txt和{根目录名}_val_list_videos.txt分别表述训练集和验证集，python支持输入一个比率比如0.8代表80%的数据集用于训练20的数据用于验证。

python create_mmaciton2_annfile.py --root /path/to/dataset --ratio 0.8
'''
import os
import argparse
import random


def get_all_video_files(root_dir, exts=('.mp4', '.avi', '.mov', '.mkv')):
    class_dirs = [d for d in os.listdir(
        root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    class_dirs.sort()
    video_list = []
    label_map = {}
    for idx, class_name in enumerate(class_dirs):
        label_map[class_name] = idx  # 标签
        class_dir = os.path.join(root_dir, class_name)
        for fname in os.listdir(class_dir):
            if fname.lower().endswith(exts):
                rel_path = os.path.join(class_name, fname)
                video_list.append((rel_path, label_map[class_name]))
    return video_list, label_map


def split_dataset(video_list, train_ratio):
    random.shuffle(video_list)
    train_size = int(len(video_list) * train_ratio)
    train_list = video_list[:train_size]
    val_list = video_list[train_size:]
    return train_list, val_list


def write_list_file(list_data, out_path):
    with open(out_path, 'w') as f:
        for rel_path, label in list_data:
            f.write(f"{rel_path} {label}\n")


def main(root_dir, train_ratio):
    root_dir = os.path.abspath(root_dir)
    root_name = os.path.basename(root_dir.rstrip('/'))
    video_list, label_map = get_all_video_files(root_dir)
    with open(os.path.join(root_dir, f"{root_name}_label_map.txt"), 'w') as f:
        for class_name, label in label_map.items():
            f.write(f"{label} {class_name}\n")
    print(f"标签映射: {label_map}")
    train_list, val_list = split_dataset(video_list, train_ratio)
    train_file = os.path.join(root_dir, f"{root_name}_train_list_videos.txt")
    val_file = os.path.join(root_dir, f"{root_name}_val_list_videos.txt")
    write_list_file(train_list, train_file)
    write_list_file(val_list, val_file)
    print(f"训练集样本数: {len(train_list)}，验证集样本数: {len(val_list)}")
    print(f"已生成: {train_file}, {val_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成视频分类数据集的训练/验证列表")
    parser.add_argument("--root", required=True, help="数据集根目录路径")
    parser.add_argument("--ratio", type=float, default=0.8, help="训练集比例(0-1)")
    args = parser.parse_args()
    main(args.root, args.ratio)
