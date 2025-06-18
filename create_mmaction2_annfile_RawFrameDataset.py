import os
import shutil  # 用于在测试中清理dummy数据


def count_frames_in_directory(directory_path: str) -> int:
    """
    计算指定目录中有效帧的数量。
    有效帧是指以数字命名并以.jpg结尾的图片文件 (例如 '0.jpg', '1.jpg', ...)。

    参数:
        directory_path (str): 要检查的目录路径。

    返回:
        int: 目录中有效帧的数量。如果目录不存在或无法访问，则返回0。
    """
    if not os.path.isdir(directory_path):
        return 0
    try:
        image_files = [
            f for f in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, f))
            and f.lower().endswith('.jpg')
            and f[:-4].isdigit()  # 检查文件名部分（不含.jpg后缀）是否为纯数字
        ]
        return len(image_files)
    except OSError:  # 例如，权限不足等问题
        print(f"警告：无法访问目录 '{directory_path}' 中的文件列表。")
        return 0


def generate_rawframes_annotation(root_directory: str, output_filename: str = "annotations.txt"):
    """
    生成RawFrameDataset格式的原始帧注释文件。

    脚本会扫描指定的根目录，该目录应按以下结构组织：
    根目录/
    ├── 类别A/
    │   ├── 视频帧目录1/  (直接存放帧图片)
    │   │   ├── 0.jpg
    │   │   └── ...
    │   └── 源视频ID_X/ (代表某个源视频)
    │       ├── 视频片段帧目录_A/ (存放该源视频的某个片段的帧)
    │       │   ├── 0.jpg
    │       │   └── ...
    │       └── 视频片段帧目录_B/
    │           └── ...
    ├── 类别B/
    │   └── ...

    参数:
        root_directory (str): 包含类别文件夹的根目录路径。
        output_filename (str): 要生成的注释文件的名称。
                               该文件将保存在 `root_directory` 内。
    """
    annotations = []  # 存储最终的注释行
    class_to_label = {}  # 映射类别名称到整数标签
    current_label_idx = 0  # 标签从1开始，与示例一致

    if not os.path.isdir(root_directory):
        print(f"错误：根目录 '{root_directory}' 未找到。")
        return

    print(f"开始扫描根目录: {root_directory}")

    # 获取根目录下的所有项，并筛选出作为类别文件夹的目录，按名称排序以确保标签分配的一致性
    class_names = sorted(
        [d for d in os.listdir(root_directory) if os.path.isdir(
            os.path.join(root_directory, d))]
    )

    if not class_names:
        print(f"在 '{root_directory}' 中未找到任何类别文件夹。")
        return

    for class_name in class_names:
        # 为新的类别分配标签
        if class_name not in class_to_label:
            class_to_label[class_name] = current_label_idx
            current_label_idx += 1
        label = class_to_label[class_name]

        class_path = os.path.join(root_directory, class_name)  # 当前类别的完整路径

        # 获取类别文件夹下的所有子项，按名称排序
        # 这些子项可能是直接的视频帧目录，也可能是源视频ID目录
        level1_items_names = sorted(
            [d for d in os.listdir(class_path) if os.path.isdir(
                os.path.join(class_path, d))]
        )

        for item1_name in level1_items_names:
            path_item1 = os.path.join(class_path, item1_name)  # 第一层子目录的完整路径

            # 尝试将 path_item1 视为直接的视频帧目录
            frame_count_item1 = count_frames_in_directory(path_item1)

            if frame_count_item1 > 0:
                # 情况1: path_item1 是一个直接的视频帧目录
                # 例如: root/类别/视频帧目录/0.jpg
                relative_frame_dir = os.path.join(
                    class_name, item1_name).replace(os.sep, '/')
                annotations.append(
                    f"{relative_frame_dir} {frame_count_item1} {label}")
            else:
                # 情况2: path_item1 不是直接的视频帧目录 (frame_count_item1 为 0)
                # 假设 item1_name 是一个源视频ID目录，需要检查其下的子目录作为视频片段帧目录
                # 例如: root/类别/源视频ID/视频片段帧目录/0.jpg

                # 获取 path_item1 下的所有子目录（这些应该是视频片段帧目录）
                level2_items_names = sorted(
                    [d for d in os.listdir(path_item1) if os.path.isdir(
                        os.path.join(path_item1, d))]
                )

                if not level2_items_names:  # 如果 item1 没有帧也没有子目录
                    print(
                        f"信息：目录 '{path_item1}' 既不直接包含帧图片，也没有包含视频片段的子目录。可能是一个空的源视频ID目录或不符合预期的结构。")
                    continue  # 继续处理下一个 item1_name

                for item2_name in level2_items_names:
                    path_item2 = os.path.join(
                        path_item1, item2_name)  # 第二层子目录（视频片段帧目录）的完整路径

                    frame_count_item2 = count_frames_in_directory(path_item2)

                    if frame_count_item2 > 0:
                        relative_frame_dir = os.path.join(
                            class_name, item1_name, item2_name).replace(os.sep, '/')
                        annotations.append(
                            f"{relative_frame_dir} {frame_count_item2} {label}")
                    else:
                        # 如果这个第二层子目录也没有帧，打印一个提示信息
                        print(f"信息：在预期的视频片段帧目录 '{path_item2}' 中未找到有效的帧图片。")

    if not annotations:
        print("未找到任何有效的视频帧数据来生成注释。")
        return

    # 将注释写入到输出文件中（保存在根目录内）
    output_file_path = os.path.join(root_directory, output_filename)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:  # 使用utf-8编码
            for line in annotations:
                f.write(line + '\n')

        print(f"\n注释文件 '{output_file_path}' 已成功生成，包含 {len(annotations)} 条记录。")
        print("使用的类别到标签的映射关系如下:")
        for cls, lbl in class_to_label.items():
            print(f"- 类别 '{cls}': 标签 {lbl}")
    except IOError as e:
        print(f"错误：无法将注释文件写入到 '{output_file_path}'。错误详情: {e}")


if __name__ == '__main__':
    # === 脚本主要执行部分 ===
    # 1. 定义你的数据集的根目录
    #    对于此示例，我们使用上面创建的模拟数据路径。
    #    在实际使用中，请将此路径替换为你的数据集的实际根目录。
    #    例如: my_dataset_root_dir = "/path/to/your/frames_dataset"
    my_dataset_root_directory = "/home/tl/data/datasets/mmaction2/expand_x2_60/keep_ratio/val_test"

    # 2. 定义你希望生成的注释文件的名称。
    #    此文件将创建在 'my_dataset_root_directory' 内部。
    annotation_file_name = "110_video_train_annotation_file.txt"

    # 3. 生成注释文件
    generate_rawframes_annotation(
        my_dataset_root_directory, annotation_file_name)

    # --- 验证输出 (可选：仅用于测试目的) ---
    expected_output_path = os.path.join(
        my_dataset_root_directory, annotation_file_name)
    if os.path.exists(expected_output_path):
        print(f"\n已生成的注释文件 ('{expected_output_path}') 内容如下:")
        with open(expected_output_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"错误：注释文件 '{expected_output_path}' 未能成功创建。")

    # --- 清理模拟数据 (可选) ---
    # print(f"\n正在清理模拟数据目录: '{my_dataset_root_directory}'")
    # shutil.rmtree(my_dataset_root_directory)
    # print("模拟数据已清理。")
