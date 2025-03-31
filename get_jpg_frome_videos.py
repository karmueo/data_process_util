import cv2
import os
import argparse
import shutil
from datetime import timedelta


def extract_frames(video_path, output_dir, interval_seconds):
    # 获取视频文件名（不含扩展名）
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return

    # 获取视频基本信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    current_time = 0.0
    success = True

    while success and current_time <= duration:
        # 设置当前时间位置（单位：秒）
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)

        # 读取帧
        success, frame = cap.read()
        if not success:
            break

        # 生成时间戳字符串（HH:MM:SS）
        time_str = str(timedelta(seconds=current_time)).split(".")[0].zfill(8)

        # 生成输出文件名
        output_filename = f"{video_name}_{time_str.replace(':', '-')}.jpg"
        output_path = os.path.join(output_dir, output_filename)

        # 保存帧为JPEG
        cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"已保存: {output_path}")

        # 增加时间间隔
        current_time += interval_seconds

    cap.release()


def process_videos(input_dir, output_dir, interval_seconds, is_add):
    # 如果输出目录已存在，则删除该目录
    if is_add is not True and os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 遍历输入目录下的所有MP4文件
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".mp4"):
                video_path = os.path.join(root, file)
                print(f"\n正在处理视频: {video_path}")
                extract_frames(video_path, output_dir, interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频帧提取工具")
    parser.add_argument(
        "--input", type=str, required=True, help="输入目录路径（包含MP4视频文件）"
    )
    parser.add_argument("--output", type=str, required=True, help="输出目录路径")
    parser.add_argument("--interval", type=int, required=True, help="截取间隔（秒）")
    parser.add_argument("--is_add", type=bool, default=False, help="截取间隔（秒）")

    args = parser.parse_args()

    process_videos(args.input, args.output, args.interval, args.is_add)
