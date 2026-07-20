"""
手腕速度检测和击球帧定位模块
完全照抄 extract_frame_samples.py 的实现方法
"""

import numpy as np
from scipy.interpolate import interp1d
from typing import Tuple, Dict, Optional


def moving_average(signal, window=3):
    """简单移动平均平滑"""
    if window < 2:
        return signal
    if len(signal) < window:
        return signal
    kernel = np.ones(window) / window
    return np.convolve(signal, kernel, mode='same')


def fill_low_confidence(xy_px, score, thresh=0.2):
    """
    填充低置信度点:
    - score >= thresh: 保留
    - score < thresh: 线性插值 (如果前后有高置信度点)
    """
    T = len(xy_px)
    xy_filled = xy_px.copy()
    valid = (score >= thresh)

    if not valid.any():
        return xy_filled, valid

    valid_indices = np.where(valid)[0]
    if len(valid_indices) == 0:
        return xy_filled, valid

    # 对 x 和 y 分别插值
    if len(valid_indices) < T:
        try:
            f_x = interp1d(valid_indices, xy_px[valid_indices, 0],
                          kind='linear', fill_value='extrapolate')
            f_y = interp1d(valid_indices, xy_px[valid_indices, 1],
                          kind='linear', fill_value='extrapolate')
            xy_filled[:, 0] = f_x(np.arange(T))
            xy_filled[:, 1] = f_y(np.arange(T))
        except:
            pass  # 插值失败就用原值

    return xy_filled, valid


def _compute_joint_speed(kp_seq, joint_idx, img_w, img_h,
                        smooth_xy=3, smooth_v=3, score_thresh=0.2):
    """
    计算单个关节的速度曲线 (完全照抄 extract_frame_samples.py)

    Args:
        kp_seq: (T, 17, 3) 关键点序列 [y_norm, x_norm, score]
        joint_idx: 关节索引 (如 10 = 右手腕)
        img_w, img_h: 图像尺寸 (用于归一化坐标转像素)
        smooth_xy: xy 坐标平滑窗口
        smooth_v: 速度平滑窗口
        score_thresh: 置信度阈值

    Returns:
        dict with keys: xy_px, xy_smooth, speed_raw, speed_smooth, score, valid_mask
    """
    T = len(kp_seq)

    # 提取归一化坐标和置信度
    y_norm = kp_seq[:, joint_idx, 0]  # [0, 1]
    x_norm = kp_seq[:, joint_idx, 1]  # [0, 1]
    score = kp_seq[:, joint_idx, 2]   # [0, 1]

    # 转像素坐标
    xy_px = np.zeros((T, 2), dtype=np.float64)
    xy_px[:, 0] = x_norm * img_w
    xy_px[:, 1] = y_norm * img_h

    # 填充低置信度点
    xy_filled, valid = fill_low_confidence(xy_px, score, thresh=score_thresh)

    # 平滑 xy
    xy_smooth = np.zeros_like(xy_filled)
    xy_smooth[:, 0] = moving_average(xy_filled[:, 0], smooth_xy)
    xy_smooth[:, 1] = moving_average(xy_filled[:, 1], smooth_xy)

    # 计算速度
    diff = np.diff(xy_smooth, axis=0)
    speed = np.sqrt((diff ** 2).sum(axis=1))
    speed = np.concatenate([[0.0], speed])  # 对齐,使 speed[t] 是从 t-1 到 t 的速度

    # 平滑速度
    speed_smooth = moving_average(speed, smooth_v)

    return {
        "xy_px": xy_filled,
        "xy_smooth": xy_smooth,
        "speed_raw": speed,
        "speed_smooth": speed_smooth,
        "score": score,
        "valid_mask": valid,
    }


def compute_fused_speed(kp_seq, img_w, img_h,
                       smooth_xy=3, smooth_v=3, score_thresh=0.2,
                       wrist_prior=0.7):
    """
    融合右手腕和右肘的速度 (完全照抄 extract_frame_samples.py)

    融合公式:
        w_wrist = wrist_prior * score_wrist
        w_elbow = (1 - wrist_prior) * score_elbow
        speed_fused = (w_wrist * speed_wrist + w_elbow * speed_elbow) / (w_wrist + w_elbow)

    Args:
        kp_seq: (T, 17, 3) 关键点序列
        img_w, img_h: 图像尺寸
        wrist_prior: 手腕权重先验 (默认 0.7)

    Returns:
        dict with keys: speed_fused, valid_mask, wrist, elbow
    """
    KP_RIGHT_WRIST = 10
    KP_RIGHT_ELBOW = 8

    wrist = _compute_joint_speed(kp_seq, KP_RIGHT_WRIST, img_w, img_h,
                                 smooth_xy, smooth_v, score_thresh)
    elbow = _compute_joint_speed(kp_seq, KP_RIGHT_ELBOW, img_w, img_h,
                                 smooth_xy, smooth_v, score_thresh)

    T = len(wrist["speed_smooth"])
    eps = 1e-6

    # 权重融合
    w_wrist = wrist_prior * np.clip(wrist["score"], 0.0, 1.0)
    w_elbow = (1.0 - wrist_prior) * np.clip(elbow["score"], 0.0, 1.0)
    w_sum = w_wrist + w_elbow + eps

    speed_fused = (w_wrist * wrist["speed_smooth"]
                   + w_elbow * elbow["speed_smooth"]) / w_sum

    # 有效掩码: 至少一个关节有效
    valid_fused = wrist["valid_mask"] | elbow["valid_mask"]

    return {
        "speed_fused": speed_fused,
        "valid_mask": valid_fused,
        "wrist": wrist,
        "elbow": elbow,
    }


# ============================================================================
# 关键帧位置统计先验
# 数据源：tennis0.7/264/*_final.json（58 个 Label Studio 手工标注）
# 提取脚本：见 commit "撤掉 pick_impact_frame_by_type 硬编码窗口偏置"
# 更新日期：2026-07-20
# ----------------------------------------------------------------------------
# impact 在窗口中的相对位置极其稳定（stdev 0.05-0.12），可作为定位锚点，
# 比"在固定帧区间找速度峰"鲁棒得多——后者隐含"窗口长度固定"假设，
# 而 SkeletonRecorder 切出的窗口实际浮动 20~60 帧。
# ============================================================================
_IMPACT_REL_PRIOR = {
    # shot_type: (impact_rel_median, n_samples, stdev)
    "forehand": 0.70,   # n=21, mean=0.74, median=0.70, stdev=0.09
    "backhand": 0.70,   # n=17, mean=0.72, median=0.70, stdev=0.12
    "serve":    0.80,   # n=20, mean=0.75, median=0.80, stdev=0.05
}
_IMPACT_REL_DEFAULT = 0.70   # unknown / 异常 shot_type 的兜底
_IMPACT_SEARCH_RADIUS = 5    # 在锚点 ±N 帧内找速度峰精修


def pick_impact_frame_by_type(
    speed,
    valid_mask,
    shot_type,
    head_pad_ratio=0.10,
    tail_pad_ratio=0.10,
):
    """
    根据击球类型选择精确击球帧。

    历史 bug（2026-07-20 修复）：
    原实现按 shot_type 写死了搜索区间（forehand [10,30) / backhand 前 22 帧 /
    serve 后半段），隐含"窗口长度固定且击球总在固定位置"假设。但 SkeletonRecorder
    的窗口由 RNN 概率曲线粗切，长度浮动 20~60 帧，导致：
    - forehand：impact 强制落在 [10,30)，真击球若在 35 帧则严重偏早
    - backhand：窗口 ≤22 帧时搜全窗，反手随挥大开大合速度更大被误选为 impact

    新算法：用 58 个 Label Studio 标注的 impact_rel 中位数作锚点，在锚点
    ±_IMPACT_SEARCH_RADIUS 帧内找速度峰精修。对任意窗口长度都适用。

    Args:
        speed: (T,) 速度曲线
        valid_mask: (T,) 有效掩码
        shot_type: "forehand" | "backhand" | "serve" | "unknown"
        head_pad_ratio: 头部排除比例（默认 0.10，比原 0.20 收窄，给锚点更多空间）
        tail_pad_ratio: 尾部排除比例（默认 0.10）

    Returns:
        int: 击球帧索引（窗口内相对位置）
    """
    T = len(speed)
    if T == 0:
        return 0

    head = max(1, int(T * head_pad_ratio))
    tail = max(1, int(T * tail_pad_ratio))

    candidate = speed.copy().astype(np.float64)
    candidate[:head] = -np.inf
    candidate[-tail:] = -np.inf
    candidate[~valid_mask] = -np.inf

    # 全无效时回退到全局 argmax（速度曲线本身，不受 padding 影响）
    if np.all(np.isneginf(candidate)):
        return int(np.argmax(speed))

    # 1) 用统计先验的 impact_rel 作为锚点
    impact_rel = _IMPACT_REL_PRIOR.get(shot_type, _IMPACT_REL_DEFAULT)
    anchor = int(T * impact_rel)

    # 2) 在锚点 ±_IMPACT_SEARCH_RADIUS 帧内找速度峰
    search_start = max(head, anchor - _IMPACT_SEARCH_RADIUS)
    search_end = min(T - tail, anchor + _IMPACT_SEARCH_RADIUS + 1)

    if search_start >= search_end:
        # 窗口过窄，锚点附近无法容纳搜索区，退化到全局 argmax
        return int(np.argmax(candidate))

    search_slice = candidate[search_start:search_end]
    if np.all(np.isneginf(search_slice)):
        # 锚点附近都无效，退化到全局 argmax
        return int(np.argmax(candidate))

    local_peak = int(np.argmax(search_slice))
    return search_start + local_peak


# ========== 测试代码 ==========
if __name__ == "__main__":
    # 模拟测试
    T = 30
    kp_seq = np.random.rand(T, 17, 3)
    kp_seq[:, :, 2] = 0.8  # 置信度

    # 模拟手腕在击球时速度增加
    impact_frame = 18
    kp_seq[impact_frame-2:impact_frame+2, 10, 0] += 0.1  # 手腕 y 移动

    img_w, img_h = 640, 480

    result = compute_fused_speed(kp_seq, img_w, img_h)
    speed = result["speed_fused"]
    valid = result["valid_mask"]

    print(f"速度曲线形状: {speed.shape}")
    print(f"有效掩码: {valid.sum()}/{len(valid)}")

    for shot_type in ["forehand", "backhand", "serve", "unknown"]:
        impact = pick_impact_frame_by_type(speed, valid, shot_type)
        print(f"{shot_type:10s} -> 击球帧: {impact}")