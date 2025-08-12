import cv2
import os
import glob
import argparse
import math


def resize_with_padding(img, target_width, target_height):
    h, w = img.shape[:2]
    scale = min(target_width / w, target_height / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h))
    pad_w = target_width - new_w
    pad_h = target_height - new_h
    top = pad_h // 2
    bottom = pad_h - top
    left = pad_w // 2
    right = pad_w - left
    color = [0, 0, 0]
    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return padded


def resize_stretch(img, target_width, target_height):
    """不保持比例，直接拉伸到指定尺寸"""
    return cv2.resize(img, (target_width, target_height))


def main(folder, output, fps, width, height, chunk_size, resize_mode):
    # 获取所有帧图片，按帧号排序
    image_files = glob.glob(os.path.join(folder, "*.jpg"))
    image_files.sort(key=lambda x: int(
        os.path.splitext(os.path.basename(x))[0]))
    if not image_files:
        print("未找到图片")
        return

    total_images = len(image_files)
    num_chunks = math.ceil(total_images / chunk_size)

    for chunk_idx in range(num_chunks):
        start = chunk_idx * chunk_size
        end = min((chunk_idx + 1) * chunk_size, total_images)
        chunk_files = image_files[start:end]
        if not chunk_files:
            continue

        # 生成不冲突的输出文件名
        if num_chunks == 1:
            out_name = output
        else:
            base, ext = os.path.splitext(output)
            out_name = f"{base}_{chunk_idx+1}{ext}"

        # 读取第一帧，确定视频参数
        frame = cv2.imread(chunk_files[0])
        if frame is None:
            print(f"无法读取图片: {chunk_files[0]}")
            continue

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(out_name, fourcc, fps, (width, height))

        for img_path in chunk_files:
            img = cv2.imread(img_path)
            if img is None:
                print(f"跳过无法读取的图片: {img_path}")
                continue
            if resize_mode == 'stretch':
                frame = resize_stretch(img, width, height)
            else:
                frame = resize_with_padding(img, width, height)
            video_writer.write(frame)

        video_writer.release()
        print(f"视频已保存到: {out_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将图片序列合成为视频")
    parser.add_argument("--folder", required=True, help="图片文件夹路径")
    parser.add_argument("--output", default="output.mp4", help="输出视频文件名")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--width", type=int, default=224, help="目标视频宽度")
    parser.add_argument("--height", type=int, default=224, help="目标视频高度")
    parser.add_argument("--chunk", type=int, default=90, help="每段视频包含的图片数量")
    parser.add_argument(
        "--resize_mode",
        choices=['pad', 'stretch'],
        default='pad',
        help="resize 方式: pad=保持比例加黑边, stretch=直接拉伸 (默认 pad)"
    )
    args = parser.parse_args()
    main(args.folder, args.output, args.fps,
         args.width, args.height, args.chunk, args.resize_mode)
