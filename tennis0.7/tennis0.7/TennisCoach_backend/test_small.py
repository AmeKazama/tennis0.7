import cv2
import numpy as np
from extract_human_pose import HumanPoseExtractor

# 读取一帧
cap = cv2.VideoCapture("E:/Desktop/WeChat_20260506133038.mp4")  # 换成你的视频路径
ret, frame = cap.read()
cap.release()

if not ret:
    print("无法读取视频")
    exit()

# 初始化
print("初始化 HumanPoseExtractor...")
human_pose_extractor = HumanPoseExtractor(frame.shape)

# 提取姿态
print("提取姿态...")
human_pose_extractor.extract(frame)

# 打印关键点
kps = human_pose_extractor.keypoints_with_scores.reshape(17, 3)
print(f"关键点 shape: {kps.shape}")
print(f"关键点值范围: [{kps[:, 0].min():.3f}, {kps[:, 0].max():.3f}]")
print(f"前5个关键点 (y, x, score):")
for i in range(5):
    print(f"  {i}: ({kps[i, 0]:.3f}, {kps[i, 1]:.3f}, {kps[i, 2]:.3f})")

# discard 后
human_pose_extractor.discard(["left_eye", "right_eye", "left_ear", "right_ear"])
kps2 = human_pose_extractor.keypoints_with_scores.reshape(17, 3)
print(f"\ndiscard 后，有效关键点数量: {(kps2[:, 2] > 0).sum()}")

# 构建 features
features = kps2[kps2[:, 2] > 0][:, 0:2].reshape(1, 13 * 2)
print(f"\nfeatures shape: {features.shape}")
print(f"features 值范围: [{features.min():.4f}, {features.max():.4f}]")
print(f"features 前10个值: {features[0, :10]}")