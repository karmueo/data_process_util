'''
生成类似Kinetics-400的标注train.csv, val.csv
目录结构要求：
root_dir/
├── bird/          # 类别1
│   ├── bird_1.mp4
│   ├── bird_2.mp4
│   └── ...
├── uav/           # 类别2
│   ├── uav_1.mp4
│   └── ...
└── ...

python generate_kinetics_csv.py /path/to/your/root_dir --train_ratio 0.8
'''
import os
import csv
import random
from glob import glob


def generate_kinetics_style_csv(root_dir, train_ratio=0.8, output_dir=None):
    """
    生成类似 Kinetics-400 格式的 train.csv 和 val.csv 文件。

    参数:
        root_dir (str): 根目录路径，子文件夹代表类别，内含视频文件。
        train_ratio (float): 训练集比例（默认 0.8）。
        output_dir (str): 输出 CSV 的目录（默认与 root_dir 相同）。
    """
    if output_dir is None:
        output_dir = root_dir

    # 获取所有类别（子文件夹名）
    classes = sorted([d for d in os.listdir(root_dir)
                     if os.path.isdir(os.path.join(root_dir, d))])
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}  # 类别名 -> 类别ID

    # 收集所有视频文件路径和类别
    video_paths = []
    for cls in classes:
        cls_dir = os.path.join(root_dir, cls)
        videos = glob(os.path.join(cls_dir, "*.*"))  # 匹配所有文件（可调整扩展名）
        videos = [v for v in videos if v.lower().endswith(
            ('.mp4', '.avi', '.mov', '.mkv'))]  # 过滤视频文件
        for video in videos:
            video_paths.append((video, class_to_idx[cls]))

    # 随机打乱并划分训练集/验证集
    random.shuffle(video_paths)
    split_idx = int(len(video_paths) * train_ratio)
    train_data = video_paths[:split_idx]
    val_data = video_paths[split_idx:]

    # 写入 train.csv
    train_csv = os.path.join(output_dir, "train.csv")
    with open(train_csv, "w", newline="") as f:
        writer = csv.writer(f, delimiter=" ")
        for video_path, label in train_data:
            writer.writerow([video_path, label])

    # 写入 val.csv
    val_csv = os.path.join(output_dir, "val.csv")
    with open(val_csv, "w", newline="") as f:
        writer = csv.writer(f, delimiter=" ")
        for video_path, label in val_data:
            writer.writerow([video_path, label])

    print(f"生成完成！\n- 类别数: {len(classes)}\n- 总视频数: {len(video_paths)}")
    print(f"- 训练集: {len(train_data)} (保存至 {train_csv})")
    print(f"- 验证集: {len(val_data)} (保存至 {val_csv})")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="生成 Kinetics-400 风格的 CSV 标注文件")
    parser.add_argument("root_dir", type=str, help="包含类别子文件夹的根目录路径")
    parser.add_argument("--train_ratio", type=float,
                        default=0.8, help="训练集比例（默认 0.8）")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="输出 CSV 的目录（默认与 root_dir 相同）")
    args = parser.parse_args()

    generate_kinetics_style_csv(
        args.root_dir, args.train_ratio, args.output_dir)
