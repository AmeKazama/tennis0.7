"""
MoveNet Thunder 模型加载和推理模块（TFLite 版本）
完全兼容原项目 extract_human_pose.py 的加载方式
"""

import numpy as np
import cv2

# 延迟导入 TensorFlow，避免启动时报错
_tf = None

def get_tf():
    """延迟加载 TensorFlow"""
    global _tf
    if _tf is None:
        import tensorflow as tf
        _tf = tf
    return _tf


# COCO-17 关键点索引
KP_NOSE = 0
KP_LEFT_SHOULDER = 5
KP_RIGHT_SHOULDER = 6
KP_LEFT_ELBOW = 7
KP_RIGHT_ELBOW = 8
KP_LEFT_WRIST = 9
KP_RIGHT_WRIST = 10
KP_LEFT_HIP = 11
KP_RIGHT_HIP = 12
KP_LEFT_KNEE = 13
KP_RIGHT_KNEE = 14
KP_LEFT_ANKLE = 15
KP_RIGHT_ANKLE = 16


class MoveNetThunder:
    """MoveNet Thunder 模型包装器（TFLite 版本）"""

    def __init__(self, model_path="services/movenet.tflite", num_threads=1):
        """
        初始化 MoveNet Thunder（使用 TFLite）
        完全按照原项目 extract_human_pose.py 的方式

        Args:
            model_path: TFLite 模型路径，默认 "movenet.tflite"
            num_threads: 线程数，默认 1
        """
        import os

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"未找到 MoveNet TFLite 模型: {model_path}\n"
                f"请确保 movenet.tflite 在当前目录。"
            )

        print(f"[info] 加载 TFLite 模型: {model_path}")

        # 加载 TensorFlow
        tf = get_tf()

        # 按照原项目的方式加载（extract_human_pose.py 第 199 行）
        self.interpreter = tf.lite.Interpreter(
            model_path=model_path,
            num_threads=num_threads
        )
        self.interpreter.allocate_tensors()

        # 获取输入输出详情
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # 获取输入尺寸
        self.input_size = self.input_details[0]['shape'][1]

        print(f"[info] 模型输入尺寸: {self.input_size}x{self.input_size}")
        print(f"[info] TensorFlow 版本: {tf.__version__ if hasattr(tf, '__version__') else 'unknown'}")

    def infer(self, frame):
        """
        对单帧图像进行姿态估计（按照原项目方式）

        Args:
            frame: OpenCV 读取的图像 (H, W, 3) BGR uint8

        Returns:
            keypoints: (17, 3) ndarray，每行为 (y_norm, x_norm, score)
        """
        tf = get_tf()

        # 转换为 RGB（原项目不需要这步，直接用 BGR）
        # 但为了兼容性保留
        img = frame.copy()

        # 按照原项目的方式：tf.image.resize_with_pad
        # (extract_human_pose.py 第 210 行)
        img = tf.image.resize_with_pad(
            np.expand_dims(img, axis=0),
            self.input_size,
            self.input_size
        )
        input_image = tf.cast(img, dtype=tf.uint8)

        # 设置输入张量（第 219 行）
        self.interpreter.set_tensor(
            self.input_details[0]["index"],
            np.array(input_image)
        )

        # 运行推理（第 220 行）
        self.interpreter.invoke()

        # 获取输出（第 221-223 行）
        keypoints_with_scores = self.interpreter.get_tensor(
            self.output_details[0]["index"]
        )

        # 提取为 (17, 3) 格式
        # 原项目格式：[1, 1, 17, 3]
        keypoints = keypoints_with_scores[0, 0, :, :]

        return keypoints


def compute_joint_angles(keypoints):
    """
    从 MoveNet 关键点计算 8 个关节角度

    Args:
        keypoints: (17, 3) ndarray from MoveNet, [y_norm, x_norm, score]

    Returns:
        angles: (8,) ndarray of joint angles in degrees
            [right_shoulder, right_elbow, right_hip, right_knee,
             left_shoulder, left_elbow, left_hip, left_knee]
    """
    def compute_angle(p1, p2, p3):
        """计算三点夹角，p2 为顶点"""
        v1 = p1 - p2
        v2 = p3 - p2
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return np.nan
        cos_angle = np.dot(v1, v2) / (norm1 * norm2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)
        return np.degrees(angle_rad)

    # 提取关键点 (只用 xy，忽略 score)
    kp_xy = keypoints[:, :2]

    # 右侧关节角度
    right_shoulder_angle = compute_angle(
        kp_xy[KP_RIGHT_ELBOW],
        kp_xy[KP_RIGHT_SHOULDER],
        kp_xy[KP_RIGHT_HIP]
    )
    right_elbow_angle = compute_angle(
        kp_xy[KP_RIGHT_SHOULDER],
        kp_xy[KP_RIGHT_ELBOW],
        kp_xy[KP_RIGHT_WRIST]
    )
    right_hip_angle = compute_angle(
        kp_xy[KP_RIGHT_SHOULDER],
        kp_xy[KP_RIGHT_HIP],
        kp_xy[KP_RIGHT_KNEE]
    )
    right_knee_angle = compute_angle(
        kp_xy[KP_RIGHT_HIP],
        kp_xy[KP_RIGHT_KNEE],
        kp_xy[KP_RIGHT_ANKLE]
    )

    # 左侧关节角度
    left_shoulder_angle = compute_angle(
        kp_xy[KP_LEFT_ELBOW],
        kp_xy[KP_LEFT_SHOULDER],
        kp_xy[KP_LEFT_HIP]
    )
    left_elbow_angle = compute_angle(
        kp_xy[KP_LEFT_SHOULDER],
        kp_xy[KP_LEFT_ELBOW],
        kp_xy[KP_LEFT_WRIST]
    )
    left_hip_angle = compute_angle(
        kp_xy[KP_LEFT_SHOULDER],
        kp_xy[KP_LEFT_HIP],
        kp_xy[KP_LEFT_KNEE]
    )
    left_knee_angle = compute_angle(
        kp_xy[KP_LEFT_HIP],
        kp_xy[KP_LEFT_KNEE],
        kp_xy[KP_LEFT_ANKLE]
    )

    return np.array([
        right_shoulder_angle,
        right_elbow_angle,
        right_hip_angle,
        right_knee_angle,
        left_shoulder_angle,
        left_elbow_angle,
        left_hip_angle,
        left_knee_angle
    ], dtype=np.float64)


def dtw_compare(user_angles, std_angles, shot_type="unknown"):
    """
    使用动态时间规整比较两个角度序列 (完全照抄 extract_frame_samples.py 的实现)

    根据 shot_type 选择关注的关节:
    - forehand/serve: 只看右侧 (index 0-3)
    - backhand: 只看左侧 (index 4-7)
    - unknown: 看全部 8 个关节

    参数:
        user_angles: 用户角度数组，shape (M, 8)
        std_angles:  标准角度数组，shape (N, 8)
        shot_type: "forehand" | "backhand" | "serve" | "unknown"

    返回:
        dict:
            distance: 归一化的 DTW 距离 (distance / path_length) ← 关键!
            path: 对齐路径 [(i,j), ...]
            per_joint_error: 每个关节的平均绝对误差
            per_joint_signed_error: 每个关节的平均带符号误差
            active_joints: 参与对比的关节索引列表
            alignment_info: {user_frames, standard_frames, path_length}
    """
    import numpy as np

    # 尝试使用 fastdtw (更快)
    try:
        from fastdtw import fastdtw
        use_fastdtw = True
    except ImportError:
        use_fastdtw = False

    # 确定关注的关节 (与 extract_frame_samples.py 完全一致)
    if shot_type in ["forehand", "serve"]:
        active_joints = [0, 1, 2, 3]  # 右侧: 右肩、右肘、右髋、右膝
    elif shot_type == "backhand":
        active_joints = [4, 5, 6, 7]  # 左侧: 左肩、左肘、左髋、左膝
    else:
        active_joints = list(range(8))  # 全部

    if use_fastdtw:
        # 使用 fastdtw
        def angle_dist(a, b):
            # 只计算 active_joints 的距离
            valid = np.isfinite(a) & np.isfinite(b)
            # 进一步限制到 active_joints
            active_mask = np.zeros(8, dtype=bool)
            active_mask[active_joints] = True
            valid = valid & active_mask

            if not valid.any():
                return 100.0  # large penalty
            diff = a[valid] - b[valid]
            return float(np.sqrt((diff ** 2).mean()))

        distance, path = fastdtw(user_angles, std_angles, dist=angle_dist)
        normalized_dist = distance / len(path)  # ← 关键: 归一化!
    else:
        # 降级到 naive DTW
        M, N = len(user_angles), len(std_angles)
        cost = np.full((M + 1, N + 1), np.inf)
        cost[0, 0] = 0

        for i in range(1, M + 1):
            for j in range(1, N + 1):
                valid = np.isfinite(user_angles[i-1]) & np.isfinite(std_angles[j-1])
                active_mask = np.zeros(8, dtype=bool)
                active_mask[active_joints] = True
                valid = valid & active_mask

                if not valid.any():
                    d = 100.0
                else:
                    diff = user_angles[i-1][valid] - std_angles[j-1][valid]
                    d = float(np.sqrt((diff ** 2).mean()))
                cost[i, j] = d + min(cost[i-1, j], cost[i, j-1], cost[i-1, j-1])

        normalized_dist = cost[M, N] / max(M, N)  # ← 关键: 归一化!
        path = []  # naive 版本不返回详细路径

    # 计算每个关节的平均偏差 (绝对值和带符号)
    per_joint_error = np.zeros(8)
    per_joint_signed_error = np.zeros(8)
    per_joint_count = np.zeros(8)

    if path:
        # 有路径信息,沿路径统计
        for i, j in path:
            for k in active_joints:
                if np.isfinite(user_angles[i, k]) and np.isfinite(std_angles[j, k]):
                    diff = user_angles[i, k] - std_angles[j, k]
                    per_joint_error[k] += abs(diff)
                    per_joint_signed_error[k] += diff
                    per_joint_count[k] += 1
    else:
        # 无路径,假设对角对齐
        for i in range(min(len(user_angles), len(std_angles))):
            for k in active_joints:
                if np.isfinite(user_angles[i, k]) and np.isfinite(std_angles[i, k]):
                    diff = user_angles[i, k] - std_angles[i, k]
                    per_joint_error[k] += abs(diff)
                    per_joint_signed_error[k] += diff
                    per_joint_count[k] += 1

    # 平均
    for k in range(8):
        if per_joint_count[k] > 0:
            per_joint_error[k] /= per_joint_count[k]
            per_joint_signed_error[k] /= per_joint_count[k]
        else:
            per_joint_error[k] = np.nan
            per_joint_signed_error[k] = np.nan

    return {
        "distance": normalized_dist,  # ← 归一化距离,范围 0-100
        "path": path if path else [],
        "per_joint_error": per_joint_error.tolist(),
        "per_joint_signed_error": per_joint_signed_error.tolist(),
        "active_joints": active_joints,
        "alignment_info": {
            "user_frames": len(user_angles),
            "standard_frames": len(std_angles),
            "path_length": len(path) if path else 0
        }
    }

def naive_dtw(seq1, seq2, shot_type="unknown"):
    """简化版 DTW（当 fastdtw 不可用时）"""
    if shot_type in ["forehand", "serve"]:
        active_joints = [0, 1, 2, 3]
    elif shot_type == "backhand":
        active_joints = [4, 5, 6, 7]
    else:
        active_joints = list(range(8))

    M, N = len(seq1), len(seq2)
    cost = np.full((M + 1, N + 1), np.inf)
    cost[0, 0] = 0

    for i in range(1, M + 1):
        for j in range(1, N + 1):
            valid = np.isfinite(seq1[i-1]) & np.isfinite(seq2[j-1])
            active_mask = np.zeros(8, dtype=bool)
            active_mask[active_joints] = True
            valid = valid & active_mask

            if not valid.any():
                d = 100.0
            else:
                diff = seq1[i-1][valid] - seq2[j-1][valid]
                d = float(np.sqrt((diff ** 2).mean()))
            cost[i, j] = d + min(cost[i-1, j], cost[i, j-1], cost[i-1, j-1])

    # 简单估算偏差
    per_joint_error = np.zeros(8)
    per_joint_signed_error = np.zeros(8)
    count = np.zeros(8)

    for i in range(min(M, N)):
        for k in active_joints:
            if np.isfinite(seq1[i, k]) and np.isfinite(seq2[i, k]):
                diff = seq1[i, k] - seq2[i, k]
                per_joint_error[k] += abs(diff)
                per_joint_signed_error[k] += diff
                count[k] += 1

    for k in active_joints:
        if count[k] > 0:
            per_joint_error[k] /= count[k]
            per_joint_signed_error[k] /= count[k]
        else:
            per_joint_error[k] = np.nan
            per_joint_signed_error[k] = np.nan

    return {
        "distance": cost[M, N] / max(M, N),
        "path": [],
        "per_joint_error": per_joint_error.tolist(),
        "per_joint_signed_error": per_joint_signed_error.tolist(),
        "active_joints": active_joints,
        "alignment_info": {
            "user_frames": M,
            "standard_frames": N,
            "path_length": 0
        }
    }