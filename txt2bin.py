import numpy as np

def txt_to_bin(txt_path, bin_path, dtype=np.float32):
    """
    将每行一个数据的txt文件转换为二进制bin文件
    
    参数:
        txt_path (str): 输入txt文件路径
        bin_path (str): 输出bin文件路径
        dtype (np.dtype): 数据类型，默认为np.float32
    """
    # 读取txt文件，逐行解析为列表
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    
    # 去除空行和换行符，转换为目标数据类型
    data = []
    for line in lines:
        line = line.strip()  # 去除首尾空格/换行
        if line:  # 跳过空行
            try:
                value = dtype(line)  # 转换为指定类型（如float32）
                data.append(value)
            except ValueError as e:
                raise ValueError(f"无法将行 '{line}' 转换为 {dtype}: {e}")
    
    # 转为NumPy数组并保存为bin文件
    np.array(data, dtype=dtype).tofile(bin_path)
    print(f"转换完成: {txt_path} -> {bin_path} (数据类型: {dtype})")

# 示例用法
if __name__ == "__main__":
    input_txt = "/home/tl/work/mmaction2/mmaction/output.txt"  # 输入txt文件路径
    output_bin = "/home/tl/work/mmaction2/mmaction/output.bin"  # 输出bin文件路径
    
    # 可选：指定数据类型（np.float32或np.int32等）
    txt_to_bin(input_txt, output_bin, dtype=np.float32)