"""
输入视频路径和算法，根据算法分别使用梯度能量和 拉普拉斯方差对视频每一帧计算对应的清晰度指标，并统计总值和均值
"""
import cv2
import numpy as np
from tqdm import tqdm

def gradient_energy(img):
    """计算梯度能量清晰度指标"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    dy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return np.sum(dx**2 + dy**2)

def laplacian_variance(img):
    """计算拉普拉斯方差清晰度指标"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return lap.var()

def analyze_video(video_path, method='laplacian'):
    """
    分析视频清晰度
    :param video_path: 视频文件路径
    :param method: 'gradient' 或 'laplacian'
    :return: (所有帧的得分列表, 总分, 平均分)
    """
    # 验证算法选择
    if method not in ['gradient', 'laplacian']:
        raise ValueError("Method must be 'gradient' or 'laplacian'")
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video Info: {total_frames} frames, {fps:.2f} FPS, {width}x{height}")
    
    # 选择算法
    if method == 'gradient':
        metric_func = gradient_energy
        print("Using Gradient Energy method")
    else:
        metric_func = laplacian_variance
        print("Using Laplacian Variance method")
    
    # 逐帧处理
    scores = []
    progress_bar = tqdm(total=total_frames, desc="Processing frames")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        score = metric_func(frame)
        scores.append(score)
        progress_bar.update(1)
    
    cap.release()
    progress_bar.close()
    
    # 计算统计值
    total_score = np.sum(scores)
    mean_score = np.mean(scores)
    
    return scores, total_score, mean_score

if __name__ == "__main__":
    import argparse
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Video Sharpness Analysis')
    parser.add_argument('video_path', help='Path to the video file')
    parser.add_argument('--method', choices=['gradient', 'laplacian'], 
                       default='laplacian', help='Sharpness calculation method')
    args = parser.parse_args()
    
    # 执行分析
    scores, total, mean = analyze_video(args.video_path, args.method)
    
    # 打印结果
    print("\nResults:")
    print(f"Total sharpness score: {total:.2f}")
    print(f"Mean sharpness score: {mean:.2f}")
    print(f"Frame count: {len(scores)}")
    
    # 可选：保存结果到CSV
    save_csv = input("Save results to CSV? (y/n): ").lower() == 'y'
    if save_csv:
        import pandas as pd
        df = pd.DataFrame({
            'frame_num': range(1, len(scores)+1),
            'sharpness_score': scores
        })
        csv_path = args.video_path + '_sharpness.csv'
        df.to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")