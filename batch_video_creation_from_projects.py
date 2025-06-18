import os
import cv2
import argparse


def get_sorted_numeric_dirs(path):
    """返回指定路径下所有按数字排序的子目录名（字符串）"""
    if not os.path.isdir(path):
        return []
    return sorted(
        [d for d in os.listdir(path) if os.path.isdir(
            os.path.join(path, d)) and d.isdigit()],
        key=lambda x: int(x)
    )


def get_sorted_numeric_images(folder_path):
    """返回指定文件夹下所有按数字排序的jpg图片完整路径"""
    if not os.path.isdir(folder_path):
        return []
    imgs = []
    for f_name in os.listdir(folder_path):
        if f_name.lower().endswith('.jpg'):
            name_part = os.path.splitext(f_name)[0]
            if name_part.isdigit():
                imgs.append(
                    (int(name_part), os.path.join(folder_path, f_name)))
    imgs.sort(key=lambda x: x[0])
    return [p for _, p in imgs]


def create_video_from_image_paths(image_paths, output_video_path, fps):
    """从图片路径列表创建视频"""
    if not image_paths:
        print(f"警告：没有图片提供给 {output_video_path}，跳过视频创建。")
        return

    try:
        first_image = cv2.imread(image_paths[0])
        if first_image is None:
            print(
                f"错误：无法读取第一张图片 '{image_paths[0]}' 用于 {output_video_path}。请检查文件是否有效。")
            return
        height, width, _ = first_image.shape
    except Exception as e:
        print(f"读取第一张图片时出错 ({image_paths[0]}): {e}")
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(
        output_video_path, fourcc, float(fps), (width, height))

    if not video_writer.isOpened():
        print(f"错误：无法打开视频文件进行写入: '{output_video_path}'")
        return

    print(f"\n正在为 '{output_video_path}' 创建视频，帧率: {fps}，尺寸: {width}x{height}...")
    for i, image_path in enumerate(image_paths):
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"警告：跳过无法读取的图片 '{image_path}'")
            continue

        if frame.shape[0] != height or frame.shape[1] != width:
            print(
                f"警告：图片 '{image_path}' 的尺寸 ({frame.shape[1]}x{frame.shape[0]}) 与第一张图片 ({width}x{height}) 不同。将调整大小。")
            frame = cv2.resize(frame, (width, height))

        video_writer.write(frame)
        print(
            f"  已为 '{os.path.basename(output_video_path)}' 处理帧 {i+1}/{len(image_paths)}", end='\r')

    video_writer.release()
    print(f"\n视频 '{output_video_path}' 已成功创建。")


def process_all_projects(grand_root_dir, fps):
    """
    遍历 grand_root_dir 下的每个子目录（视为一个项目），
    并为每个项目生成一个视频。
    """
    if not os.path.isdir(grand_root_dir):
        print(f"错误：指定的根目录 '{grand_root_dir}' 不存在或不是一个目录。")
        return

    for project_name in os.listdir(grand_root_dir):
        project_path = os.path.join(grand_root_dir, project_name)

        if os.path.isdir(project_path):
            print(f"\n开始处理项目: '{project_name}'")

            # 获取项目内按数字排序的序列文件夹 (0, 1, 2, ...)
            sequence_folders = get_sorted_numeric_dirs(project_path)

            if not sequence_folders:
                print(f"  在项目 '{project_name}' 中没有找到数字命名的序列文件夹。")
                continue

            all_project_images = []
            print(f"  按以下顺序为项目 '{project_name}' 收集图片：")
            for seq_folder_name in sequence_folders:
                seq_folder_path = os.path.join(project_path, seq_folder_name)
                images_in_seq_folder = get_sorted_numeric_images(
                    seq_folder_path)

                if images_in_seq_folder:
                    print(
                        f"    从文件夹 '{seq_folder_name}' 中收集 {len(images_in_seq_folder)} 张图片。")
                    all_project_images.extend(images_in_seq_folder)
                else:
                    print(f"    文件夹 '{seq_folder_name}' 中没有图片。")

            if all_project_images:
                output_video_filename = f"{project_name}.mp4"
                # 视频输出在 grand_root_dir 中，与项目文件夹同级
                output_video_path = os.path.join(
                    grand_root_dir, output_video_filename)

                create_video_from_image_paths(
                    all_project_images, output_video_path, fps)
            else:
                print(f"  项目 '{project_name}' 中没有收集到任何图片，不生成视频。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="遍历根目录下的每个子目录（项目），并将每个项目中数字序列文件夹内的图片序列合并成一个以项目名命名的 MP4 视频。"
    )
    parser.add_argument(
        "root_dir",
        type=str,
        help="包含多个项目子目录的根目录路径 (例如，包含 'bird_big', 'cat_small' 等文件夹的目录)。"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="输出视频的帧率 (FPS)。默认为 24。"
    )

    args = parser.parse_args()
    process_all_projects(args.root_dir, args.fps)
