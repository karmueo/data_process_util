"""
视频帧提取工具（改进版）
整合了按时间跳转和按帧顺序两种模式的优点
支持递归目录、多种视频格式、详细信息输出和错误处理
"""

import cv2
import os
import argparse
import shutil
from datetime import timedelta


class VideoFrameExtractor:
    """视频帧提取器"""

    SUPPORTED_FORMATS = (".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv")

    def __init__(
        self,
        output_dir,
        interval_seconds,
        mode="time",
        jpeg_quality=95,
        add_mode=False,
        recursive=True,
    ):
        """
        初始化提取器

        Args:
            output_dir: 输出目录
            interval_seconds: 抽帧间隔（秒）
            mode: 抽帧模式 ('time' 或 'frame')
            jpeg_quality: JPEG质量 (1-100)
            add_mode: 是否追加模式（不删除已有输出目录）
            recursive: 是否递归处理子目录
        """
        self.output_dir = output_dir
        self.interval_seconds = interval_seconds
        self.mode = mode
        self.jpeg_quality = jpeg_quality
        self.add_mode = add_mode
        self.recursive = recursive

        # 统计信息
        self.total_videos = 0
        self.successful_videos = 0
        self.total_frames_saved = 0

    def setup_output_dir(self):
        """设置输出目录"""
        if not self.add_mode and os.path.exists(self.output_dir):
            print(f"删除已存在的输出目录: {self.output_dir}")
            shutil.rmtree(self.output_dir)

        os.makedirs(self.output_dir, exist_ok=True)
        print(f"输出目录: {self.output_dir}")

    def extract_by_time(self, video_path, video_name, cap, fps, duration):
        """
        按时间跳转方式提取帧（适合精确时间点抽帧和VFR视频）

        Args:
            video_path: 视频路径
            video_name: 视频名称
            cap: VideoCapture对象
            fps: 帧率
            duration: 视频时长（秒）

        Returns:
            保存的帧数
        """
        saved_count = 0
        current_time = 0.0

        while current_time <= duration:
            # 设置当前时间位置（单位：毫秒）
            cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)

            # 读取帧
            success, frame = cap.read()
            if not success:
                break

            # 生成时间戳字符串（HH:MM:SS）
            td = timedelta(seconds=int(current_time))
            hours = td.seconds // 3600
            minutes = (td.seconds % 3600) // 60
            seconds = td.seconds % 60
            time_str = f"{hours:02d}-{minutes:02d}-{seconds:02d}"

            # 生成输出文件名
            output_filename = f"{video_name}_{time_str}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)

            # 保存帧为JPEG
            try:
                cv2.imwrite(
                    output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                )
                saved_count += 1
                if saved_count % 10 == 0:  # 每10帧打印一次进度
                    print(f"  已保存 {saved_count} 帧 (当前时间: {time_str})")
            except Exception as e:
                print(f"  警告：保存帧失败 {output_path}: {e}")

            # 增加时间间隔
            current_time += self.interval_seconds

        return saved_count

    def extract_by_frame(self, video_path, video_name, cap, fps, total_frames):
        """
        按帧顺序方式提取帧（适合CFR视频，处理效率更高）

        Args:
            video_path: 视频路径
            video_name: 视频名称
            cap: VideoCapture对象
            fps: 帧率
            total_frames: 总帧数

        Returns:
            保存的帧数
        """
        # 计算帧间隔，确保至少为1
        frame_interval = max(1, int(round(fps * self.interval_seconds)))

        print(
            f"  抽帧间隔: 每 {self.interval_seconds} 秒提取一次（{frame_interval} 帧）"
        )

        saved_count = 0
        frame_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 按间隔保存帧
            if frame_index % frame_interval == 0:
                # 计算当前时间（用于文件名）
                current_time_sec = frame_index / fps if fps > 0 else 0
                td = timedelta(seconds=int(current_time_sec))
                hours = td.seconds // 3600
                minutes = (td.seconds % 3600) // 60
                seconds = td.seconds % 60
                time_str = f"{hours:02d}-{minutes:02d}-{seconds:02d}"

                output_filename = f"{video_name}_frame_{saved_count:04d}_{time_str}.jpg"
                output_path = os.path.join(self.output_dir, output_filename)

                try:
                    cv2.imwrite(
                        output_path,
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality],
                    )
                    saved_count += 1
                    if saved_count % 10 == 0:  # 每10帧打印一次进度
                        progress = f"{frame_index}/{total_frames}"
                        print(f"  已保存 {saved_count} 帧 (进度: {progress})")
                except Exception as e:
                    print(f"  警告：保存帧失败 {output_path}: {e}")

            frame_index += 1

        return saved_count

    def extract_frames_from_video(self, video_path):
        """
        从单个视频提取帧

        Args:
            video_path: 视频文件路径

        Returns:
            保存的帧数，失败返回None
        """
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("  错误：无法打开视频文件")
            return None

        try:
            # 获取视频基本信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 检查FPS是否有效
            if fps <= 0 or fps > 1000:  # FPS异常
                print(f"  警告：FPS值异常 ({fps})，尝试估算...")
                fps = 25.0  # 使用默认值

            duration = total_frames / fps if fps > 0 else 0

            print(f"  分辨率: {width}x{height}")
            print(f"  FPS: {fps:.2f}")
            print(f"  总帧数: {total_frames}")
            print(f"  时长: {timedelta(seconds=int(duration))}")

            # 根据模式选择提取方法
            if self.mode == "time":
                saved_count = self.extract_by_time(
                    video_path, video_name, cap, fps, duration
                )
            else:  # frame mode
                saved_count = self.extract_by_frame(
                    video_path, video_name, cap, fps, total_frames
                )

            return saved_count

        except Exception as e:
            print(f"  错误：处理视频时发生异常: {e}")
            return None
        finally:
            cap.release()

    def find_video_files(self, input_dir):
        """
        查找视频文件

        Args:
            input_dir: 输入目录

        Returns:
            视频文件路径列表
        """
        video_files = []

        if self.recursive:
            # 递归查找
            for root, _, files in os.walk(input_dir):
                for file in files:
                    if file.lower().endswith(self.SUPPORTED_FORMATS):
                        video_files.append(os.path.join(root, file))
        else:
            # 只在顶层目录查找
            for file in os.listdir(input_dir):
                if file.lower().endswith(self.SUPPORTED_FORMATS):
                    video_files.append(os.path.join(input_dir, file))

        return sorted(video_files)

    def process_videos(self, input_dir):
        """
        处理目录下的所有视频

        Args:
            input_dir: 输入目录
        """
        # 设置输出目录
        self.setup_output_dir()

        # 查找视频文件
        video_files = self.find_video_files(input_dir)

        if not video_files:
            print(f"错误：在 {input_dir} 中没有找到支持的视频文件")
            print(f"支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
            return

        self.total_videos = len(video_files)
        print(f"\n找到 {self.total_videos} 个视频文件")
        print(f"抽帧模式: {'按时间跳转' if self.mode == 'time' else '按帧顺序'}")
        print(f"抽帧间隔: {self.interval_seconds} 秒")
        print(f"JPEG质量: {self.jpeg_quality}")
        print(f"递归模式: {'是' if self.recursive else '否'}\n")

        # 处理每个视频
        for idx, video_path in enumerate(video_files, 1):
            print(f"[{idx}/{self.total_videos}] 正在处理: {video_path}")

            saved_count = self.extract_frames_from_video(video_path)

            if saved_count is not None:
                self.successful_videos += 1
                self.total_frames_saved += saved_count
                print(f"  完成：保存了 {saved_count} 帧\n")
            else:
                print("  失败：跳过此视频\n")

        # 打印总结
        print("=" * 60)
        print("处理完成！")
        print(f"成功处理: {self.successful_videos}/{self.total_videos} 个视频")
        print(f"总共保存: {self.total_frames_saved} 帧")
        print(f"输出目录: {self.output_dir}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="视频帧提取工具（改进版）- 支持按时间/按帧两种模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 按时间模式，每5秒抽一帧，递归处理
  python extract_video_frames.py -i videos/ -o output/ -t 5

  # 按帧模式，每3秒抽一帧，只处理顶层目录
  python extract_video_frames.py -i videos/ -o output/ -t 3 \\
      -m frame --no-recursive

  # 追加模式，不删除已有输出
  python extract_video_frames.py -i videos/ -o output/ -t 2 --add
        """,
    )

    parser.add_argument(
        "-i", "--input", type=str, required=True, help="输入目录路径（包含视频文件）"
    )

    parser.add_argument("-o", "--output", type=str, required=True, help="输出目录路径")

    parser.add_argument(
        "-t", "--interval", type=float, required=True, help="抽帧间隔（秒），支持小数"
    )

    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["time", "frame"],
        default="time",
        help="抽帧模式: time=按时间跳转(适合VFR/精确时间点), frame=按帧顺序(适合CFR/高效处理) [默认: time]",
    )

    parser.add_argument(
        "-q", "--quality", type=int, default=95, help="JPEG质量 (1-100) [默认: 95]"
    )

    parser.add_argument(
        "--add",
        action="store_true",
        help="追加模式：在已有输出目录上追加，不删除已有文件",
    )

    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="禁用递归：只处理输入目录的顶层视频文件",
    )

    args = parser.parse_args()

    # 验证参数
    if not os.path.isdir(args.input):
        print(f"错误：输入目录不存在: {args.input}")
        return

    if args.quality < 1 or args.quality > 100:
        print("错误：JPEG质量必须在1-100之间")
        return

    if args.interval <= 0:
        print("错误：抽帧间隔必须大于0")
        return

    # 创建提取器并处理
    extractor = VideoFrameExtractor(
        output_dir=args.output,
        interval_seconds=args.interval,
        mode=args.mode,
        jpeg_quality=args.quality,
        add_mode=args.add,
        recursive=not args.no_recursive,
    )

    extractor.process_videos(args.input)


if __name__ == "__main__":
    main()

""" # 查看帮助
python extract_video_frames.py -h

# 按时间模式，每5秒抽一帧（默认，递归处理）
python extract_video_frames.py -i videos/ -o output/ -t 5

# 按帧模式，每3秒抽一帧，只处理顶层目录
python extract_video_frames.py -i videos/ -o output/ -t 3 -m frame --no-recursive

# 追加模式，不删除已有输出，设置JPEG质量为90
python extract_video_frames.py -i videos/ -o output/ -t 2 --add -q 90

# 每0.5秒抽一帧（支持小数）
python extract_video_frames.py -i videos/ -o output/ -t 0.5 """
