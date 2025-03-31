import cv2
import os
import argparse
import glob


def video_to_frames(video_path, output_dir, seconds_per_frame=1):
    """
    将单个视频按指定时间间隔切割为图片，文件名包含原视频名称
    """
    # 提取视频名称（不含扩展名）
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"错误：无法打开视频文件 {video_path}")
        return

    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = int(fps * seconds_per_frame)  # 计算帧间隔

    print(f"\n处理视频: {video_name}")
    print(f" - 分辨率: {int(cap.get(3))}x{int(cap.get(4))}")
    print(f" - 总帧数: {total_frames}")
    print(f" - 抽帧间隔: 每 {seconds_per_frame} 秒提取一次（{frame_interval} 帧）")

    saved_count = 0
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 按间隔保存帧，文件名包含视频名称
        if frame_index % frame_interval == 0:
            output_path = os.path.join(
                output_dir,
                f"{video_name}_frame_{saved_count:04d}.jpg"  # 唯一命名
            )
            cv2.imwrite(output_path, frame)
            saved_count += 1

        frame_index += 1

    cap.release()
    print(f" - 保存完成: {saved_count} 帧")


def process_all_videos(input_dir, output_dir, seconds_per_frame=1):
    """
    遍历输入目录下的所有 .mp4 文件并处理
    """
    # 获取所有MP4文件路径
    video_paths = glob.glob(os.path.join(input_dir, "*.mp4"))

    if not video_paths:
        print(f"错误：目录 {input_dir} 中没有找到 .mp4 文件")
        return

    print(f"找到 {len(video_paths)} 个视频文件，开始处理...")
    for idx, video_path in enumerate(video_paths, 1):
        print(f"\n[{idx}/{len(video_paths)}]")
        video_to_frames(video_path, output_dir, seconds_per_frame)


if __name__ == "__main__":
    # 命令行参数设置
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", default="drone+bird_3.20/videos/drone", help="输入视频文件夹路径")
    parser.add_argument(
        "-o", "--output", default="drone+bird_3.20/small/drone", help="输出目录")
    parser.add_argument("-s", "--seconds", type=int,
                        default=5, help="每多少秒提取一帧")
    args = parser.parse_args()

    # 执行批量处理
    process_all_videos(
        input_dir=args.input,
        output_dir=args.output,
        seconds_per_frame=args.seconds
    )
