"""
With this script, you can provide a video and your RNN model (e.g tennis_rnn.h5)
and see a shot classification/detection. For this, we feed our neural network with
a sliding window of 30 frame (1 second) and classify the shot.

修改说明 (TF 2.16 + Keras 3.x 兼容):
  - 移除 `from tensorflow import keras`，改用 `import keras`
  - GPU memory growth 改用新 API
  - 模型加载改用 keras.saving.load_model
  - 输出结果改为显示窗口（原版写图片文件，改回实时显示）
  - ShotCounter 加入延迟确认机制，serve 可覆盖 forehand

新增功能:
  - 每次击球确认后，保存整个击球窗口的骨架数据到 CSV
  - CSV 包含归一化 xy 坐标、置信度 score、以及主要关节角度
  - 关节角度用于后续与标准库运动员动作对比
"""

import time
import math
from argparse import ArgumentParser
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
import keras
import numpy as np
import pandas as pd
import cv2
from movenet_model import compute_joint_angles, dtw_compare
import json
from extract_human_pose import HumanPoseExtractor

physical_devices = tf.config.list_physical_devices("GPU")
print(f"GPU 设备: {physical_devices}")
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
print(f"可用 GPU 数量: {len(physical_devices)}")


# ─────────────────────────────────────────────
# MoveNet 关键点索引（Thunder/Lightning 17点）
# 经过 discard(['left_eye','right_eye','left_ear','right_ear']) 后
# 剩余13点，原始索引如下（保留用于角度计算索引映射）
# ─────────────────────────────────────────────
# 原始17点索引:
#  0:nose  1:left_eye  2:right_eye  3:left_ear  4:right_ear
#  5:left_shoulder   6:right_shoulder
#  7:left_elbow      8:right_elbow
#  9:left_wrist     10:right_wrist
# 11:left_hip       12:right_hip
# 13:left_knee      14:right_knee
# 15:left_ankle     16:right_ankle
#
# discard 后剩余13点，新索引顺序:
#  0:nose
#  1:left_shoulder   2:right_shoulder
#  3:left_elbow      4:right_elbow
#  5:left_wrist      6:right_wrist
#  7:left_hip        8:right_hip
#  9:left_knee      10:right_knee
# 11:left_ankle     12:right_ankle

KP_NAMES = [
    "nose",
    "left_shoulder", "right_shoulder",
    "left_elbow",    "right_elbow",
    "left_wrist",    "right_wrist",
    "left_hip",      "right_hip",
    "left_knee",     "right_knee",
    "left_ankle",    "right_ankle",
]

# 角度定义: (顶点索引, 边点A索引, 边点B索引, 角度名称)
# 角度 = 向量(顶点→A) 与 向量(顶点→B) 的夹角
ANGLE_DEFS = [
    (3,  1,  5,  "left_elbow_angle"),    # 左肘：左肩-左肘-左腕
    (4,  2,  6,  "right_elbow_angle"),   # 右肘：右肩-右肘-右腕
    (1,  7,  3,  "left_shoulder_angle"), # 左肩：左髋-左肩-左肘
    (2,  8,  4,  "right_shoulder_angle"),# 右肩：右髋-右肩-右肘
    (7,  1,  9,  "left_hip_angle"),      # 左髋：左肩-左髋-左膝
    (8,  2, 10,  "right_hip_angle"),     # 右髋：右肩-右髋-右膝
    (9,  7, 11,  "left_knee_angle"),     # 左膝：左髋-左膝-左踝
    (10, 8, 12,  "right_knee_angle"),    # 右膝：右髋-右膝-右踝
]

# CSV 列名
_kp_cols = []
for name in KP_NAMES:
    _kp_cols += [f"{name}_x", f"{name}_y", f"{name}_score"]
_angle_cols = [d[3] for d in ANGLE_DEFS]

CSV_COLUMNS = (
    ["shot_id", "shot_type", "frame_id", "frame_in_window", "peak_frame_id",
     "prob_backhand", "prob_forehand", "prob_neutral", "prob_serve"]
    + _kp_cols
    + _angle_cols
)


def _angle_between(kps, vertex_idx, a_idx, b_idx):
    """
    计算三点夹角（度）。
    kps: shape (13, 3)，列为 [y_norm, x_norm, score]
    返回 float 角度，若任一点 score < 0.2 则返回 NaN。
    注意：MoveNet 输出 [y, x, score]，这里做了正确的坐标提取。
    """
    pts = [vertex_idx, a_idx, b_idx]
    if any(kps[i, 2] < 0.2 for i in pts):
        return float("nan")
    # MoveNet: col0=y, col1=x
    v = np.array([kps[vertex_idx, 1], kps[vertex_idx, 0]])
    a = np.array([kps[a_idx, 1],      kps[a_idx, 0]])
    b = np.array([kps[b_idx, 1],      kps[b_idx, 0]])
    va = a - v
    vb = b - v
    cos_val = np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-8)
    cos_val = float(np.clip(cos_val, -1.0, 1.0))
    return math.degrees(math.acos(cos_val))


def keypoints_to_row(kps_17x3, probs):
    """
    将原始 17x3 关键点（discard 前）转换为 CSV 一行所需的字段字典。
    discard 顺序：去掉 index 1,2,3,4（left_eye,right_eye,left_ear,right_ear）
    剩余13点按 KP_NAMES 顺序排列。
    """
    # discard eyes & ears → 剩13点，shape (13,3)
    keep_indices = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    kps = kps_17x3[keep_indices]  # (13, 3)

    row = {}
    # 关键点坐标与置信度
    for i, name in enumerate(KP_NAMES):
        row[f"{name}_y"]     = round(float(kps[i, 0]), 5)
        row[f"{name}_x"]     = round(float(kps[i, 1]), 5)
        row[f"{name}_score"] = round(float(kps[i, 2]), 4)

    # 关节角度
    for vertex_idx, a_idx, b_idx, angle_name in ANGLE_DEFS:
        row[angle_name] = round(_angle_between(kps, vertex_idx, a_idx, b_idx), 2)

    # probs（顺序：backhand, forehand, neutral, serve）
    row["prob_backhand"] = round(float(probs[0]), 4)
    row["prob_forehand"] = round(float(probs[1]), 4)
    row["prob_neutral"]  = round(float(probs[2]), 4)
    row["prob_serve"]    = round(float(probs[3]), 4)

    return row


class SkeletonRecorder:
    """
    击球骨架记录器（概率曲线自动定位峰值窗口版）。

    设计思路
    ─────────
    RNN trigger 帧只是"概率第一次超阈值"，不是峰值；confirm 帧更晚。
    因此不用固定 BEFORE/AFTER，而是：
      1. 长缓冲持续缓存 (frame_id, kps_17x3, probs)，不缓存视频帧（省内存）。
      2. confirm 后再收集 AFTER_CONFIRM 帧，确保 follow-through 完整入缓冲。
      3. flush 时用概率曲线找峰值，向两侧扩展到阈值以下 + EDGE_BUFFER。
      4. CSV：直接从缓冲写出裁剪好的骨架序列。
      5. 视频片段：用 cv2.VideoCapture seek 到对应帧段重新读取写出，
         完全不占额外内存，且写入的是带骨架标注的渲染帧（复用 annotate_frame）。

    输出文件（同名对：.csv + .mp4）：
      shot_001_forehand_frame420.csv
      shot_001_forehand_frame420.mp4
    """

    BUFFER_SIZE   = 200    # 骨架缓冲帧数（~6.7s@30fps），发球动作长，需更大缓冲
    SHOT_PROB_IDX = {"backhand": 0, "forehand": 1, "neutral": 2, "serve": 3}

    # 各击球类型的窗口参数
    # prob_threshold : 概率低于此值视为动作边界
    # edge_before    : 概率边界外再向前多保留帧（引拍预备动作）
    # edge_after     : 概率边界外再向后多保留帧（随挥完整度）
    # after_confirm  : confirm 后继续收集帧数（确保后半段完整入缓冲）
    WINDOW_PARAMS = {
        "forehand": dict(prob_threshold=0.35, edge_before=20, edge_after=0,  after_confirm=15),
        "backhand": dict(prob_threshold=0.35, edge_before=20, edge_after=0,  after_confirm=15),
        "serve":    dict(prob_threshold=0.25, edge_before=30, edge_after=30, after_confirm=55),
        "_default": dict(prob_threshold=0.35, edge_before=12, edge_after=10, after_confirm=30),
    }

    def __init__(self, output_dir="skeleton_data",
                 save_video=False, video_path=None, video_fps=30.0):
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir  = output_dir
        self.save_video  = save_video
        self.video_path  = video_path   # 原始视频路径，用于 seek 重读
        self.video_fps   = video_fps
        self.shot_counter = 0

        # 骨架缓冲：(frame_id, kps_17x3, probs)  — 不存像素
        self._buffer: list = []

        self._collecting            = False
        self._collect_shot_type     = None
        self._collect_trigger_frame = None
        self._frames_after_left     = 0

        # 供视频片段渲染时复用的标注函数（由主循环注入）
        self._annotate_fn = None   # callable(frame, frame_id, probs) -> annotated_frame

        self._all_csv_path   = os.path.join(output_dir, "all_shots.csv")
        self._written_header = False

    def set_annotate_fn(self, fn):
        """注入帧标注函数，签名：fn(bgr_frame, frame_id, probs) -> bgr_frame"""
        self._annotate_fn = fn

    # ── 每帧调用 ─────────────────────────────────────────────────
    def update(self, frame_id: int, kps_17x3: np.ndarray, probs: np.ndarray):
        self._buffer.append((frame_id, kps_17x3.copy(), probs.copy()))
        if len(self._buffer) > self.BUFFER_SIZE:
            self._buffer.pop(0)

        if self._collecting:
            self._frames_after_left -= 1
            if self._frames_after_left <= 0:
                self._flush()

    # ── 击球确认回调 ──────────────────────────────────────────────
    def on_shot_confirmed(self, shot_type: str, trigger_frame_id: int):
        if self._collecting:
            self._flush()
        p = self.WINDOW_PARAMS.get(shot_type, self.WINDOW_PARAMS["_default"])
        self.shot_counter          += 1
        self._collecting            = True
        self._collect_shot_type     = shot_type
        self._collect_trigger_frame = trigger_frame_id
        self._frames_after_left     = p["after_confirm"]

    # ── 概率曲线裁窗 ──────────────────────────────────────────────
    def _find_action_window(self, shot_type: str, trigger_frame_id: int):
        """返回 (start_buf_idx, end_buf_idx, peak_frame_id)，闭区间。"""
        p = self.WINDOW_PARAMS.get(shot_type, self.WINDOW_PARAMS["_default"])
        prob_threshold = p["prob_threshold"]
        edge_before    = p["edge_before"]
        edge_after     = p["edge_after"]

        pidx  = self.SHOT_PROB_IDX.get(shot_type, 1)
        curve = np.array([e[2][pidx] for e in self._buffer])
        n     = len(curve)

        # 找 trigger 帧在缓冲中的位置，峰值只在此之后搜索
        # 防止上次击球的历史概率峰值干扰当前窗口定位（重复视频的根因）
        trigger_buf_idx = 0
        for i, (fid, _, _) in enumerate(self._buffer):
            if fid >= trigger_frame_id:
                trigger_buf_idx = i
                break

        search_curve = curve[trigger_buf_idx:]
        if len(search_curve) == 0:
            peak_idx = n - 1
        else:
            peak_idx = trigger_buf_idx + int(np.argmax(search_curve))

        # 向前扫：从峰值往前找边界（可以跨越 trigger 帧进入引拍区）
        start_idx = peak_idx
        for i in range(peak_idx, -1, -1):
            if curve[i] < prob_threshold:
                break
            start_idx = i

        # 向后扫：找第一个低于阈值的位置
        end_idx = peak_idx
        for i in range(peak_idx, n):
            if curve[i] < prob_threshold:
                break
            end_idx = i

        # 在边界外各加类型专属 padding
        start_idx = max(0,   start_idx - edge_before)
        end_idx   = min(n-1, end_idx   + edge_after)

        peak_frame_id = self._buffer[peak_idx][0]
        return start_idx, end_idx, peak_frame_id

    # ── 写出 CSV + 视频片段 ───────────────────────────────────────
    def _flush(self):
        if not self._buffer:
            self._collecting = False
            return

        shot_id   = self.shot_counter
        shot_type = self._collect_shot_type
        trigger   = self._collect_trigger_frame

        start_idx, end_idx, peak_frame_id = self._find_action_window(shot_type, trigger)
        window = self._buffer[start_idx : end_idx + 1]

        if not window:
            self._analyze_shot(window, shot_type, shot_id)
            self._collecting = False
            return

        base_name = f"shot_{shot_id:03d}_{shot_type}_frame{trigger}"

        # ── CSV ──────────────────────────────────────────────────
        rows = []
        for win_idx, (frame_id, kps_17x3, probs) in enumerate(window):
            row = keypoints_to_row(kps_17x3, probs)
            row["shot_id"]         = shot_id
            row["shot_type"]       = shot_type
            row["frame_id"]        = frame_id
            row["frame_in_window"] = win_idx
            row["peak_frame_id"]   = peak_frame_id
            rows.append(row)

        df = pd.DataFrame(rows, columns=CSV_COLUMNS)
        csv_path = os.path.join(self.output_dir, base_name + ".csv")
        df.to_csv(csv_path, index=False)
        print(f"[Recorder] CSV   → {csv_path}  "
              f"({len(df)}帧, peak@{peak_frame_id})")

        df.to_csv(self._all_csv_path, mode="a",
                  header=not self._written_header, index=False)
        self._written_header = True

        # ── 视频片段：seek 重读，不占缓冲内存 ────────────────────
        if self.save_video and self.video_path:
            frame_start = window[0][0]   # 起始 frame_id（1-based）
            frame_end   = window[-1][0]  # 结束 frame_id（含）

            # 建立 frame_id → probs 查表（供标注）
            probs_lut = {e[0]: e[2] for e in window}

            vid_path = os.path.join(self.output_dir, base_name + ".mp4")
            cap2 = cv2.VideoCapture(self.video_path)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_start - 1)  # 0-based

            ret, first = cap2.read()
            if ret:
                h, w = first.shape[:2]
                vw = cv2.VideoWriter(
                    vid_path,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    self.video_fps, (w, h)
                )
                fid = frame_start
                frame_to_write = first
                while fid <= frame_end:
                    p = probs_lut.get(fid, np.zeros(4))
                    if self._annotate_fn:
                        frame_to_write = self._annotate_fn(frame_to_write, fid, p)
                    vw.write(frame_to_write)
                    fid += 1
                    if fid <= frame_end:
                        ret, frame_to_write = cap2.read()
                        if not ret:
                            break
                vw.release()
                n_clip = frame_end - frame_start + 1
                print(f"[Recorder] Video → {vid_path}  ({n_clip}帧)")
            cap2.release()

        self._collecting        = False
        self._collect_shot_type = None

    def finalize(self):
        if self._collecting:
            self._flush()
        if self._written_header:
            print(f"[Recorder] 汇总  → {self._all_csv_path}")

    def _analyze_shot(self, window, shot_type, shot_id):
        """分析击球片段 - DTW 对比"""
        # 1. 提取角度序列
        angles_list = []
        for frame_id, kps_17x3, probs in window:
            angles = compute_joint_angles(kps_17x3)
            angles_list.append(angles)

        user_angles = np.array(angles_list, dtype=np.float64)

        # 2. DTW 对比标准库
        try:
            with open("standard_library.json", "r", encoding="utf-8") as f:
                library = json.load(f)

            best_match = None
            best_distance = float('inf')

            for std_entry in library["videos"]:
                if std_entry["shot_type"] != shot_type:
                    continue

                std_angles = np.array(std_entry["angles"], dtype=np.float64)
                dtw_result = dtw_compare(user_angles, std_angles, shot_type=shot_type)

                if dtw_result["distance"] < best_distance:
                    best_distance = dtw_result["distance"]
                    best_match = {
                        "name": std_entry["name"],
                        "distance": dtw_result["distance"],
                        "dtw_result": dtw_result
                    }

            if not best_match:
                return None

            # 3. 构建结果
            distance = best_match["distance"]
            if distance < 10:
                grade = "优秀"
            elif distance < 20:
                grade = "良好"
            elif distance < 30:
                grade = "一般"
            else:
                grade = "较差"

            # 4. 打印分析结果
            print(f"\n[DTW分析] 片段 #{shot_id} - {shot_type}")
            print(f"  评级: {grade}, DTW距离: {distance:.1f}")
            print(f"  最佳匹配: {best_match['name']}")

            active_joints = best_match["dtw_result"]["active_joints"]
            per_joint_err = np.array(best_match["dtw_result"]["per_joint_error"])
            per_joint_signed = np.array(best_match["dtw_result"]["per_joint_signed_error"])

            joint_names = ["右肩", "右肘", "右髋", "右膝", "左肩", "左肘", "左髋", "左膝"]

            errors = [(i, joint_names[i], per_joint_err[i], per_joint_signed[i])
                      for i in active_joints if np.isfinite(per_joint_err[i])]
            errors.sort(key=lambda x: x[2], reverse=True)

            print(f"  主要问题:")
            for idx, name, abs_err, signed_err in errors[:3]:
                direction = "偏大" if signed_err > 0 else "偏小"
                print(f"    - {name}: {signed_err:+.1f}° ({direction})")
            print()

        except Exception as e:
            print(f"[DTW分析] 失败: {e}")
BAR_WIDTH = 30
BAR_HEIGHT = 170
MARGIN_ABOVE_BAR = 30
SPACE_BETWEEN_BARS = 55
TEXT_ORIGIN_X = 1075
BAR_ORIGIN_X = 1070


class ShotCounter:
    MIN_FRAMES_BETWEEN_SHOTS = 60
    CONFIRM_DELAY = 30  # 触发后等20帧再确认，期间serve可覆盖forehand

    def __init__(self, skeleton_recorder=None):
        self.nb_history = 30
        self.probs = np.zeros(4)
        self.nb_forehands = 0
        self.nb_backhands = 0
        self.nb_serves = 0
        self.last_shot = "neutral"
        self.frames_since_last_shot = self.MIN_FRAMES_BETWEEN_SHOTS
        self.results = []

        # 延迟确认
        self.pending_shot = None
        self.pending_frame = 0
        self.pending_prob = 0.0

        # 骨架记录器（可选）
        self.skeleton_recorder = skeleton_recorder

    def _confirm(self, shot, frame_id):
        """真正记录一次击球"""
        if shot == "backhand":
            self.nb_backhands += 1
        elif shot == "forehand":
            self.nb_forehands += 1
        elif shot == "serve":
            self.nb_serves += 1
        self.last_shot = shot
        self.frames_since_last_shot = 0
        self.results.append({"FrameID": frame_id, "Shot": shot})

        # 通知骨架记录器
        if self.skeleton_recorder:
            self.skeleton_recorder.on_shot_confirmed(shot, frame_id)

    def update(self, probs, frame_id):
        if len(probs) == 4:
            self.probs = probs
        else:
            self.probs[0:3] = probs

        self.frames_since_last_shot += 1

        # ── 阶段1：检测新击球触发 ──────────────────────────
        if self.frames_since_last_shot > self.MIN_FRAMES_BETWEEN_SHOTS and self.pending_shot is None:
            if probs[3] > 0.6:       # serve 优先
                self.pending_shot = "serve"
                self.pending_frame = frame_id
                self.pending_prob = probs[3]
            elif probs[0] > 0.8:     # backhand
                self.pending_shot = "backhand"
                self.pending_frame = frame_id
                self.pending_prob = probs[0]
            elif probs[1] > 0.8:     # forehand
                self.pending_shot = "forehand"
                self.pending_frame = frame_id
                self.pending_prob = probs[1]

        # ── 阶段2：pending 期间，serve 可覆盖 forehand/backhand ──
        elif self.pending_shot in ("forehand", "backhand"):
            if probs[3] > self.pending_prob and probs[3] > 0.6:
                self.pending_shot = "serve"
                self.pending_prob = probs[3]
            elif probs[3] > 0.7:
                self.pending_shot = "serve"
                self.pending_prob = probs[3]

        # ── 阶段3：等待 CONFIRM_DELAY 帧后确认 ─────────────
        if self.pending_shot and (frame_id - self.pending_frame) >= self.CONFIRM_DELAY:
            self._confirm(self.pending_shot, self.pending_frame)
            self.pending_shot = None
            self.pending_prob = 0.0

    def finalize(self):
        """视频结束时，强制确认待定的击球"""
        if self.pending_shot:
            print(f"[视频结束] 强制确认待定击球: {self.pending_shot} @ frame {self.pending_frame}")
            self._confirm(self.pending_shot, self.pending_frame)
            self.pending_shot = None
            self.pending_prob = 0.0

    def display(self, frame):
        current = self.pending_shot if self.pending_shot else self.last_shot

        cv2.putText(frame, f"Backhands = {self.nb_backhands}",
            (20, frame.shape[0] - 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
            (0, 255, 0) if current == "backhand" else (0, 0, 255), 2)
        cv2.putText(frame, f"Forehands = {self.nb_forehands}",
            (20, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 1,
            (0, 255, 0) if current == "forehand" else (0, 0, 255), 2)
        cv2.putText(frame, f"Serves = {self.nb_serves}",
            (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1,
            (0, 255, 0) if current == "serve" else (0, 0, 255), 2)

        if self.pending_shot:
            cv2.putText(frame, f"[待确认: {self.pending_shot}]",
                (20, frame.shape[0] - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 200, 255), 2)


def draw_probs(frame, probs):
    for i, label in enumerate(["S", "B", "N", "F"]):
        cv2.putText(frame, label,
            (TEXT_ORIGIN_X + SPACE_BETWEEN_BARS * i, 230),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    for i, p in enumerate([probs[3], probs[0], probs[2], probs[1]]):
        cv2.rectangle(frame,
            (BAR_ORIGIN_X + SPACE_BETWEEN_BARS * i,
             int(BAR_HEIGHT + MARGIN_ABOVE_BAR - BAR_HEIGHT * p)),
            (BAR_ORIGIN_X + SPACE_BETWEEN_BARS * i + BAR_WIDTH,
             BAR_HEIGHT + MARGIN_ABOVE_BAR),
            color=(0, 0, 255), thickness=-1)
        cv2.rectangle(frame,
            (BAR_ORIGIN_X + SPACE_BETWEEN_BARS * i, MARGIN_ABOVE_BAR),
            (BAR_ORIGIN_X + SPACE_BETWEEN_BARS * i + BAR_WIDTH,
             BAR_HEIGHT + MARGIN_ABOVE_BAR),
            color=(255, 255, 255), thickness=1)
    return frame


class GT:
    def __init__(self, path_to_annotation):
        self.shots = pd.read_csv(path_to_annotation)
        self.current_row_in_shots = 0
        self.nb_backhands = 0
        self.nb_forehands = 0
        self.nb_serves = 0
        self.last_shot = "neutral"

    def display(self, frame, frame_id):
        if self.current_row_in_shots < len(self.shots):
            if frame_id == self.shots.iloc[self.current_row_in_shots]["FrameId"]:
                shot = self.shots.iloc[self.current_row_in_shots]["Shot"]
                if shot == "backhand":   self.nb_backhands += 1
                elif shot == "forehand": self.nb_forehands += 1
                elif shot == "serve":    self.nb_serves += 1
                self.last_shot = shot
                self.current_row_in_shots += 1
        for i, (label, count) in enumerate([
            ("Backhands", self.nb_backhands),
            ("Forehands", self.nb_forehands),
            ("Serves",    self.nb_serves),
        ]):
            cv2.putText(frame, f"{label} = {count}",
                (frame.shape[1] - 300, frame.shape[0] - 100 + i * 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0) if self.last_shot == label[:-1].lower() else (0, 0, 255), 2)


def draw_fps(frame, fps):
    cv2.putText(frame, f"{int(fps)} fps", (20, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)


def draw_frame_id(frame, frame_id):
    cv2.putText(frame, f"Frame {frame_id}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)


def compute_recall_precision(gt, shots):
    gt_numpy = gt.to_numpy()
    nb_match = nb_misses = nb_fp = 0
    for gt_shot in gt_numpy:
        found = any(s["Shot"] == gt_shot[0] and abs(s["FrameID"] - gt_shot[1]) <= 30
                    for s in shots)
        if found: nb_match += 1
        else:     nb_misses += 1
    for shot in shots:
        found = any(gt_shot[0] == shot["Shot"] and abs(shot["FrameID"] - gt_shot[1]) <= 30
                    for gt_shot in gt_numpy)
        if not found: nb_fp += 1
    if nb_match + nb_fp > 0:
        print(f"Precision {nb_match/(nb_match+nb_fp)*100:.1f}%")
    if nb_match + nb_misses > 0:
        print(f"Recall    {nb_match/(nb_match+nb_misses)*100:.1f}%")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("model")
    parser.add_argument("--evaluate", help="标注文件路径（可选）")
    parser.add_argument("-f", type=int, help="从第几帧开始")
    parser.add_argument("--left-handed", action="store_const", const=True, default=False)
    parser.add_argument("--save", help="输出视频路径（可选，不传则实时显示）")
    parser.add_argument("--skeleton-dir", default="skeleton_data",
                        help="骨架CSV输出目录（默认: skeleton_data）")
    parser.add_argument("--save-video-clips", action="store_true",
                        help="同时保存每次击球的视频片段（.mp4）到 skeleton-dir")
    args = parser.parse_args()

    # 初始化骨架记录器
    skeleton_recorder = SkeletonRecorder(
        output_dir=args.skeleton_dir,
        save_video=args.save_video_clips,
        video_path=args.video,
        video_fps=30.0,   # 会在读取视频后更新
    )

    shot_counter = ShotCounter(skeleton_recorder=skeleton_recorder)
    gt = GT(args.evaluate) if args.evaluate else None

    m1 = keras.saving.load_model(args.model)

    cap = cv2.VideoCapture(args.video)
    assert cap.isOpened(), f"无法打开视频: {args.video}"

    # 用实际视频帧率更新记录器
    skeleton_recorder.video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # 注入帧标注函数：视频片段会用同一套标注（骨架+概率条+帧号）
    def _annotate(bgr, fid, probs):
        draw_probs(bgr, probs)
        draw_fps(bgr, 0)          # 片段中 fps 无意义，显示0
        draw_frame_id(bgr, fid)
        return bgr
    skeleton_recorder.set_annotate_fn(_annotate)

    ret, frame = cap.read()
    human_pose_extractor = HumanPoseExtractor(frame.shape)

    writer = None
    if args.save:
        fps_out = cap.get(cv2.CAP_PROP_FPS)
        h, w = frame.shape[:2]
        writer = cv2.VideoWriter(args.save,
                                 cv2.VideoWriter_fourcc(*"mp4v"),
                                 fps_out, (w, h))

    NB_IMAGES = 30
    FRAME_ID = 0
    features_pool = []
    prev_time = time.time()

    # 当前帧的原始关键点（17x3），供 SkeletonRecorder 使用
    current_kps_raw = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        FRAME_ID += 1
        if args.f is not None and FRAME_ID < args.f:
            continue

        human_pose_extractor.extract(frame)

        # ── 在 discard 之前保存原始17点关键点 ──────────────
        # keypoints_with_scores shape: (1, 1, 17, 3)
        current_kps_raw = human_pose_extractor.keypoints_with_scores.reshape(17, 3)

        human_pose_extractor.discard(["left_eye", "right_eye", "left_ear", "right_ear"])

        features = human_pose_extractor.keypoints_with_scores.reshape(17, 3)
        if args.left_handed:
            features[:, 1] = 1 - features[:, 1]
        features = features[features[:, 2] > 0][:, 0:2].reshape(1, 13 * 2)

        features_pool.append(features)
        if len(features_pool) == NB_IMAGES:
            features_seq = np.array(features_pool).reshape(1, NB_IMAGES, 26)
            probs = m1(features_seq)[0].numpy()
            print(f"\n[原脚本] Frame {FRAME_ID}, probs={probs}")
            print(f"  max={probs.max():.4f}, argmax={probs.argmax()}")
            shot_counter.update(probs, FRAME_ID)
            features_pool = features_pool[1:]

        # ── 每帧更新骨架记录器 ──────────────────────────────────
        skeleton_recorder.update(FRAME_ID, current_kps_raw, shot_counter.probs)

        draw_probs(frame, shot_counter.probs)
        shot_counter.display(frame)
        if gt:
            gt.display(frame, FRAME_ID)

        fps_val = 1 / (time.time() - prev_time)
        prev_time = time.time()
        draw_fps(frame, fps_val)
        draw_frame_id(frame, FRAME_ID)

        human_pose_extractor.draw_results_frame(frame)
        if shot_counter.frames_since_last_shot < 30 and shot_counter.last_shot != "neutral":
            human_pose_extractor.roi.draw_shot(frame, shot_counter.last_shot)
        human_pose_extractor.roi.update(human_pose_extractor.keypoints_pixels_frame)

        if writer:
            writer.write(frame)
        else:
            cv2.imshow("Tennis Shot Recognition", frame)
            k = cv2.waitKey(1)
            if k == 27:
                break

    cap.release()
    if writer:
        writer.release()
        print(f"输出视频已保存: {args.save}")
    cv2.destroyAllWindows()

    # 先确认待定击球，再写出骨架数据
    shot_counter.finalize()
    skeleton_recorder.finalize()

    print("\n击球结果:")
    for r in shot_counter.results:
        print(f"  Frame {r['FrameID']:5d}  {r['Shot']}")

    if gt and args.evaluate:
        compute_recall_precision(pd.read_csv(args.evaluate), shot_counter.results)