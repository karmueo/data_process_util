import os


def list_files_with_ext(root, ext):
    result = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(ext):
                result.append(os.path.join(dirpath, f))
    return sorted(result)


def main(img_dir, label_dir, img_txt, label_txt):
    img_paths = list_files_with_ext(img_dir, '.jpg')
    label_paths = list_files_with_ext(label_dir, '.txt')

    with open(img_txt, 'w') as f:
        for p in img_paths:
            f.write(p + '\n')
    with open(label_txt, 'w') as f:
        for p in label_paths:
            f.write(p + '\n')

    img_names = set(os.path.splitext(
        os.path.basename(p))[0] for p in img_paths)
    label_names = set(os.path.splitext(os.path.basename(p))
                      [0] for p in label_paths)

    only_img = img_names - label_names
    only_label = label_names - img_names

    if only_img:
        print("仅图片有，无标注：")
        for n in sorted(only_img):
            print(n + ".jpg")
    if only_label:
        print("仅标注有，无图片：")
        for n in sorted(only_label):
            print(n + ".txt")
    if not only_img and not only_label:
        print("图片和标注一一对应。")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="比对图片和标注文件名是否一致，并输出不一致的文件。")
    parser.add_argument("img_dir", type=str, help="图片目录")
    parser.add_argument("label_dir", type=str, help="标注目录")
    parser.add_argument("--img_txt", type=str,
                        default="image_list.txt", help="图片路径输出txt")
    parser.add_argument("--label_txt", type=str,
                        default="label_list.txt", help="标注路径输出txt")
    args = parser.parse_args()
    main(args.img_dir, args.label_dir, args.img_txt, args.label_txt)
