import os
import shutil
import random
import argparse
from typing import List


def list_subdirectories(root: str, include_hidden: bool = False) -> List[str]:
    """列出根目录下的一级子文件夹名称（不含路径）。

    Args:
        root: 根目录路径
        include_hidden: 是否包含以点开头的隐藏目录
    """
    items = []
    try:
        for name in os.listdir(root):
            if not include_hidden and name.startswith('.'):
                continue
            full_path = os.path.join(root, name)
            if os.path.isdir(full_path):
                items.append(name)
    except FileNotFoundError:
        raise FileNotFoundError(f"输入目录不存在: {root}")
    return sorted(items)


def valid_ratio(value: str) -> float:
    """校验比例 (0,1)"""
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("比例必须是数字")
    if not (0 < f < 1):
        raise argparse.ArgumentTypeError("比例必须在 0 与 1 之间(不含)")
    return f


def move_subfolders(source: str, dest: str, ratio: float, seed: int = 42,
                    dry_run: bool = False, include_hidden: bool = False,
                    rename_on_conflict: bool = True) -> None:
    """按比例随机剪切(移动)一级子文件夹到目标目录。

    Args:
        source: 源根目录
        dest: 目标目录（不存在则创建）
        ratio: 需要移动的子文件夹比例 (0,1)
        seed: 随机种子
        dry_run: 仅显示计划，不执行移动
        include_hidden: 是否包含隐藏目录
        rename_on_conflict: 若目标已存在同名目录，是否自动重命名 (追加 _N)
    """
    if not os.path.isdir(source):
        raise ValueError(f"源目录不存在: {source}")

    os.makedirs(dest, exist_ok=True)

    subdirs = list_subdirectories(source, include_hidden=include_hidden)
    total = len(subdirs)
    if total == 0:
        print("源目录下没有子文件夹，无需操作。")
        return

    random.seed(seed)
    k = max(1, int(round(total * ratio)))  # 至少移动一个
    if k > total:
        k = total

    selected = random.sample(subdirs, k)

    print(f"源目录: {source}")
    print(f"目标目录: {dest}")
    print(f"发现子文件夹总数: {total}")
    print(f"比例: {ratio} => 计划移动: {k} 个 (随机)\n")

    print("将移动以下子文件夹:")
    for name in selected:
        print(f"  - {name}")

    if dry_run:
        print("\n干运行模式(dry-run)，未实际移动。")
        return

    moved = 0
    for name in selected:
        src_path = os.path.join(source, name)
        target_name = name
        dst_path = os.path.join(dest, target_name)

        if os.path.exists(dst_path):
            if rename_on_conflict:
                base = target_name
                idx = 1
                while os.path.exists(dst_path):
                    target_name = f"{base}_{idx}"
                    dst_path = os.path.join(dest, target_name)
                    idx += 1
                print(f"[重命名冲突] {name} -> {target_name}")
            else:
                print(f"[跳过] 目标已存在同名目录: {target_name}")
                continue

        try:
            shutil.move(src_path, dst_path)
            moved += 1
            print(f"[OK] {name} -> {target_name}")
        except Exception as e:
            print(f"[失败] {name}: {e}")

    print(f"\n完成: 成功移动 {moved}/{k} 个目录。剩余 {total - moved} 个留在源目录。")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="按比例随机剪切源目录下的子文件夹到目标目录")
    p.add_argument('-s', '--source', required=True, help='源根目录路径')
    p.add_argument('-d', '--dest', required=True, help='目标目录路径')
    p.add_argument('-r', '--ratio', type=valid_ratio, required=True,
                   help='剪切比例 (0-1，例如 0.3)')
    p.add_argument('--seed', type=int, default=42, help='随机种子 (默认 42)')
    p.add_argument('--include-hidden', action='store_true', help='包含以点开头的隐藏目录')
    p.add_argument('--no-rename-on-conflict', action='store_true',
                   help='冲突时不自动重命名而是跳过')
    p.add_argument('--dry-run', action='store_true', help='显示计划，不执行移动')
    return p


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    move_subfolders(
        source=args.source,
        dest=args.dest,
        ratio=args.ratio,
        seed=args.seed,
        dry_run=args.dry_run,
        include_hidden=args.include_hidden,
        rename_on_conflict=not args.no_rename_on_conflict,
    )


if __name__ == '__main__':
    main()
