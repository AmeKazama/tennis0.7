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
  - 添加 --service 模式，输出 JSON 流（供后端调用）
  - 提供 analyze_video_stream 异步生成器，可直接导入供 FastAPI 使用
"""

import time
import math
from argparse import ArgumentParser
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import sys
import tensorflow as tf
import keras
import numpy as np
import pandas as pd
import cv2
from services.movenet_model import compute_joint_angles, dtw_compare
import json
from services.extract_human_pose import HumanPoseExtractor
try:
    from services.phase_dtw import extract_mediapipe_annotation, compare_user_annotation
    HAS_PHASE_DTW = True
except Exception as e:
    print(f"[warning] phase_dtw unavailable: {e}")
    HAS_PHASE_DTW = False
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple
import tempfile
import shutil
import httpx
import asyncio
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

# 导入手腕速度检测模块
try:
    from services.wrist_speed_detection import (
        compute_fused_speed,
        pick_impact_frame_by_type
    )
    HAS_WRIST_SPEED = True
except ImportError:
    print("[警告] wrist_speed_detection 模块未找到,将使用基础模式")
    HAS_WRIST_SPEED = False


# 导入手腕速度检测模块
try:
    from services.wrist_speed_detection import (
        compute_fused_speed,
        pick_impact_frame_by_type
    )
    HAS_WRIST_SPEED = True
except ImportError:
    print("[警告] wrist_speed_detection 模块未找到,将使用基础模式")
    HAS_WRIST_SPEED = False

# YOLO 导入（可选）
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    YOLO = None

# COCO 类别索引
COCO_SPORTS_BALL = 32    # 网球
COCO_TENNIS_RACKET = 38  # 球拍
physical_devices = tf.config.list_physical_devices("GPU")
print(f"GPU 设备: {physical_devices}")
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
print(f"可用 GPU 数量: {len(physical_devices)}")


# ==================== 豆包 AI 教练服务 ====================

class DoubaoService:
    """豆包 AI 教练服务"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "80aa24d9-9b78-458a-81f9-8c093d0fbffd"
        self.url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.model = "ep-m-20260330202605-hpzwt"

        self.client = httpx.AsyncClient(timeout=httpx.Timeout(50.0, connect=10.0))
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_coach_advice(self, analysis_report: str) -> Optional[str]:
        """根据分析报告获取豆包教练建议"""
        system_prompt = """你是一位有10年经验的专业网球教练，性格热情、幽默、有耐心。你正在场边看学员录像回放。

你会收到学员动作的技术分析报告，包含：
- 动作类型（正手/反手/发球）
- 整体评级（优秀/良好/一般/较差）
- 关节角度偏差和主要问题

你的反馈分两部分，**必须有情绪和温度**：

【第1句：情绪化评价】根据评级给出真实的情感反应
- 优秀（DTW<10）："哇！这球打得太漂亮了！" / "牛啊！动作标准得没话说！"
- 良好（DTW 10-20）："不错不错！进步明显啊！" / "嘿，打得挺好的！"
- 一般（DTW 20-30）："嗯...还行吧，不过还能更好" / "这球有点勉强啊"
- 较差（DTW>30）："哎呀，这球打得有点乱啊" / "别急别急，咱从头再来"

【第2句：具体建议】用口语化、生活化的语言，不要说"角度偏大/偏小"，要说动作的感觉和画面感。

示例：
✅ "哇！这球打得太漂亮了！手肘再放松一丢丢就完美了。"
✅ "不错不错！手臂别绷那么紧，像甩鞭子一样挥出去。"
✅ "嗯...还行吧，膝盖蹲太低了，站得自然点来。"

总长度30-40字，必须有真实情绪。"""

        system_prompt = """你是一位有10年经验的专业网球教练，正在看学员录像回放。
你会收到结构化动作报告，可能包含：整体评级、阶段DTW、关键帧角度、最相似标准动作、差异最大的阶段。

回复要求：
1. 先给一句有情绪的真实评价，再给具体建议。
2. 优先使用【阶段化动作分析】里的最大差异阶段，不要只看总分。
3. 不要逐项复述数字；把角度和DTW翻译成动作感觉，例如：挠背不够深、甩鞭蓄力不足、击球点没有完全向上伸展、随挥和落地缓冲不够完整。
4. 如果是发球，重点关注：引拍/挠背、向前启动、击球伸展、身体扭转、落地缓冲。
5. 输出2-3句，口语化、具体、可执行；不要使用“DTW”“阶段序列差异”等技术词。
6. 如果报告中没有阶段分析，则根据主要问题给最关键的一条建议。"""

        system_prompt = """你是一位专业网球教练，正在根据动作分析报告给学员反馈。

报告里可能包含 phase_distances、keyframe_distances、最大阶段问题、最大关键帧问题和关键角度读数。

回复必须遵守：
1. 先讲问题，不能先夸奖；第一句必须直接指出最主要动作问题。
2. 优先参考报告里的【必须优先讲的主要问题】和【必须结合说明的关键帧问题】。
3. 不要说 DTW、distance、phase_distances、keyframe_distances、阶段序列差异等技术词。
4. 不要逐项复述数字；把数字翻译成动作感受，比如：挠背不够深、甩鞭蓄力不足、击球点释放不完整、随挥和落地缓冲不够。
5. 如果是发球，重点关注：引拍/挠背、向前启动、击球伸展、身体扭转、落地缓冲。
6. 必须输出三段，格式固定：
主要问题: ...
改进建议: ...
训练方法: ...
7. 每段一到两句话，口语化、具体、可执行。可以有鼓励，但必须放在指出问题之后。"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_report}
            ],
            "temperature": 1.3
        }

        try:
            response = await self.client.post(self.url, headers=self.headers, json=payload)
            if response.status_code != 200:
                print(f"[豆包] API 失败: {response.status_code}", file=sys.stderr)
                return None
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result['choices'][0]['message']['content'].strip()
            return None
        except Exception as e:
            print(f"[豆包] 异常: {e}", file=sys.stderr)
            return None

    async def close(self):
        await self.client.aclose()


# ==================== 击球帧精确定位 ====================

def compute_wrist_speed(keypoints_sequence: np.ndarray, smooth_window: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """计算手腕速度曲线（用于精确定位击球帧）"""
    T = len(keypoints_sequence)
    KP_RIGHT_WRIST = 10

    wrist_x = keypoints_sequence[:, KP_RIGHT_WRIST, 1]
    wrist_y = keypoints_sequence[:, KP_RIGHT_WRIST, 0]
    wrist_score = keypoints_sequence[:, KP_RIGHT_WRIST, 2]

    valid_mask = wrist_score > 0.2

    if valid_mask.sum() < 3:
        return np.zeros(T), np.zeros(T, dtype=bool)

    valid_indices = np.where(valid_mask)[0]
    if len(valid_indices) < T:
        f_x = interp1d(valid_indices, wrist_x[valid_indices], kind='linear', fill_value='extrapolate')
        f_y = interp1d(valid_indices, wrist_y[valid_indices], kind='linear', fill_value='extrapolate')
        wrist_x = f_x(np.arange(T))
        wrist_y = f_y(np.arange(T))

    if smooth_window > 2 and T > smooth_window:
        wrist_x = savgol_filter(wrist_x, smooth_window, 2)
        wrist_y = savgol_filter(wrist_y, smooth_window, 2)

    dx = np.diff(wrist_x, prepend=wrist_x[0])
    dy = np.diff(wrist_y, prepend=wrist_y[0])
    speed = np.sqrt(dx**2 + dy**2)

    if smooth_window > 2 and T > smooth_window:
        speed = savgol_filter(speed, smooth_window, 2)

    return speed, valid_mask


def detect_impact_frame(keypoints_sequence: np.ndarray, shot_type: str = "unknown") -> Tuple[int, Dict]:
    """检测击球帧（基于手腕速度峰值）"""
    T = len(keypoints_sequence)
    if T < 5:
        return 0, {"error": "序列太短"}

    speed_curve, valid_mask = compute_wrist_speed(keypoints_sequence, smooth_window=5)

    if shot_type == "serve":
        start_idx = max(0, T // 2)
        end_idx = T
    elif shot_type == "forehand":
        start_idx = min(10, T - 1)
        end_idx = min(30, T)
    elif shot_type == "backhand":
        start_idx = 0
        end_idx = min(22, T)
    else:
        start_idx = 0
        end_idx = T

    window_speed = speed_curve[start_idx:end_idx]
    if len(window_speed) == 0:
        return 0, {"error": "窗口为空"}

    local_max_idx = np.argmax(window_speed)
    impact_frame = start_idx + local_max_idx

    return impact_frame, {
        "speed_at_impact": float(speed_curve[impact_frame]),
        "max_speed": float(speed_curve.max()),
    }


# ==================== YOLO 球拍+网球检测器 ====================

class YoloBallRacketDetector:
    """
    YOLO 检测器：检测网球和球拍位置
    用于更精确的击球帧定位（基于球拍与球的距离）
    """

    def __init__(self, weights_path: str = "yolov8s.pt", conf: float = 0.20,
                 device: Optional[str] = None, imgsz: int = 640):
        """
        初始化 YOLO 检测器

        Args:
            weights_path: YOLO 模型权重路径
            conf: 置信度阈值
            device: 设备 (None=自动选择, 'cpu', 'cuda:0')
            imgsz: 输入图像大小
        """
        if not HAS_YOLO:
            raise RuntimeError(
                "ultralytics 未安装。运行: pip install ultralytics"
            )

        print(f"[YOLO] 加载权重: {weights_path}")
        self.model = YOLO(weights_path)
        self.conf = conf
        self.imgsz = imgsz
        self.device = device
        print(f"[YOLO] 初始化完成")

    def infer(self, frame_bgr: np.ndarray) -> Dict:
        """
        检测单帧中的球和球拍

        Returns:
            {
                "ball": (cx, cy, conf) or None,
                "racket": (cx, cy, w, h, conf) or None
            }
        """
        results = self.model.predict(
            frame_bgr,
            conf=self.conf,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )

        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return {"ball": None, "racket": None}

        cls = r.boxes.cls.cpu().numpy().astype(int)
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()

        ball = None
        racket = None

        for i in range(len(cls)):
            c = int(cls[i])
            x1, y1, x2, y2 = xyxy[i]
            cx = 0.5 * (x1 + x2)
            cy = 0.5 * (y1 + y2)
            bw = x2 - x1
            bh = y2 - y1
            conf_i = float(confs[i])

            if c == COCO_SPORTS_BALL:
                if ball is None or conf_i > ball[2]:
                    ball = (float(cx), float(cy), conf_i)
            elif c == COCO_TENNIS_RACKET:
                if racket is None or conf_i > racket[4]:
                    racket = (float(cx), float(cy), float(bw), float(bh), conf_i)

        return {"ball": ball, "racket": racket}


def compute_ball_racket_distance(detections: List[Dict], img_diag: float,
                                 max_interp_gap: int = 3) -> Dict:
    """
    计算球拍与球的距离曲线（归一化）

    Args:
        detections: 每帧的检测结果列表
        img_diag: 图像对角线长度（用于归一化）
        max_interp_gap: 最大插值间隔

    Returns:
        {
            "dist": 原始距离 (T,),
            "dist_interp": 插值后距离 (T,),
            "both_mask": 同时检测到球和拍的帧 (T,),
            "valid_mask": 有效距离的帧 (T,)
        }
    """
    T = len(detections)
    dist = np.full(T, np.inf, dtype=np.float64)
    both = np.zeros(T, dtype=bool)

    for t, det in enumerate(detections):
        b = det.get("ball")
        r = det.get("racket")

        if b is not None and r is not None:
            d_px = float(np.hypot(b[0] - r[0], b[1] - r[1]))
            dist[t] = d_px / max(img_diag, 1.0)
            both[t] = True

    # 线性插值填补短暂的检测丢失
    dist_interp = dist.copy()
    valid = both.copy()

    if both.any() and max_interp_gap > 0:
        detected_indices = np.where(both)[0]
        for i in range(len(detected_indices) - 1):
            a = detected_indices[i]
            b_idx = detected_indices[i + 1]
            gap = b_idx - a - 1

            if 0 < gap <= max_interp_gap:
                da, db = dist[a], dist[b_idx]
                for k in range(1, gap + 1):
                    frac = k / (gap + 1)
                    dist_interp[a + k] = da + frac * (db - da)
                    valid[a + k] = True

    return {
        "dist": dist,
        "dist_interp": dist_interp,
        "both_mask": both,
        "valid_mask": valid,
    }


def detect_impact_frame_with_yolo(
    keypoints_sequence: np.ndarray,
    video_frames: List[np.ndarray],
    shot_type: str,
    yolo_detector: Optional[YoloBallRacketDetector] = None,
    dist_floor: float = 0.005
) -> Tuple[int, Dict]:
    """
    使用 YOLO + 手腕速度联合检测击球帧

    Args:
        keypoints_sequence: (T, 17, 3) 关键点序列
        video_frames: 视频帧列表
        shot_type: 击球类型
        yolo_detector: YOLO 检测器实例
        dist_floor: 距离下限（防止极小值主导）

    Returns:
        impact_frame: 击球帧索引
        info: 诊断信息
    """
    T = len(keypoints_sequence)

    # 1. 计算手腕速度
    speed_curve, _ = compute_wrist_speed(keypoints_sequence, smooth_window=5)

    # 2. YOLO 检测球和拍
    if yolo_detector is None or not video_frames:
        # 降级到纯手腕速度
        return detect_impact_frame(keypoints_sequence, shot_type)

    print(f"[击球帧] 使用 YOLO 辅助检测...")
    detections = []
    for frame in video_frames:
        det = yolo_detector.infer(frame)
        detections.append(det)

    # 3. 计算球拍距离
    h, w = video_frames[0].shape[:2]
    img_diag = np.hypot(h, w)

    dist_result = compute_ball_racket_distance(detections, img_diag, max_interp_gap=3)
    dist_interp = dist_result["dist_interp"]
    valid_mask = dist_result["valid_mask"]

    # 4. 联合评分：speed / distance
    # 距离越小越好，速度越大越好
    joint_score = np.zeros(T)
    for t in range(T):
        if valid_mask[t] and speed_curve[t] > 0:
            d = max(dist_interp[t], dist_floor)
            joint_score[t] = speed_curve[t] / d
        else:
            joint_score[t] = -np.inf

    # 5. 根据击球类型选择窗口
    if shot_type == "serve":
        start_idx = max(0, T // 2)
        end_idx = T
    elif shot_type == "forehand":
        start_idx = min(10, T - 1)
        end_idx = min(30, T)
    elif shot_type == "backhand":
        start_idx = 0
        end_idx = min(22, T)
    else:
        start_idx = 0
        end_idx = T

    window_score = joint_score[start_idx:end_idx]
    if len(window_score) == 0 or np.all(window_score == -np.inf):
        # 降级到纯速度
        return detect_impact_frame(keypoints_sequence, shot_type)

    local_max_idx = np.argmax(window_score)
    impact_frame = start_idx + local_max_idx

    return impact_frame, {
        "speed_at_impact": float(speed_curve[impact_frame]),
        "distance_at_impact": float(dist_interp[impact_frame]) if valid_mask[impact_frame] else None,
        "joint_score": float(joint_score[impact_frame]),
        "yolo_used": True,
    }


def format_analysis_report(shot_id: int, shot_type: str, dtw_distance: float,
                          issues: List[Dict], best_match_name: str) -> str:
    """格式化分析报告（供豆包解析）"""
    if dtw_distance < 20:
        grade = "优秀"
    elif dtw_distance < 35:
        grade = "良好"
    elif dtw_distance < 50:
        grade = "一般"
    else:
        grade = "较差"

    shot_type_cn = {"forehand": "正手", "backhand": "反手", "serve": "发球"}.get(shot_type, shot_type)

    top_issues = issues[:3]
    issues_text = "\n".join([
        f"{i+1}. {issue['joint']}{issue['signed_error']:+.1f}°({issue['direction']})"
        for i, issue in enumerate(top_issues)
    ])

    focus_side = "右侧" if any("右" in i['joint'] for i in top_issues) else "左侧"
    if any("左" in i['joint'] for i in top_issues) and any("右" in i['joint'] for i in top_issues):
        focus_side = "双侧"

    report = f"""【动作分析报告 #{shot_id}】
动作类型: {shot_type_cn}
整体评级: {grade} (DTW距离: {dtw_distance:.1f})
关注侧: {focus_side}

主要问题:
{issues_text}

参考标准: {best_match_name}

请作为专业网球教练，用1-2句话提醒学员最关键的问题和改进方法。"""

    return report


def format_enhanced_analysis_report(shot_id: int, shot_type: str, dtw_distance: float,
                                    issues: List[Dict], best_match_name: str,
                                    phase_dtw: Optional[Dict] = None,
                                    user_annotation: Optional[Dict] = None) -> str:
    """Build a richer Doubao prompt using phase DTW and key-frame angles."""
    base_report = format_analysis_report(
        shot_id=shot_id,
        shot_type=shot_type,
        dtw_distance=dtw_distance,
        issues=issues,
        best_match_name=best_match_name,
    )

    if not phase_dtw:
        return base_report

    phase_names = {
        "prepare_to_backswing": "准备到引拍阶段",
        "backswing_to_forward": "引拍顶点到向前启动阶段",
        "forward_to_impact": "向前挥拍到击球阶段",
        "impact_to_finish": "击球后随挥/落地阶段",
        "start": "准备姿态",
        "backswing_peak": "引拍顶点",
        "forward_start": "向前启动",
        "impact": "击球瞬间",
        "end": "结束姿态",
    }
    serve_hints = {
        "prepare_to_backswing": "看抛球后的身体蓄力和手臂引拍节奏",
        "backswing_to_forward": "看挠背深度、肘部折叠和甩鞭蓄力",
        "forward_to_impact": "看向上伸展、击球点释放和手臂打直",
        "impact_to_finish": "看随挥完整性、落地缓冲和身体平衡",
        "backswing_peak": "引拍顶点决定挠背是否充分",
        "forward_start": "向前启动决定甩鞭是否蓄住力",
        "impact": "击球瞬间决定是否在最高点充分伸展",
        "end": "结束姿态反映随挥和落地缓冲",
    }

    def describe_phase(name):
        label = phase_names.get(name, name)
        hint = serve_hints.get(name, "") if shot_type == "serve" else ""
        return f"{label}：{hint}" if hint else label

    lines = [
        "",
        "【阶段化动作分析】",
        f"匹配标准动作: {best_match_name}",
    ]
    seq = phase_dtw.get("sequence_distance")
    key = phase_dtw.get("keyframe_distance")
    if seq is not None:
        lines.append(f"阶段序列差异: {seq:.1f}")
    if key is not None:
        lines.append(f"关键帧姿态差异: {key:.1f}")

    phase_boundaries = (user_annotation or {}).get("phase_boundaries", {})
    if phase_boundaries:
        lines.append(f"用户阶段帧: {phase_boundaries}")

    phase_distances = sorted(
        phase_dtw.get("phase_distances", []),
        key=lambda item: item.get("distance", 0),
        reverse=True,
    )
    if phase_distances:
        lines.append("阶段差异排序:")
        for idx, item in enumerate(phase_distances[:4], 1):
            lines.append(
                f"{idx}. {describe_phase(item.get('phase', ''))}，差异 {item.get('distance', 0):.1f} "
                f"({item.get('user_frames')}帧 vs 标准{item.get('standard_frames')}帧)"
            )

    key_distances = sorted(
        phase_dtw.get("keyframe_distances", []),
        key=lambda item: item.get("distance", 0),
        reverse=True,
    )
    if key_distances:
        lines.append("关键帧差异排序:")
        for idx, item in enumerate(key_distances[:3], 1):
            lines.append(f"{idx}. {describe_phase(item.get('phase', ''))}，差异 {item.get('distance', 0):.1f}")

    key_angles = (user_annotation or {}).get("key_angles", {})
    if shot_type == "serve" and key_angles:
        def angle_at(phase, angle_name):
            value = key_angles.get(phase, {}).get("angles", {}).get(angle_name)
            return f"{value:.1f}°" if isinstance(value, (int, float)) else "未知"

        lines.extend([
            "发球关键动作读数:",
            f"- 引拍顶点右肘: {angle_at('backswing_peak', 'right_elbow')}，判断挠背深度",
            f"- 向前启动右肘: {angle_at('forward_start', 'right_elbow')}，判断甩鞭蓄力",
            f"- 击球瞬间右肘: {angle_at('impact', 'right_elbow')}，判断击球伸展",
            f"- 击球瞬间身体扭转: {angle_at('impact', 'torso_rotation')}，判断躯干释放",
            f"- 结束帧右膝: {angle_at('end', 'right_knee')}，判断落地缓冲",
        ])

    lines.append("请优先针对差异最大的阶段给建议，把数字翻译成动作感觉，不要逐项复述角度。")
    return base_report + "\n" + "\n".join(lines)


# ─────────────────────────────────────────────
# Override the earlier formatter with a stricter report for Doubao.
def format_enhanced_analysis_report(shot_id: int, shot_type: str, dtw_distance: float,
                                    issues: List[Dict], best_match_name: str,
                                    phase_dtw: Optional[Dict] = None,
                                    user_annotation: Optional[Dict] = None) -> str:
    base_report = format_analysis_report(
        shot_id=shot_id,
        shot_type=shot_type,
        dtw_distance=dtw_distance,
        issues=issues,
        best_match_name=best_match_name,
    )
    if not phase_dtw:
        return base_report

    phase_names = {
        "prepare_to_backswing": "准备到引拍阶段",
        "backswing_to_forward": "引拍顶点到向前启动阶段",
        "forward_to_impact": "向前挥拍到击球阶段",
        "impact_to_finish": "击球后随挥/落地阶段",
        "start": "准备姿势",
        "backswing_peak": "引拍顶点",
        "forward_start": "向前启动",
        "impact": "击球瞬间",
        "end": "结束姿势",
    }
    serve_hints = {
        "prepare_to_backswing": "看抛球后的身体蓄力和手臂引拍节奏",
        "backswing_to_forward": "看挠背深度、肘部折叠和甩鞭蓄力",
        "forward_to_impact": "看向上伸展、击球点释放和手臂打直",
        "impact_to_finish": "看随挥完整性、落地缓冲和身体平衡",
        "backswing_peak": "判断挠背是否充分",
        "forward_start": "判断甩鞭蓄力姿势是否到位",
        "impact": "判断击球瞬间是否在高点击球并充分伸展",
        "end": "判断随挥和落地缓冲是否完整",
    }
    phase_problem_hints = {
        "prepare_to_backswing": "优先检查抛球后的节奏、转肩蓄力和引拍是否稳定。",
        "backswing_to_forward": "优先指出挠背深度、肘部折叠和甩鞭蓄力是否不充分。",
        "forward_to_impact": "优先指出向上蹬伸、击球点释放、手臂伸展是否不完整。",
        "impact_to_finish": "优先指出随挥收拍、落地缓冲和身体平衡是否不完整。",
    }
    keyframe_problem_hints = {
        "start": "准备姿势可能影响后续节奏。",
        "backswing_peak": "引拍顶点差异大时，重点看挠背和持拍手臂折叠。",
        "forward_start": "向前启动差异大时，重点看甩鞭蓄力和身体启动顺序。",
        "impact": "击球瞬间差异大时，重点看击球高度、手臂伸展和躯干释放。",
        "end": "结束姿势差异大时，重点看随挥、落地缓冲和重心稳定。",
    }

    def phase_label(name):
        label = phase_names.get(name, name)
        hint = serve_hints.get(name, "") if shot_type == "serve" else ""
        return f"{label}: {hint}" if hint else label

    phase_distances = sorted(
        phase_dtw.get("phase_distances", []),
        key=lambda item: item.get("distance", 0),
        reverse=True,
    )
    keyframe_distances = sorted(
        phase_dtw.get("keyframe_distances", []),
        key=lambda item: item.get("distance", 0),
        reverse=True,
    )

    lines = [
        "",
        "【阶段化动作分析】",
        f"匹配标准动作: {best_match_name}",
    ]
    seq = phase_dtw.get("sequence_distance")
    key = phase_dtw.get("keyframe_distance")
    if seq is not None:
        lines.append(f"阶段序列总差异: {seq:.1f}")
    if key is not None:
        lines.append(f"关键帧姿态总差异: {key:.1f}")

    phase_boundaries = (user_annotation or {}).get("phase_boundaries", {})
    if phase_boundaries:
        lines.append(f"用户阶段帧: {phase_boundaries}")

    if phase_distances:
        worst = phase_distances[0]
        worst_phase = worst.get("phase", "")
        lines.extend([
            "",
            "【必须优先讲的主要问题】",
            f"最大阶段问题: {phase_label(worst_phase)}",
            f"该阶段差异: {worst.get('distance', 0):.1f}",
            f"问题解释方向: {phase_problem_hints.get(worst_phase, '把这个阶段翻译成具体动作问题。')}",
            "",
            "【phase_distances 阶段差异排序】",
        ])
        for idx, item in enumerate(phase_distances[:4], 1):
            phase = item.get("phase", "")
            lines.append(
                f"{idx}. phase={phase} | {phase_label(phase)} | "
                f"distance={item.get('distance', 0):.1f} | "
                f"user_frames={item.get('user_frames')} | "
                f"standard_frames={item.get('standard_frames')} | "
                f"path_length={item.get('path_length')}"
            )

    if keyframe_distances:
        worst_key = keyframe_distances[0]
        worst_key_phase = worst_key.get("phase", "")
        lines.extend([
            "",
            "【必须结合说明的关键帧问题】",
            f"最大关键帧问题: {phase_label(worst_key_phase)}",
            f"该关键帧差异: {worst_key.get('distance', 0):.1f}",
            f"问题解释方向: {keyframe_problem_hints.get(worst_key_phase, '把关键帧差异解释成具体动作问题。')}",
            "",
            "【keyframe_distances 关键帧差异排序】",
        ])
        for idx, item in enumerate(keyframe_distances[:5], 1):
            phase = item.get("phase", "")
            lines.append(
                f"{idx}. phase={phase} | {phase_label(phase)} | "
                f"distance={item.get('distance', 0):.1f}"
            )

    key_angles = (user_annotation or {}).get("key_angles", {})
    if shot_type == "serve" and key_angles:
        def angle_at(phase, angle_name):
            value = key_angles.get(phase, {}).get("angles", {}).get(angle_name)
            return f"{value:.1f}度" if isinstance(value, (int, float)) else "未知"

        lines.extend([
            "",
            "【发球关键动作读数】",
            f"- 引拍顶点右肘: {angle_at('backswing_peak', 'right_elbow')}，用于判断挠背深度。",
            f"- 向前启动右肘: {angle_at('forward_start', 'right_elbow')}，用于判断甩鞭蓄力。",
            f"- 击球瞬间右肘: {angle_at('impact', 'right_elbow')}，用于判断击球伸展。",
            f"- 击球瞬间身体扭转: {angle_at('impact', 'torso_rotation')}，用于判断躯干释放。",
            f"- 结束帧右膝: {angle_at('end', 'right_knee')}，用于判断落地缓冲。",
        ])

    lines.extend([
        "",
        "【给豆包的强制要求】",
        "必须先指出主要问题，不能只夸奖。",
        "第一句必须包含一个明确动作问题，优先使用“最大阶段问题”和“最大关键帧问题”。",
        "不要逐项复述数字，不要说 DTW、distance、阶段序列差异等技术词；把数字翻译成动作感受。",
        "输出格式固定为: 主要问题: ... 改进建议: ... 训练方法: ...",
    ])
    return base_report + "\n" + "\n".join(lines)


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
    支持从 CSV 文件夹加载标准骨架库进行 DTW 对比。
    """

    BUFFER_SIZE   = 200
    SHOT_PROB_IDX = {"backhand": 0, "forehand": 1, "neutral": 2, "serve": 3}

    WINDOW_PARAMS = {
        "forehand": dict(prob_threshold=0.35, edge_before=20, edge_after=0,  after_confirm=15),
        "backhand": dict(prob_threshold=0.35, edge_before=20, edge_after=0,  after_confirm=15),
        "serve":    dict(prob_threshold=0.25, edge_before=30, edge_after=30, after_confirm=55),
        "_default": dict(prob_threshold=0.35, edge_before=12, edge_after=10, after_confirm=30),
    }

    def __init__(self, output_dir="skeleton_data",
                 save_video=False, video_path=None, video_fps=30.0, service_mode=False,
                 standard_dir="services/standard_skeletons"):
        self.service_mode = service_mode
        if not service_mode:
            os.makedirs(output_dir, exist_ok=True)
        self.output_dir  = output_dir
        self.save_video  = save_video
        self.video_path  = video_path
        self.video_fps   = video_fps
        self.shot_counter = 0

        self._buffer: list = []

        self._collecting            = False
        self._collect_shot_type     = None
        self._collect_trigger_frame = None
        self._frames_after_left     = 0

        self._annotate_fn = None

        self._all_csv_path   = os.path.join(output_dir, "all_shots.csv") if not service_mode else None
        self._written_header = False

        self.service_results = []
        self._on_shot_ready = None  # 回调：分析完一段立刻调用，供流式推送使用

    def set_annotate_fn(self, fn):
        self._annotate_fn = fn

    def _load_standard_library(self):
        """从 standard_dir 中的 CSV 文件加载标准动作角度序列"""
        import glob
        from pathlib import Path

        angle_cols = [
            "left_elbow_angle", "right_elbow_angle",
            "left_shoulder_angle", "right_shoulder_angle",
            "left_hip_angle", "right_hip_angle",
            "left_knee_angle", "right_knee_angle"
        ]

        prefix_map = {"正": "forehand", "反": "backhand", "发": "serve"}

        for filepath in glob.glob(os.path.join(self.standard_dir, "*.csv")):
            filename = Path(filepath).stem
            shot_type = None
            for prefix, st in prefix_map.items():
                if filename.startswith(prefix):
                    shot_type = st
                    break
            if shot_type is None:
                continue

            try:
                df = pd.read_csv(filepath)
                angles_df = df[angle_cols].copy()
                # 处理缺失值
                angles_df = angles_df.infer_objects(copy=False)
                angles_df = angles_df.interpolate(method='linear', limit_direction='both')
                angles_df = angles_df.fillna(method='ffill').fillna(method='bfill').fillna(0)
                angles_array = angles_df.to_numpy(dtype=np.float64)

                self._standard_library[shot_type].append({
                    "name": filename,
                    "angles": angles_array
                })
            except Exception as e:
                print(f"[标准库] 跳过 {filepath}: {e}")

        for shot_type, entries in self._standard_library.items():
            if entries:
                print(f"[标准库] 已加载 {shot_type} 类动作 {len(entries)} 个")

    def update(self, frame_id: int, kps_17x3: np.ndarray, probs: np.ndarray):
        self._buffer.append((frame_id, kps_17x3.copy(), probs.copy()))
        if len(self._buffer) > self.BUFFER_SIZE:
            self._buffer.pop(0)

        if self._collecting:
            self._frames_after_left -= 1
            if self._frames_after_left <= 0:
                self._flush()

    def on_shot_confirmed(self, shot_type: str, trigger_frame_id: int):
        if self._collecting:
            self._flush()
        p = self.WINDOW_PARAMS.get(shot_type, self.WINDOW_PARAMS["_default"])
        self.shot_counter          += 1
        self._collecting            = True
        self._collect_shot_type     = shot_type
        self._collect_trigger_frame = trigger_frame_id
        self._frames_after_left     = p["after_confirm"]

    def _find_action_window(self, shot_type: str, trigger_frame_id: int):
        p = self.WINDOW_PARAMS.get(shot_type, self.WINDOW_PARAMS["_default"])
        prob_threshold = p["prob_threshold"]
        edge_before    = p["edge_before"]
        edge_after     = p["edge_after"]

        pidx  = self.SHOT_PROB_IDX.get(shot_type, 1)
        curve = np.array([e[2][pidx] for e in self._buffer])
        n     = len(curve)

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

        start_idx = peak_idx
        for i in range(peak_idx, -1, -1):
            if curve[i] < prob_threshold:
                break
            start_idx = i

        end_idx = peak_idx
        for i in range(peak_idx, n):
            if curve[i] < prob_threshold:
                break
            end_idx = i

        start_idx = max(0,   start_idx - edge_before)
        end_idx   = min(n-1, end_idx   + edge_after)

        peak_frame_id = self._buffer[peak_idx][0]
        return start_idx, end_idx, peak_frame_id

    def _flush(self):
        """
        确认击球后,提取动作窗口并分析 (已集成手腕速度检测)
        """
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

        # ========== 新增: 使用手腕速度检测精确击球帧 ==========
        analysis_window = window  # 默认使用整个窗口
        impact_frame_id = peak_frame_id

        if HAS_WRIST_SPEED and len(window) >= 10:
            try:
                # 1. 提取关键点序列
                kp_seq = np.array([kps for _, kps, _ in window])  # (T, 17, 3)

                # 2. 计算融合速度 (使用合理的默认图像尺寸)
                img_w, img_h = 640, 480
                speed_result = compute_fused_speed(
                    kp_seq, img_w, img_h,
                    smooth_xy=3,
                    smooth_v=3,
                    score_thresh=0.2,
                    wrist_prior=0.7
                )

                # 3. 根据 shot_type 找精确击球帧索引 (在 window 内的相对位置)
                impact_idx = pick_impact_frame_by_type(
                    speed_result["speed_fused"],
                    speed_result["valid_mask"],
                    shot_type,
                    head_pad_ratio=0.15,  # 减小排除区域
                    tail_pad_ratio=0.15
                )

                # 4. 提取击球帧周围的子窗口 (±10 帧,动态窗口)
                pad = 10
                sub_start = max(0, impact_idx - pad)
                sub_end = min(len(window), impact_idx + pad + 1)
                analysis_window = window[sub_start:sub_end]
                impact_frame_id = window[impact_idx][0]

                print(f"[速度检测] 窗口 {len(window)} 帧 -> 击球帧@{impact_idx} -> 分析窗口 {len(analysis_window)} 帧")

            except Exception as e:
                print(f"[速度检测] 失败,降级到全窗口: {e}")
                analysis_window = window
        # ========== 手腕速度检测结束 ==========

        base_name = f"shot_{shot_id:03d}_{shot_type}_frame{trigger}"

        if not self.service_mode:
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

            if self.save_video and self.video_path:
                frame_start = window[0][0]
                frame_end   = window[-1][0]
                probs_lut = {e[0]: e[2] for e in window}

                vid_path = os.path.join(self.output_dir, base_name + ".mp4")
                cap2 = cv2.VideoCapture(self.video_path)
                cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_start - 1)

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

        # 使用 analysis_window (可能是精确提取的子窗口) 做 DTW 分析
        analysis = self._analyze_shot(
            analysis_window,
            shot_type,
            shot_id,
            full_window=window,
            impact_frame_id=impact_frame_id,
        )
        if analysis is not None:
            self.service_results.append(analysis)
            # 立刻触发回调，实现分出一段推送一段
            if self._on_shot_ready is not None:
                try:
                    self._on_shot_ready(analysis)
                except Exception as cb_err:
                    print(f"[Recorder] 回调异常: {cb_err}")

        self._collecting = False

    def finalize(self):
        if self._collecting:
            self._flush()
        if self._written_header:
            print(f"[Recorder] 汇总  → {self._all_csv_path}")

    def _analyze_shot(self, window, shot_type, shot_id, full_window=None, impact_frame_id=None):
        """分析击球片段 - DTW 对比（从 standard_library.json 读取标准库）【完美适配版】"""
        if not window:
            return None

        # ── 1. 提取用户动作的角度序列 ──
        if HAS_PHASE_DTW and self.video_path:
            try:
                user_annotation = extract_mediapipe_annotation(
                    self.video_path,
                    full_window or window,
                    shot_type,
                    shot_id,
                    impact_frame=impact_frame_id,
                )
                if user_annotation is not None:
                    phase_matches = compare_user_annotation(user_annotation)
                    if phase_matches:
                        best_phase = phase_matches[0]
                        distance = float(best_phase["distance"])
                        if distance < 20:
                            grade = "优秀"
                        elif distance < 35:
                            grade = "良好"
                        elif distance < 50:
                            grade = "一般"
                        else:
                            grade = "较差"

                        phase_issues = sorted(
                            best_phase.get("phase_distances", []),
                            key=lambda item: item.get("distance", 0),
                            reverse=True,
                        )[:3]
                        issues = [
                            {
                                "joint": item["phase"],
                                "signed_error": float(item["distance"]),
                                "direction": "阶段差异",
                                "user_angle": None,
                                "standard_angle": None,
                            }
                            for item in phase_issues
                        ]

                        print(f"\n[阶段DTW] 片段 #{shot_id} - {shot_type}")
                        print(f"  评级: {grade}, 阶段DTW距离: {distance:.1f}")
                        print(f"  最佳匹配: {best_phase.get('standard', 'unknown')}")
                        print(f"  用户阶段: {user_annotation.get('phase_boundaries')}")
                        for item in best_phase.get("phase_distances", []):
                            print(f"    - {item['phase']}: {item['distance']:.1f} "
                                  f"({item['user_frames']} vs {item['standard_frames']} frames)")

                        return {
                            "shot_id": shot_id,
                            "shot_type": shot_type,
                            "grade": grade,
                            "distance": distance,
                            "best_match": best_phase.get("standard", "unknown"),
                            "issues": issues,
                            "phase_dtw": {
                                "sequence_distance": best_phase.get("sequence_distance"),
                                "keyframe_distance": best_phase.get("keyframe_distance"),
                                "phase_distances": best_phase.get("phase_distances", []),
                                "keyframe_distances": best_phase.get("keyframe_distances", []),
                                "standard_file": best_phase.get("file"),
                            },
                            "user_annotation": user_annotation,
                        }
            except Exception as e:
                print(f"[阶段DTW] 失败，回退到旧DTW: {e}")

        angles_list = []
        for frame_id, kps_17x3, probs in window:
            angles = compute_joint_angles(kps_17x3)
            angles_list.append(angles)
        user_angles = np.array(angles_list, dtype=np.float64)

        # ── 2. 从 standard_library.json 加载标准库 ──
        try:
            with open("services/standard_library.json", "r", encoding="utf-8") as f:
                library = json.load(f)
        except Exception as e:
            print(f"[DTW分析] 无法读取 standard_library.json: {e}")
            return None

        best_match = None
        best_distance = float('inf')
        best_dtw_result = None
        best_std_angles = None

        for std_entry in library.get("videos", []):
            if std_entry["shot_type"] != shot_type:
                continue

            std_angles = np.array(std_entry["angles"], dtype=np.float64)
            dtw_result = dtw_compare(user_angles, std_angles, shot_type=shot_type)

            if dtw_result["distance"] < best_distance:
                best_distance = dtw_result["distance"]
                best_match = std_entry["name"]
                best_dtw_result = dtw_result
                best_std_angles = std_angles

        if not best_match:
            print(f"[DTW分析] 没有匹配的标准动作")
            return None

        # ── 3. 计算评级 ──
        distance = best_distance
        if distance < 10:
            grade = "优秀"
        elif distance < 20:
            grade = "良好"
        elif distance < 30:
            grade = "一般"
        else:
            grade = "较差"

        # ── 4. 从 DTW 结果安全读取数据 ──
        dtw_result = best_dtw_result
        active_joints = dtw_result["active_joints"]
        per_joint_err = np.array(dtw_result["per_joint_error"])
        per_joint_signed = np.array(dtw_result["per_joint_signed_error"])
        path = dtw_result.get("path", [])
        std_angles = best_std_angles

        joint_names = ["右肩", "右肘", "右髋", "右膝", "左肩", "左肘", "左髋", "左膝"]

        # ── 🔥 核心修复：用 path 生成对齐后的序列（等价 aligned_user_angles）🔥 ──
        aligned_user_angles = []
        aligned_std_angles = []
        if len(path) > 0:
            aligned_user_angles = np.array([user_angles[i] for i, j in path])
            aligned_std_angles = np.array([std_angles[j] for i, j in path])
        else:
            min_len = min(len(user_angles), len(std_angles))
            aligned_user_angles = user_angles[:min_len]
            aligned_std_angles = std_angles[:min_len]

        # ── 5. 用标准库整段均值 vs 用户对齐段均值做对比展示 ──
        if len(aligned_user_angles) > 0:
            user_sample = np.nanmean(aligned_user_angles, axis=0)  # 用户整段均值
            std_sample  = np.nanmean(std_angles, axis=0)           # 标准库整段均值
        else:
            user_sample = np.full(8, np.nan)
            std_sample  = np.full(8, np.nan)

        # ── 6. 生成问题列表 ──
        errors = []
        for i in active_joints:
            if i >= len(joint_names):
                continue
            err = per_joint_err[i] if i < len(per_joint_err) else np.nan
            signed = per_joint_signed[i] if i < len(per_joint_signed) else np.nan
            if np.isfinite(err):
                errors.append((i, joint_names[i], err, signed))

        errors.sort(key=lambda x: x[2], reverse=True)
        issues = []
        for idx, name, abs_err, signed_err in errors[:3]:
            direction = "偏大" if signed_err > 0 else "偏小"
            issues.append({
                "joint": name,
                "signed_error": float(signed_err),
                "direction": direction,
                "user_angle": round(float(user_sample[idx]), 1) if np.isfinite(user_sample[idx]) else None,
                "standard_angle": round(float(std_sample[idx]), 1) if np.isfinite(std_sample[idx]) else None
            })

        # ── 7. 输出 ──
        print(f"\n[DTW分析] 片段 #{shot_id} - {shot_type}")
        print(f"  评级: {grade}, DTW距离: {distance:.1f}")
        print(f"  最佳匹配: {best_match}")
        print(f"  主要问题:")
        for issue in issues:
            print(f"    - {issue['joint']}: {issue['signed_error']:+.1f}° ({issue['direction']}) "
                  f"用户:{issue['user_angle']}° 标准:{issue['standard_angle']}°")
        print()

        return {
            "shot_id": shot_id,
            "shot_type": shot_type,
            "grade": grade,
            "distance": distance,
            "best_match": best_match,
            "issues": issues
        }


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
        print(f"[DEBUG] CONFIRM {shot.upper()} at frame {frame_id}", file=sys.stderr)
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
                print(f"[DEBUG] Trigger SERVE at frame {frame_id}, prob={probs[3]:.4f}", file=sys.stderr)
                self.pending_shot = "serve"
                self.pending_frame = frame_id
                self.pending_prob = probs[3]
            elif probs[0] > 0.8:     # backhand
                print(f"[DEBUG] Trigger BACKHAND at frame {frame_id}, prob={probs[0]:.4f}", file=sys.stderr)
                self.pending_shot = "backhand"
                self.pending_frame = frame_id
                self.pending_prob = probs[0]
            elif probs[1] > 0.8:     # forehand
                print(f"[DEBUG] Trigger FOREHAND at frame {frame_id}, prob={probs[1]:.4f}", file=sys.stderr)
                self.pending_shot = "forehand"
                self.pending_frame = frame_id
                self.pending_prob = probs[1]

        # ── 阶段2：pending 期间，serve 可覆盖 forehand/backhand ──
        elif self.pending_shot in ("forehand", "backhand"):
            if probs[3] > self.pending_prob and probs[3] > 0.6:
                print(f"[DEBUG] Override to SERVE at frame {frame_id}", file=sys.stderr)
                self.pending_shot = "serve"
                self.pending_prob = probs[3]
            elif probs[3] > 0.7:
                print(f"[DEBUG] Override to SERVE (high) at frame {frame_id}", file=sys.stderr)
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


# ===================================================================
# 核心分析函数（命令行和 service 共用）
# ===================================================================
def run_analysis(video_path, model, args, service_mode=False, fps_override=None, on_shot_ready=None):
    """
    执行完整的击球检测和分析。
    如果 service_mode=True，则返回 (shot_counter, skeleton_recorder, total_frames, fps)；
    否则直接显示 GUI 并返回 None。
    on_shot_ready: 可选回调，每当一个片段 DTW 分析完成立刻调用，参数为 analysis dict。
    """
    # 初始化骨架记录器
    # service 模式下使用临时目录（避免 Windows 路径问题）
    if service_mode:
        temp_dir = tempfile.mkdtemp(prefix="tennis_service_")
        output_dir = temp_dir
    else:
        output_dir = args.skeleton_dir
        temp_dir = None

    skeleton_recorder = SkeletonRecorder(
        output_dir=output_dir,
        save_video=args.save_video_clips and not service_mode,
        video_path=video_path,
        video_fps=args.video_fps if hasattr(args, 'video_fps') else 30.0,
        service_mode=service_mode,
    )
    skeleton_recorder._on_shot_ready = on_shot_ready  # 注入回调

    shot_counter = ShotCounter(skeleton_recorder=skeleton_recorder)
    gt = GT(args.evaluate) if args.evaluate and not service_mode else None

    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"无法打开视频: {video_path}"

    # 用实际视频帧率更新记录器
    real_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    skeleton_recorder.video_fps = real_fps
    if fps_override is not None:
        real_fps = fps_override

    # 注入帧标注函数（非 service 模式或视频片段需要）
    def _annotate(bgr, fid, probs):
        if service_mode:
            # service 模式下不需要标注，直接返回原图
            return bgr
        draw_probs(bgr, probs)
        draw_fps(bgr, 0)
        draw_frame_id(bgr, fid)
        return bgr
    skeleton_recorder.set_annotate_fn(_annotate)

    ret, frame = cap.read()
    human_pose_extractor = HumanPoseExtractor(frame.shape)

    writer = None
    if not service_mode and args.save:
        fps_out = real_fps
        h, w = frame.shape[:2]
        writer = cv2.VideoWriter(args.save,
                                 cv2.VideoWriter_fourcc(*"mp4v"),
                                 fps_out, (w, h))

    NB_IMAGES = 30
    FRAME_ID = 0
    features_pool = []
    prev_time = time.time()
    current_kps_raw = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        FRAME_ID += 1
        if args.f is not None and FRAME_ID < args.f:
            continue

        human_pose_extractor.extract(frame)

        # 保存原始17点关键点
        current_kps_raw = human_pose_extractor.keypoints_with_scores.reshape(17, 3)

        human_pose_extractor.discard(["left_eye", "right_eye", "left_ear", "right_ear"])

        features = human_pose_extractor.keypoints_with_scores.reshape(17, 3)
        if args.left_handed:
            features[:, 1] = 1 - features[:, 1]
        features = features[features[:, 2] > 0][:, 0:2].reshape(1, 13 * 2)

        features_pool.append(features)
        if len(features_pool) == NB_IMAGES:
            features_seq = np.array(features_pool).reshape(1, NB_IMAGES, 26)
            probs = model(features_seq)[0].numpy()

            # 单机模式打印概率
            if not service_mode:
                print(f"\nFrame {FRAME_ID}, probs={probs}")
                print(f"  max={probs.max():.4f}, argmax={probs.argmax()}")

            shot_counter.update(probs, FRAME_ID)
            features_pool = features_pool[1:]

        skeleton_recorder.update(FRAME_ID, current_kps_raw, shot_counter.probs)

        if not service_mode:
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
        else:
            # Service 模式：只执行关键的 roi.update()
            human_pose_extractor.roi.update(human_pose_extractor.keypoints_pixels_frame)

    if not service_mode and writer:
        writer.release()
        print(f"输出视频已保存: {args.save}")

    cap.release()
    if not service_mode:
        cv2.destroyAllWindows()

    # 最终确认
    shot_counter.finalize()
    skeleton_recorder.finalize()

    if not service_mode:
        print("\n击球结果:")
        for r in shot_counter.results:
            print(f"  Frame {r['FrameID']:5d}  {r['Shot']}")
        if gt and args.evaluate:
            compute_recall_precision(pd.read_csv(args.evaluate), shot_counter.results)

    # 清理临时目录（service 模式）
    if service_mode and temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 返回结果供 service 使用
    return shot_counter, skeleton_recorder, FRAME_ID, real_fps


# ===================================================================
# 异步生成器（供 FastAPI 调用）
# ===================================================================



async def analyze_video_stream(video_bytes: bytes, model_path: str = "tennis_rnn_converted.keras") -> AsyncGenerator:
    """
    异步生成器，接收视频字节流，逐个输出击球片段的分析结果（JSON dict）。
    用于 FastAPI 的 StreamingResponse。
    """
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp.write(video_bytes)
        video_path = tmp.name

    # 初始化豆包服务（用于获取教练建议）
    doubao_service = DoubaoService()

    try:
        # 加载模型
        model = keras.saving.load_model(model_path)

        # 模拟 args 对象
        class Args:
            left_handed = False
            evaluate = None
            save = None
            skeleton_dir = "skeleton_data"
            save_video_clips = False
            f = None
            video_fps = 30.0

        args = Args()

        # 运行分析（service 模式）
        shot_counter, skeleton_recorder, total_frames, fps = run_analysis(
            video_path, model, args, service_mode=True
        )

        # 建立一个 trigger_frame 映射：shot_id -> FrameID
        trigger_map = {}
        for idx, r in enumerate(shot_counter.results, start=1):
            # 结果列表顺序与击球确认顺序一致
            trigger_map[idx] = r["FrameID"]

        # 从 skeleton_recorder.service_results 中获取每个击球的分析结果
        for res in skeleton_recorder.service_results:
            shot_id = res["shot_id"]
            trigger_frame = trigger_map.get(shot_id, 0)

            # 构建分析报告，用于请求豆包建议
            report = format_analysis_report(
                shot_id=shot_id,
                shot_type=res["shot_type"],
                dtw_distance=res.get("distance", 999),
                issues=res.get("issues", []),
                best_match_name=res.get("best_match", "unknown")
            )

            # 尝试获取豆包教练建议，失败或超时则给出默认文本
            coach_advice = None
            try:
                coach_advice = await doubao_service.get_coach_advice(report)
            except Exception as e:
                print(f"[豆包] 请求异常: {e}", file=sys.stderr)
            if coach_advice is None:
                coach_advice = "教练建议生成中，请稍后重试..."

            segment = {
                "type": "segment",
                "data": {
                    "segment_id": shot_id,
                    "shot_type": res["shot_type"],
                    "shot_type_cn": {"forehand": "正手", "backhand": "反手", "serve": "发球"}.get(
                        res["shot_type"], res["shot_type"]),
                    "trigger_frame": trigger_frame,
                    "analysis": {
                        "grade": res["grade"],
                        "distance": res["distance"],
                        "top_issues": res["issues"]  # issues 已包含 user_angle 和 standard_angle
                    },
                    "coach_advice": coach_advice
                }
            }
            yield segment

        # 总结
        yield {
            "type": "summary",
            "data": {
                "num_segments": len(shot_counter.results),
                "num_frames": total_frames,
                "fps": fps,
                "duration": total_frames / fps,
                "shots": shot_counter.results
            }
        }

    finally:
        await doubao_service.close()
        if os.path.exists(video_path):
            os.unlink(video_path)



# ===================================================================
# 外部调用接口
# ===================================================================

def run_tennis_analysis(video_path: str, model_path: str, service_mode: bool = True) -> Dict:
    """
    同步调用接口（供外部模块使用）

    Args:
        video_path: 视频文件路径
        model_path: RNN 模型路径
        service_mode: 是否为 service 模式（True=输出JSON流，False=GUI显示）

    Returns:
        分析结果字典（仅 service_mode=False 时返回，service_mode=True 时直接输出到 stdout）
    """
    import sys
    from io import StringIO

    # 构造参数
    class Args:
        video = video_path
        model = model_path
        evaluate = None
        f = None
        left_handed = False
        save = None
        skeleton_dir = "skeleton_data"
        save_video_clips = False
        service = service_mode

    args = Args()

    # 保存原 stdout
    original_stdout = sys.stdout

    try:
        if service_mode:
            # Service 模式：直接运行，输出到 stdout
            asyncio.run(main_async_impl(args))
            return {"status": "success"}
        else:
            # GUI 模式：捕获输出
            sys.stdout = StringIO()
            asyncio.run(main_async_impl(args))
            output = sys.stdout.getvalue()
            return {"status": "success", "output": output}
    finally:
        sys.stdout = original_stdout


async def main_async_impl(args):
    """实际的异步主函数实现"""
    doubao_service = DoubaoService()

    try:
        if args.service:
            # Service 模式
            if not args.video or not args.model:
                print("Service 模式需要指定 --video 和 --model", file=sys.stderr)
                sys.exit(1)

            model = keras.saving.load_model(args.model)

            class ServiceArgs:
                left_handed = args.left_handed
                evaluate = None
                save = None
                skeleton_dir = args.skeleton_dir
                save_video_clips = False
                f = args.f
                video_fps = 30.0

            service_args = ServiceArgs()

            # 运行分析（service 模式）
            shot_counter, skeleton_recorder, total_frames, fps = run_analysis(
                args.video, model, service_args, service_mode=True
            )

            # 输出 SSE 格式（集成豆包建议）
            for idx, res in enumerate(skeleton_recorder.service_results, 1):
                # 格式化分析报告
                report = format_analysis_report(
                    shot_id=res["shot_id"],
                    shot_type=res["shot_type"],
                    dtw_distance=res.get("distance", 999),
                    issues=res.get("issues", []),
                    best_match_name=res.get("best_match", "unknown")
                )

                # 调用豆包获取建议
                coach_advice = await doubao_service.get_coach_advice(report)

                if idx <= len(shot_counter.results):
                    trigger_frame = shot_counter.results[idx - 1]["FrameID"]
                else:
                    trigger_frame = 0

                segment = {
                    "type": "segment",
                    "data": {
                        "segment_id": res["shot_id"],
                        "shot_type": res["shot_type"],
                        "shot_type_cn": {"forehand": "正手", "backhand": "反手", "serve": "发球"}.get(res["shot_type"], res["shot_type"]),
                        "trigger_frame": trigger_frame,
                        "analysis": {
                            "grade": res["grade"],
                            "distance": res["distance"],
                            "top_issues": res["issues"],
                            "coach_advice": coach_advice or "建议生成中..."
                        }
                    }
                }
                sys.stdout.write(f"data: {json.dumps(segment, ensure_ascii=False)}\n\n")
                sys.stdout.flush()

            summary = {
                "type": "summary",
                "data": {
                    "num_segments": len(shot_counter.results),
                    "num_frames": total_frames,
                    "fps": fps,
                    "duration": total_frames / fps,
                    "shots": shot_counter.results
                }
            }
            sys.stdout.write(f"data: {json.dumps(summary, ensure_ascii=False)}\n\n")
            sys.stdout.flush()
        else:
            # 普通命令行模式
            model = keras.saving.load_model(args.model)
            run_analysis(args.video, model, args, service_mode=False)

    finally:
        await doubao_service.close()


# ===================================================================
# 命令行入口（集成豆包）
# ===================================================================
async def main_async():
    parser = ArgumentParser()
    parser.add_argument("--video", required=False, help="视频文件路径")
    parser.add_argument("--model", required=False, help="RNN模型文件路径")
    parser.add_argument("--evaluate", help="标注文件路径（可选）")
    parser.add_argument("-f", type=int, help="从第几帧开始")
    parser.add_argument("--left-handed", action="store_const", const=True, default=False)
    parser.add_argument("--save", help="输出视频路径（可选，不传则实时显示）")
    parser.add_argument("--skeleton-dir", default="skeleton_data",
                        help="骨架CSV输出目录（默认: skeleton_data）")
    parser.add_argument("--save-video-clips", action="store_true",
                        help="同时保存每次击球的视频片段（.mp4）到 skeleton-dir")
    parser.add_argument("--service", action="store_true",
                        help="Service 模式：不显示 GUI，输出 JSON 流")
    args = parser.parse_args()

    doubao_service = DoubaoService()

    try:
        if args.service:
            # Service 模式
            if not args.video or not args.model:
                print("Service 模式需要指定 --video 和 --model", file=sys.stderr)
                sys.exit(1)

            model = keras.saving.load_model(args.model)

            class ServiceArgs:
                left_handed = args.left_handed
                evaluate = None
                save = None
                skeleton_dir = args.skeleton_dir
                save_video_clips = False
                f = args.f
                video_fps = 30.0

            service_args = ServiceArgs()

            # 运行分析（service 模式）
            shot_counter, skeleton_recorder, total_frames, fps = run_analysis(
                args.video, model, service_args, service_mode=True
            )

            # 输出 SSE 格式（集成豆包建议）
            for idx, res in enumerate(skeleton_recorder.service_results, 1):
                # 格式化分析报告
                report = format_analysis_report(
                    shot_id=res["shot_id"],
                    shot_type=res["shot_type"],
                    dtw_distance=res.get("distance", 999),
                    issues=res.get("issues", []),
                    best_match_name=res.get("best_match", "unknown")
                )

                # 调用豆包获取建议
                coach_advice = await doubao_service.get_coach_advice(report)

                if idx <= len(shot_counter.results):
                    trigger_frame = shot_counter.results[idx - 1]["FrameID"]
                else:
                    trigger_frame = 0

                segment = {
                    "type": "segment",
                    "data": {
                        "segment_id": res["shot_id"],
                        "shot_type": res["shot_type"],
                        "shot_type_cn": {"forehand": "正手", "backhand": "反手", "serve": "发球"}.get(res["shot_type"], res["shot_type"]),
                        "trigger_frame": trigger_frame,
                        "analysis": {
                            "grade": res["grade"],
                            "distance": res["distance"],
                            "top_issues": res["issues"],
                            "coach_advice": coach_advice or "建议生成中..."
                        }
                    }
                }
                sys.stdout.write(f"data: {json.dumps(segment, ensure_ascii=False)}\n\n")
                sys.stdout.flush()

            summary = {
                "type": "summary",
                "data": {
                    "num_segments": len(shot_counter.results),
                    "num_frames": total_frames,
                    "fps": fps,
                    "duration": total_frames / fps,
                    "shots": shot_counter.results
                }
            }
            sys.stdout.write(f"data: {json.dumps(summary, ensure_ascii=False)}\n\n")
            sys.stdout.flush()
        else:
            # 普通命令行模式：使用位置参数
            parser_positional = ArgumentParser()
            parser_positional.add_argument("video", help="视频文件路径")
            parser_positional.add_argument("model", help="RNN模型文件路径",default="tennis_rnn_converted.keras")
            parser_positional.add_argument("--evaluate", help="标注文件路径（可选）")
            parser_positional.add_argument("-f", type=int, help="从第几帧开始")
            parser_positional.add_argument("--left-handed", action="store_const", const=True, default=False)
            parser_positional.add_argument("--save", help="输出视频路径（可选，不传则实时显示）")
            parser_positional.add_argument("--skeleton-dir", default="skeleton_data")
            parser_positional.add_argument("--save-video-clips", action="store_true")
            args_pos = parser_positional.parse_args()

            model = keras.saving.load_model(args_pos.model)
            run_analysis(args_pos.video, model, args_pos, service_mode=False)

    finally:
        await doubao_service.close()


if __name__ == "__main__":
    asyncio.run(main_async())
