"""
Detect the impact (击球) frame of each tennis shot video using right-wrist
speed peak from MoveNet Thunder.

Pipeline per video:
  1. Run MoveNet Thunder on every frame, extract right-wrist (x, y, score).
  2. Interpolate/hold low-confidence wrist points, then smooth.
  3. Compute per-frame wrist speed, smooth it.
  4. Pick the global-max speed frame as the impact frame t*.
  5. Save t*-1, t*, t*+1 as annotated JPEGs under impact_check/<video>/.
  6. Save a velocity curve PNG alongside, with the chosen peak marked.

Assumptions (per user):
  - All players are right-handed (use right wrist, COCO-17 idx 10).
  - Each MP4 contains exactly one shot -> global max is a reasonable pick.
  - GPU is available -> use Thunder.

Usage:
  python detect_impact_frame.py --input-dir shots --output-dir impact_check
"""

import os
import glob
import argparse

import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ultralytics (YOLOv8) is an optional dependency. Only imported when --use-yolo
# is passed; otherwise the script behaves exactly as before.
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False


# COCO-17 keypoint indices used by MoveNet
KP_NOSE = 0
KP_LEFT_EYE = 1
KP_RIGHT_EYE = 2
KP_LEFT_EAR = 3
KP_RIGHT_EAR = 4
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

# Thunder expects 256x256 input
THUNDER_INPUT_SIZE = 256
THUNDER_URL = "https://tfhub.dev/google/movenet/singlepose/thunder/4"

# COCO-80 class indices used by YOLOv8 pre-trained weights.
# Both classes are in the standard COCO dataset, so any off-the-shelf
# yolov8*.pt weight file detects them without fine-tuning.
COCO_SPORTS_BALL = 32    # tennis ball falls under this class in COCO
COCO_TENNIS_RACKET = 38


# ---------------------------------------------------------------------------
# Joint angle computation (for pose comparison via DTW)
# ---------------------------------------------------------------------------
#
# 关节角度定义（8 个角度，单位：度）
#
# 角度计算方式：三点夹角，中间点为顶点
# 例如：右肩角 = angle(右肘, 右肩, 右髋)
#      即以右肩为顶点，右肩→右肘 和 右肩→右髋 两条射线的夹角
#
# 索引 | 名称   | 三点定义              | 物理含义                    | 典型值范围
# -----|--------|----------------------|----------------------------|------------
#  0   | 右肩角 | 右肘-右肩-右髋        | 手臂抬起程度（肩外展）       | 0-180°
#  1   | 右肘角 | 右肩-右肘-右腕        | 手臂弯曲程度                | 0-180° (180°=伸直)
#  2   | 右髋角 | 右肩-右髋-右膝        | 上半身前倾/后仰程度          | 160-180°
#  3   | 右膝角 | 右髋-右膝-右踝        | 腿部弯曲程度                | 160-180° (180°=伸直)
#  4   | 左肩角 | 左肘-左肩-左髋        | 同右肩                      | 0-180°
#  5   | 左肘角 | 左肩-左肘-左腕        | 同右肘                      | 0-180°
#  6   | 左髋角 | 左肩-左髋-左膝        | 同右髋                      | 160-180°
#  7   | 左膝角 | 左髋-左膝-左踝        | 同右膝                      | 160-180°
#
# 物理含义解释：
# - 肩角：手臂与躯干的夹角。正手引拍时右肩角约 90-120°（手臂向后拉开）
# - 肘角：前臂与上臂的夹角。伸直 = 180°，弯曲 = 小于 180°
# - 髋角：躯干与大腿的夹角。站直 = 180°，前倾 = 小于 180°
# - 膝角：大腿与小腿的夹角。伸直 = 180°，弯曲 = 小于 180°
#
# ---------------------------------------------------------------------------

def compute_angle(p1, p2, p3):
    """
    Compute the angle at p2 formed by vectors p2→p1 and p2→p3.
    Returns angle in degrees [0, 180].
    If any point is NaN, returns NaN.
    """
    if not (np.isfinite(p1).all() and np.isfinite(p2).all() and np.isfinite(p3).all()):
        return np.nan
    v1 = p1 - p2
    v2 = p3 - p2
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def compute_joint_angles(kp):
    """
    Given a single frame's keypoints (17, 3) from MoveNet [y_norm, x_norm, score],
    compute 8 joint angles for pose comparison.

    Returns:
        angles: (8,) ndarray of angles in degrees. NaN where keypoints missing.
                Order: [右肩, 右肘, 右髋, 右膝, 左肩, 左肘, 左髋, 左膝]
    """
    # Convert normalized (y, x) to pixel-agnostic (x, y) for angle calc.
    # We don't care about actual pixel coords, just relative positions.
    pts = np.zeros((17, 2), dtype=np.float64)
    pts[:, 0] = kp[:, 1]  # x
    pts[:, 1] = kp[:, 0]  # y
    # Mask low-confidence points as NaN
    for i in range(17):
        if kp[i, 2] < 0.2:
            pts[i] = np.nan

    angles = np.zeros(8, dtype=np.float64)
    # Right shoulder: elbow-shoulder-hip
    angles[0] = compute_angle(pts[KP_RIGHT_ELBOW], pts[KP_RIGHT_SHOULDER], pts[KP_RIGHT_HIP])
    # Right elbow: shoulder-elbow-wrist
    angles[1] = compute_angle(pts[KP_RIGHT_SHOULDER], pts[KP_RIGHT_ELBOW], pts[KP_RIGHT_WRIST])
    # Right hip: shoulder-hip-knee
    angles[2] = compute_angle(pts[KP_RIGHT_SHOULDER], pts[KP_RIGHT_HIP], pts[KP_RIGHT_KNEE])
    # Right knee: hip-knee-ankle
    angles[3] = compute_angle(pts[KP_RIGHT_HIP], pts[KP_RIGHT_KNEE], pts[KP_RIGHT_ANKLE])
    # Left shoulder
    angles[4] = compute_angle(pts[KP_LEFT_ELBOW], pts[KP_LEFT_SHOULDER], pts[KP_LEFT_HIP])
    # Left elbow
    angles[5] = compute_angle(pts[KP_LEFT_SHOULDER], pts[KP_LEFT_ELBOW], pts[KP_LEFT_WRIST])
    # Left hip
    angles[6] = compute_angle(pts[KP_LEFT_SHOULDER], pts[KP_LEFT_HIP], pts[KP_LEFT_KNEE])
    # Left knee
    angles[7] = compute_angle(pts[KP_LEFT_HIP], pts[KP_LEFT_KNEE], pts[KP_LEFT_ANKLE])

    return angles


# ---------------------------------------------------------------------------
# MoveNet wrapper
# ---------------------------------------------------------------------------
class MoveNetThunder:
    def __init__(self):
        print("Loading MoveNet Thunder from TF Hub...")
        self.module = hub.load(THUNDER_URL)
        self.model = self.module.signatures["serving_default"]
        print("  ready.")

    def infer(self, frame_bgr):
        """
        Run MoveNet on a single BGR frame.
        Returns a (17, 3) array of [y_norm, x_norm, score] in image coords
        normalized to [0, 1].
        """
        img = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        # Resize with padding preserved by tf.image.resize_with_pad
        inp = tf.expand_dims(img, axis=0)
        inp = tf.image.resize_with_pad(inp, THUNDER_INPUT_SIZE, THUNDER_INPUT_SIZE)
        inp = tf.cast(inp, dtype=tf.int32)
        outputs = self.model(inp)
        # shape (1, 1, 17, 3)
        kp = outputs["output_0"].numpy()[0, 0]
        return kp


# ---------------------------------------------------------------------------
# YOLOv8 ball + racket detector (optional, used for ball-racket proximity
# impact detection). Pre-trained COCO weights detect both classes natively.
# ---------------------------------------------------------------------------
class YoloBallRacketDetector:
    """
    Thin wrapper around ultralytics.YOLO that returns only the ball and
    tennis racket detections we care about.

    Per frame we keep the highest-confidence box for each class (there's
    only one ball and one racket in view during a shot, so this is safe).
    """

    def __init__(self, weights_path, conf=0.20, device=None, imgsz=640):
        if not HAS_YOLO:
            raise RuntimeError(
                "ultralytics is not installed. Run `pip install ultralytics` "
                "to enable YOLO-based impact detection."
            )
        print(f"Loading YOLOv8 weights from {weights_path} ...")
        self.model = YOLO(weights_path)
        self.conf = conf
        self.imgsz = imgsz
        self.device = device   # None lets ultralytics pick (uses GPU if available)
        print("  ready.")

    def infer(self, frame_bgr):
        """
        Detect ball and racket in one BGR frame.

        Returns dict:
            ball:   (cx, cy, conf) or None
            racket: (cx, cy, w, h, conf) or None
        Coordinates are in pixel space. We return racket w/h so downstream
        code can estimate the "near-head" region, since the contact point
        is at the racket head not its centroid.
        """
        # verbose=False keeps per-frame prediction logs out of stdout
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
        xyxy = r.boxes.xyxy.cpu().numpy()     # (N, 4)
        confs = r.boxes.conf.cpu().numpy()    # (N,)

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
                    racket = (float(cx), float(cy),
                              float(bw), float(bh), conf_i)
        return {"ball": ball, "racket": racket}


def compute_ball_racket_distance(detections, img_diag, max_interp_gap=3):
    """
    Given a list of per-frame detection dicts (as returned by
    YoloBallRacketDetector.infer), build the per-frame ball <-> racket
    distance signal used to locate impact.

    YOLO often misses the tennis ball during the very moment it matters
    most — impact — because the ball is moving fastest and smallest relative
    to the racket head. We therefore linearly interpolate short gaps (up
    to `max_interp_gap` frames) in the distance signal, so a 1-2 frame
    ball detection dropout doesn't silently disqualify the true impact.

    Returns:
        dist:        (T,) raw distance, np.inf when ball or racket missing
        dist_interp: (T,) distance after short-gap linear interpolation
        both_mask:   (T,) bool, True only when both objects were RAW-detected
        valid_mask:  (T,) bool, True where dist_interp has a real value
                     (covers both raw detections and successful interpolations)
        ball_xy:     (T, 2) pixel coords of ball center, NaN where missing
        racket_xy:   (T, 2) pixel coords of racket center, NaN where missing
        racket_size: (T,)  diagonal of racket bbox (pixels), NaN where missing

    We don't try to infer the racket HEAD position from the bbox — the
    racket bbox centroid is a stable proxy and matches what the YOLO model
    was trained on. Distance is normalized by the image diagonal so the
    threshold semantics are resolution-agnostic.
    """
    T = len(detections)
    dist = np.full(T, np.inf, dtype=np.float64)
    both = np.zeros(T, dtype=bool)
    ball_xy = np.full((T, 2), np.nan, dtype=np.float64)
    racket_xy = np.full((T, 2), np.nan, dtype=np.float64)
    racket_sz = np.full(T, np.nan, dtype=np.float64)

    for t, det in enumerate(detections):
        b = det.get("ball")
        r = det.get("racket")
        if b is not None:
            ball_xy[t] = (b[0], b[1])
        if r is not None:
            racket_xy[t] = (r[0], r[1])
            racket_sz[t] = float(np.hypot(r[2], r[3]))
        if b is not None and r is not None:
            d_px = float(np.hypot(b[0] - r[0], b[1] - r[1]))
            dist[t] = d_px / max(img_diag, 1.0)
            both[t] = True

    # Short-gap linear interpolation on the distance signal.
    dist_interp = dist.copy()
    valid = both.copy()
    if both.any() and max_interp_gap > 0:
        detected_indices = np.where(both)[0]
        # Walk through consecutive detection pairs; fill gaps <= max_interp_gap.
        for i in range(len(detected_indices) - 1):
            a = detected_indices[i]
            b_idx = detected_indices[i + 1]
            gap = b_idx - a - 1
            if 0 < gap <= max_interp_gap:
                # Linear interpolate distance between a and b_idx.
                da, db = dist[a], dist[b_idx]
                for k in range(1, gap + 1):
                    frac = k / (gap + 1)
                    dist_interp[a + k] = da + frac * (db - da)
                    valid[a + k] = True

    return {
        "dist": dist,
        "dist_interp": dist_interp,
        "both_mask": both,       # raw: both objects actually detected
        "valid_mask": valid,     # raw OR successfully interpolated
        "ball_xy": ball_xy,
        "racket_xy": racket_xy,
        "racket_sz": racket_sz,
    }


def pick_impact_by_proximity(prox, speed_fused,
                             head_pad=0, tail_pad=0,
                             dist_floor=0.005):
    """
    Pick the impact frame by maximizing a joint score that favors frames
    where the player is swinging fast AND the ball is close to the racket:

            norm_speed[t] = (speed[t] - min_speed) / (max_speed - min_speed)
            norm_proximity[t] = (max_dist - dist[t]) / (max_dist - min_dist)
            score[t] = 0.3*norm_speed[t] + 0.7*norm_proximity[t]

    where min_speed/max_speed and min_dist/max_dist are computed over
    valid frames (ball+racket distance available). This scores the two
    physics of impact together. A rhythm-swing peak has high speed but
    also large distance, so it loses. A ball passing by while the arm is
    idle has low distance but low speed, so it also loses. Only a frame
    where the arm is accelerating AND the ball is at the racket head wins.

    We search across the entire video (minus head/tail pad), not a subset
    of pre-chosen velocity peaks, because with the joint signal there's
    no need for a shot-type-specific search window — the physics itself
    filters the candidates.

    `dist_floor` is kept for backward compatibility but no longer used in
    the scoring formula.

    Returns:
        (impact_idx, info_dict, score_array). impact_idx is None iff no frame in the
        allowed window has a valid interpolated distance. score_array is the computed
        joint score for each frame (invalid frames have -inf, head/tail excluded).
    """
    T = len(speed_fused)
    dist = prox["dist_interp"]
    valid = prox["valid_mask"]

    # Build the score array. Invalid frames get -inf so they're never chosen.
    score = np.full(T, -np.inf, dtype=np.float64)

    # Get valid frames for normalization
    valid_indices = np.where(valid)[0]
    if len(valid_indices) == 0:
        return None, {
            "reason": "no valid ball+racket distance",
            "score_max": None,
        }, None

    valid_speeds = speed_fused[valid]
    valid_dists = dist[valid]

    min_speed = np.min(valid_speeds)
    max_speed = np.max(valid_speeds)
    speed_range = max_speed - min_speed

    min_dist = np.min(valid_dists)
    max_dist = np.max(valid_dists)
    dist_range = max_dist - min_dist

    for t in range(T):
        if not valid[t]:
            continue

        # Normalize speed [0, 1]
        if speed_range > 0:
            norm_speed = (speed_fused[t] - min_speed) / speed_range
        else:
            norm_speed = 0.5

        # Normalize proximity: higher = closer (distance smaller)
        if dist_range > 0:
            norm_proximity = (max_dist - dist[t]) / dist_range
        else:
            norm_proximity = 0.5

        # Combined score: weighted average favoring proximity (70% distance, 30% speed)
        score[t] = 0.3*norm_speed + 0.7*norm_proximity

    # Apply head/tail exclusion (same convention as pick_impact_frame).
    head = max(0, int(head_pad))
    tail = max(0, int(tail_pad))
    if head > 0:
        score[:head] = -np.inf
    if tail > 0:
        score[-tail:] = -np.inf

    if np.all(np.isneginf(score)):
        return None, {
            "reason": "no valid ball+racket distance in allowed window",
            "score_max": None,
        }, None

    best = int(np.argmax(score))
    return best, {
        "reason": "joint speed/dist argmax",
        "score_max": float(score[best]),
        "speed_at_best": float(speed_fused[best]),
        "dist_at_best": float(dist[best]),
        "interpolated": bool(valid[best] and not prox["both_mask"][best]),
    }, score


# ---------------------------------------------------------------------------
# Signal processing helpers
# ---------------------------------------------------------------------------
def fill_low_confidence(xy, score, thresh=0.2):
    """
    Replace low-confidence points by linear interpolation along time.
    xy: (T, 2), score: (T,). Returns xy_filled (T, 2), valid_mask (T,).
    """
    T = len(score)
    valid = score >= thresh
    xy_filled = xy.copy().astype(np.float64)

    if not valid.any():
        return xy_filled, valid

    idx = np.arange(T)
    for dim in range(2):
        good = valid
        if good.sum() >= 2:
            xy_filled[:, dim] = np.interp(idx, idx[good], xy[good, dim])
        else:
            # only 1 good frame: hold it
            xy_filled[:, dim] = xy[good, dim][0]
    return xy_filled, valid


def moving_average(a, k):
    """Centered moving average; edges use shrinking window."""
    if k <= 1:
        return a.copy()
    T = len(a)
    out = np.empty_like(a, dtype=np.float64)
    half = k // 2
    for i in range(T):
        lo = max(0, i - half)
        hi = min(T, i + half + 1)
        out[i] = np.mean(a[lo:hi])
    return out


def _compute_joint_speed(kp_seq, kp_index, img_w, img_h,
                         smooth_xy=3, smooth_v=3, score_thresh=0.2):
    """
    Compute per-frame pixel speed for a single MoveNet keypoint.

    Returns dict with:
      xy_px:        (T, 2) interpolated pixel coords (before smoothing)
      xy_smooth:    (T, 2) smoothed pixel coords
      speed_raw:    (T,) raw speed magnitude
      speed_smooth: (T,) smoothed speed magnitude
      score:        (T,) MoveNet confidence
      valid_mask:   (T,) bool, True where score >= score_thresh
    """
    T = kp_seq.shape[0]
    yx = kp_seq[:, kp_index, :2]      # normalized (y, x)
    score = kp_seq[:, kp_index, 2]

    xy_px = np.zeros((T, 2), dtype=np.float64)
    xy_px[:, 0] = yx[:, 1] * img_w    # x
    xy_px[:, 1] = yx[:, 0] * img_h    # y

    xy_filled, valid = fill_low_confidence(xy_px, score, thresh=score_thresh)

    xy_smooth = np.zeros_like(xy_filled)
    xy_smooth[:, 0] = moving_average(xy_filled[:, 0], smooth_xy)
    xy_smooth[:, 1] = moving_average(xy_filled[:, 1], smooth_xy)

    diff = np.diff(xy_smooth, axis=0)
    speed = np.sqrt((diff ** 2).sum(axis=1))
    speed = np.concatenate([[0.0], speed])   # align so speed[t] is from t-1 to t
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
    Fuse right-wrist and right-elbow speeds into a single signal, weighted by
    per-frame MoveNet confidences.

    Rationale: MoveNet sometimes misplaces the wrist onto a different body
    part (non-dominant hand, background clutter). The elbow is usually more
    stable and its speed peak tracks the wrist's to within a couple of
    frames during a tennis swing, so fusing them recovers the true impact
    frame even when the wrist is momentarily unreliable.

    Fusion (per frame t):
        w_wrist_t = wrist_prior * score_wrist[t]
        w_elbow_t = (1 - wrist_prior) * score_elbow[t]
        v_fused[t] = (w_wrist_t * v_wrist[t] + w_elbow_t * v_elbow[t])
                     / (w_wrist_t + w_elbow_t + eps)

    Returns dict containing the per-joint breakdowns plus the fused signal,
    which downstream code (peak picker, curve plot) uses as the primary input.
    """
    wrist = _compute_joint_speed(kp_seq, KP_RIGHT_WRIST, img_w, img_h,
                                 smooth_xy, smooth_v, score_thresh)
    elbow = _compute_joint_speed(kp_seq, KP_RIGHT_ELBOW, img_w, img_h,
                                 smooth_xy, smooth_v, score_thresh)

    T = len(wrist["speed_smooth"])
    eps = 1e-6

    w_wrist = wrist_prior * np.clip(wrist["score"], 0.0, 1.0)
    w_elbow = (1.0 - wrist_prior) * np.clip(elbow["score"], 0.0, 1.0)
    w_sum = w_wrist + w_elbow + eps

    speed_fused = (w_wrist * wrist["speed_smooth"]
                   + w_elbow * elbow["speed_smooth"]) / w_sum

    # A frame is "valid" for peak selection if at least one joint had decent
    # confidence there. This is looser than requiring both joints valid.
    valid_fused = wrist["valid_mask"] | elbow["valid_mask"]

    return {
        # Fused signal — the one used by pick_impact_frame.
        "speed_fused": speed_fused,
        "valid_mask": valid_fused,

        # Keep per-joint signals for plotting and debugging.
        "wrist": wrist,
        "elbow": elbow,

        # Back-compat keys so old drawing/CSV code stays simple; these point
        # to the wrist since that's what we visualize on the frame.
        "wrist_xy_px": wrist["xy_px"],
        "wrist_score": wrist["score"],
    }


def _find_local_maxima(signal, min_distance=3):
    """
    Return indices of local maxima, each separated by at least min_distance.
    Simple O(T) scan: a point is a local max if it's >= its neighbors and
    strictly greater than at least one side (handles short plateaus).
    """
    T = len(signal)
    peaks = []
    for i in range(1, T - 1):
        left = signal[i] > signal[i - 1]
        right = signal[i] > signal[i + 1]
        left_eq = signal[i] >= signal[i - 1]
        right_eq = signal[i] >= signal[i + 1]
        if (left and right_eq) or (left_eq and right):
            # enforce min distance to previous kept peak
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)
            else:
                # keep the higher of the two
                if signal[i] > signal[peaks[-1]]:
                    peaks[-1] = i
    return peaks


def pick_impact_frame(
    speed,
    valid_mask,
    head_pad_ratio=0.20,
    tail_pad_ratio=0.20,
    mode="global_max",
    peak_prominence_ratio=0.5,
    min_peak_distance=3,
    early_skip_threshold=15,
    backhand_first_22_limit=22,
    forehand_10_30_start=10,
    forehand_10_30_end=30,
    frame_range_start=None,
    frame_range_end=None,
):
    """
    Pick the impact frame from the smoothed wrist-speed signal.

    Args:
        speed: (T,) smoothed wrist speed (or fused wrist+elbow speed).
        valid_mask: (T,) boolean; False frames are excluded from selection.
        head_pad_ratio: fraction of T at the start to ignore.
        tail_pad_ratio: fraction of T at the end to ignore.
        mode:
          - 'global_max': pick the argmax within the allowed window. Safe
            default for unknown shots.
          - 'first_peak': pick the FIRST significant local maximum.
          - 'middle_peak': pick the MIDDLE significant local maximum. Used
            for forehands.
          - 'last_peak': pick the LAST significant local maximum. Used for
            serves.
          - 'backhand_early_skip': reserved for backhands. If the first
            significant peak appears at or before `early_skip_threshold`,
            it is likely the take-back crest, so we skip to the SECOND
            significant peak. Otherwise (first peak is late enough to be
            the real impact) we pick the first significant peak. Falls back
            to first_peak semantics when only one peak exists.
        peak_prominence_ratio: a local peak must be >= this fraction of the
            in-window global max to count as "significant".
        min_peak_distance: minimum separation between detected local peaks.
        early_skip_threshold: frame index boundary for 'backhand_early_skip'.
            Peaks at frames <= this value are considered "too early" and
            skipped. Default 15 — tuned for 30-40 frame backhand clips where
            true impact typically lands around frame 20+.

    Returns:
        int frame index of the chosen impact.
    """
    T = len(speed)
    head = max(1, int(T * head_pad_ratio))
    tail = max(1, int(T * tail_pad_ratio))

    candidate = speed.copy().astype(np.float64)
    candidate[:head] = -np.inf
    candidate[-tail:] = -np.inf
    candidate[~valid_mask] = -np.inf

    # Apply frame range restriction if specified
    if frame_range_start is not None:
        start = max(0, frame_range_start)
        candidate[:start] = -np.inf
    if frame_range_end is not None:
        end = min(T, frame_range_end)
        candidate[end:] = -np.inf

    # If the window zeroed out (very short video, all-invalid, etc.), fall
    # back to the raw argmax over everything we have.
    if np.all(np.isneginf(candidate)):
        return int(np.argmax(speed))

    if mode == "global_max":
        return int(np.argmax(candidate))

    if mode == "global_max_raw":
        # 完全忽略头尾排除和有效掩码，直接在整个视频中取速度最大值
        # 但仍考虑范围限制
        raw_candidate = speed.copy().astype(np.float64)
        if frame_range_start is not None:
            start = max(0, frame_range_start)
            raw_candidate[:start] = -np.inf
        if frame_range_end is not None:
            end = min(T, frame_range_end)
            raw_candidate[end:] = -np.inf
        if np.all(np.isneginf(raw_candidate)):
            return int(np.argmax(speed))
        return int(np.argmax(raw_candidate))

    if mode in ("last_peak", "first_peak", "middle_peak",
                "backhand_early_skip", "backhand_first_22", "forehand_10_30"):
        # Scan for local maxima on a version of the signal where excluded
        # regions are replaced by a low finite value (so they never look
        # like peaks themselves but also don't break the neighbor scan).
        finite = candidate.copy()
        low = np.min(speed) - 1.0
        finite[np.isneginf(finite)] = low

        peaks = _find_local_maxima(finite, min_distance=min_peak_distance)
        peaks = [p for p in peaks if head <= p < T - tail and valid_mask[p]]

        if not peaks:
            # No local peak inside the window; fall back to in-window argmax.
            return int(np.argmax(candidate))

        in_window_max = float(np.max(candidate))
        threshold = peak_prominence_ratio * in_window_max
        significant = [p for p in peaks if speed[p] >= threshold]

        # Choose the pool: prefer significant peaks, fall back to all peaks
        # (which are already sorted in time by _find_local_maxima).
        pool = significant if significant else peaks

        if mode == "last_peak":
            # Serves: impact comes after toss and back-swing crest.
            return int(pool[-1])
        if mode == "first_peak":
            # Backhands (simple mode): impact comes before follow-through.
            return int(pool[0])
        if mode == "middle_peak":
            # Forehands. With an even count we bias toward the later of
            # the two central peaks (preparation tends to be longer than
            # follow-through in practice).
            mid_idx = len(pool) // 2
            return int(pool[mid_idx])
        if mode == "backhand_first_22":
            # Backhand: take the highest speed frame within first 22 frames
            # Search within the first 22 frames (0-indexed, so frames 0-21)
            search_end = min(backhand_first_22_limit, T)
            if search_end <= 0:
                # Fallback to global max if limit is invalid
                return int(np.argmax(candidate))
            # Consider only valid frames within the range
            valid_in_range = [i for i in range(search_end) if valid_mask[i] and candidate[i] > -np.inf]
            if not valid_in_range:
                # Fallback to global max if no valid frames in range
                return int(np.argmax(candidate))
            # Find frame with maximum speed in the range
            max_idx = max(valid_in_range, key=lambda i: speed[i])
            return int(max_idx)
        if mode == "forehand_10_30":
            # Forehand: take the highest speed frame between frames 10 and 30
            start = forehand_10_30_start
            end = min(forehand_10_30_end, T)
            if start >= end:
                # Fallback to global max if range is invalid
                return int(np.argmax(candidate))
            # Consider only valid frames within the range
            valid_in_range = [i for i in range(start, end) if valid_mask[i] and candidate[i] > -np.inf]
            if not valid_in_range:
                # Fallback to global max if no valid frames in range
                return int(np.argmax(candidate))
            # Find frame with maximum speed in the range
            max_idx = max(valid_in_range, key=lambda i: speed[i])
            return int(max_idx)
        # backhand_early_skip:
        # If the first peak lands too early, it's likely the take-back
        # crest rather than impact. Skip to peak #2 if available.
        if pool[0] <= early_skip_threshold and len(pool) >= 2:
            return int(pool[1])
        return int(pool[0])

    # Unknown mode: behave like global_max.
    return int(np.argmax(candidate))


def shot_type_from_name(name):
    """Cheap keyword-based shot type detector (matches the old pipeline)."""
    lower = name.lower()
    if "serve" in lower or "发" in name:
        return "serve"
    if "forehand" in lower or "正" in name:
        return "forehand"
    if "backhand" in lower or "反" in name:
        return "backhand"
    return "unknown"


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _load_cn_font(size=26):
    if not HAS_PIL:
        return None
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def annotate_frame(frame_bgr, lines, wrist_px=None, elbow_px=None,
                   ball_xy=None, racket_xy=None, racket_size=None):
    """Overlay text + markers. Wrist yellow, elbow cyan, ball magenta, racket green."""
    out = frame_bgr.copy()

    # Racket bbox centroid + approximate bbox outline (so we can see the
    # racket extent relative to the ball).
    if racket_xy is not None and np.isfinite(racket_xy).all():
        rx, ry = int(racket_xy[0]), int(racket_xy[1])
        cv2.circle(out, (rx, ry), 10, (0, 255, 0), 2)   # green ring
        if racket_size is not None and np.isfinite(racket_size):
            half = int(racket_size / 2 / 1.414)  # diagonal -> approx half-side
            cv2.rectangle(out, (rx - half, ry - half), (rx + half, ry + half),
                          (0, 200, 0), 1)
    # Ball: bright magenta to be unmistakable.
    if ball_xy is not None and np.isfinite(ball_xy).all():
        bx, by = int(ball_xy[0]), int(ball_xy[1])
        cv2.circle(out, (bx, by), 8, (255, 0, 255), 2)
        cv2.circle(out, (bx, by), 2, (255, 255, 255), -1)

    # Draw elbow first so the wrist marker sits on top if they overlap.
    if elbow_px is not None and np.isfinite(elbow_px).all():
        x, y = int(elbow_px[0]), int(elbow_px[1])
        cv2.circle(out, (x, y), 7, (255, 255, 0), 2)   # cyan ring
        cv2.circle(out, (x, y), 2, (0, 0, 255), -1)
    if wrist_px is not None and np.isfinite(wrist_px).all():
        x, y = int(wrist_px[0]), int(wrist_px[1])
        cv2.circle(out, (x, y), 8, (0, 255, 255), 2)   # yellow ring
        cv2.circle(out, (x, y), 2, (0, 0, 255), -1)

    if HAS_PIL:
        pil = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        font = _load_cn_font(26)
        x0, y0 = 12, 12
        lh = 32
        for i, line in enumerate(lines):
            pos = (x0, y0 + i * lh)
            # outline
            for dx in (-2, -1, 1, 2):
                for dy in (-2, -1, 1, 2):
                    draw.text((pos[0] + dx, pos[1] + dy), line, font=font, fill=(0, 0, 0))
            draw.text(pos, line, font=font, fill=(255, 255, 255))
        out = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    else:
        # ASCII fallback
        y = 30
        for line in lines:
            ascii_line = line.encode("ascii", "ignore").decode("ascii")
            cv2.putText(out, ascii_line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(out, ascii_line, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2, cv2.LINE_AA)
            y += 30
    return out


def save_velocity_curve(fused, wrist, elbow, impact_idx, out_path, title,
                        head_pad=0, tail_pad=0, all_peaks=None,
                        proximity=None, speed_only_impact_idx=None,
                        joint_score=None, top_k=3):
    """
    Plot the three speed curves (wrist, elbow, fused) on one axis. If
    `proximity` is provided (dict from compute_ball_racket_distance), the
    ball-racket distance is overlaid on a second y-axis on the right — low
    distance + speed peak = true impact, while rhythm swings show tall
    speed peaks with HIGH distance (ball not at racket).

      - fused:            solid blue (primary, left axis)
      - wrist:            thin grey (left axis)
      - elbow:            thin orange (left axis)
      - ball-racket dist: green (right axis, only when YOLO was used)
      - joint score:      purple dashed (left axis, normalized, only when YOLO was used)
      - red dashed line:  chosen final impact
      - pink dashed line: speed-only pick (drawn only if YOLO changed it)
      - light grey dots:  every local maximum of the fused curve
      - grey bands:       head/tail regions excluded from peak search
      - purple stars:     top K joint score candidates (only when YOLO was used)
    """
    T = len(fused)
    fig, ax1 = plt.subplots(figsize=(10.5, 4.0))

    ax1.plot(wrist, linewidth=0.9, color="#888888", alpha=0.8,
             label="wrist speed (smoothed)")
    ax1.plot(elbow, linewidth=0.9, color="#d78c33", alpha=0.8,
             label="elbow speed (smoothed)")
    ax1.plot(fused, linewidth=1.6, color="#1f77b4",
             label="fused speed (used for selection)")

    # Plot joint score (speed / distance) if provided
    if joint_score is not None:
        # Normalize joint score to [0, 1] for plotting on same scale
        valid_scores = joint_score[np.isfinite(joint_score)]
        if len(valid_scores) > 0:
            score_min = np.min(valid_scores)
            score_max = np.max(valid_scores)
            if score_max > score_min:
                normalized = (joint_score - score_min) / (score_max - score_min)
                # Replace NaN/Inf with 0 for plotting
                normalized_clean = np.where(np.isfinite(normalized), normalized, 0)
                ax1.plot(normalized_clean, linewidth=1.2, color="#8a2be2",
                         linestyle="--", alpha=0.7,
                         label="joint score (speed/dist, normalized)")
                # Mark top K joint score candidates
                # Get valid scores (finite values)
                valid_mask = np.isfinite(joint_score)
                valid_indices = np.where(valid_mask)[0]
                valid_values = joint_score[valid_mask]

                if len(valid_values) > 0:
                    # Sort indices by score descending
                    sorted_idx = valid_indices[np.argsort(valid_values)[::-1]]
                    # Take top K (or all if fewer available)
                    k = min(top_k, len(sorted_idx))
                    top_k_indices = sorted_idx[:k]

                    # Mark each top candidate
                    for i, idx in enumerate(top_k_indices, 1):
                        marker_size = 80 if i == 1 else 60  # Largest for rank 1
                        alpha = 1.0 if i == 1 else 0.8
                        label = f"joint score rank {i} @ {idx}" if i == 1 else None
                        ax1.scatter([idx], [normalized_clean[idx]],
                                   color="#8a2be2", marker="*", s=marker_size,
                                   zorder=7, alpha=alpha, label=label)

    if head_pad > 0:
        ax1.axvspan(0, head_pad, color="grey", alpha=0.12,
                    label=f"excluded head ({head_pad}f)")
    if tail_pad > 0:
        ax1.axvspan(T - tail_pad, T, color="grey", alpha=0.12,
                    label=f"excluded tail ({tail_pad}f)")

    if all_peaks:
        ys = [fused[p] for p in all_peaks]
        ax1.scatter(all_peaks, ys, s=22, color="#666666", zorder=4,
                    label=f"fused local peaks ({len(all_peaks)})")

    # If YOLO moved the pick, show both positions so the shift is visible.
    if (speed_only_impact_idx is not None
            and speed_only_impact_idx != impact_idx):
        ax1.axvline(speed_only_impact_idx, color="#c2185b", linestyle=":",
                    linewidth=1.0,
                    label=f"speed-only pick @ {speed_only_impact_idx}")

    ax1.axvline(impact_idx, color="red", linestyle="--", linewidth=1.2,
                label=f"impact @ frame {impact_idx}")
    ax1.scatter([impact_idx], [fused[impact_idx]], color="red", zorder=6, s=40)

    ax1.set_xlabel("frame")
    ax1.set_ylabel("speed (px/frame)")

    # Second axis: ball-racket distance + joint score.
    if proximity is not None:
        ax2 = ax1.twinx()
        dist_raw = proximity["dist"].copy()
        dist_interp = proximity["dist_interp"].copy()
        both = proximity["both_mask"]
        valid = proximity["valid_mask"]

        # Interpolated segments are drawn lighter/dashed so you can tell
        # at a glance which distance values came from raw YOLO detections
        # vs. from filling gaps.
        interp_plot = np.where(valid, dist_interp, np.nan)
        raw_plot = np.where(both, dist_raw, np.nan)
        ax2.plot(interp_plot, linewidth=1.0, color="#2ca02c", alpha=0.45,
                 linestyle="--",
                 label="ball<->racket dist (gap-filled)")
        ax2.plot(raw_plot, linewidth=1.5, color="#2ca02c",
                 label="ball<->racket dist (raw)")
        ax2.scatter(np.where(both)[0], dist_raw[both], s=12, color="#2ca02c",
                    alpha=0.7, zorder=5)

        ax2.set_ylabel("normalized distance", color="#2ca02c")
        ax2.tick_params(axis="y", labelcolor="#2ca02c")
        # Invert so "smaller distance = higher on plot" matches the
        # "impact = peak" intuition of the speed curve.
        ax2.set_ylim(ax2.get_ylim()[::-1])

        # Merge legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2,
                   loc="upper right", fontsize=7)
    else:
        ax1.legend(loc="upper right", fontsize=7)

    ax1.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main per-video routine
# ---------------------------------------------------------------------------
def process_video(video_path, output_root, model, score_thresh=0.2,
                  smooth_xy=3, smooth_v=3, save_context=1,
                  head_pad_ratio=0.20, tail_pad_ratio=0.20,
                  wrist_prior=0.7, mode_override=None,
                  frame_range_start=None, frame_range_end=None,
                  yolo=None, proximity_interp_gap=3, proximity_dist_floor=0.005,
                  save_top_k=0):
    name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = os.path.join(output_root, name)
    os.makedirs(out_dir, exist_ok=True)

    valid_frames = None  # Number of frames with valid ball-racket distance

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [skip] cannot open {video_path}")
        return None

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    shot_type = shot_type_from_name(name)
    print(f"\n--- {name} | {total} frames @ {fps:.1f} fps | {w}x{h} | type={shot_type} ---")

    if total <= 2:
        print("  [skip] video too short")
        cap.release()
        return None

    # Pass 1: MoveNet inference on every frame (+ YOLO if enabled). We cache
    # keypoints and detections here so later passes don't have to re-read the
    # video twice.
    kp_seq = np.zeros((total, 17, 3), dtype=np.float32)
    yolo_detections = [] if yolo is not None else None
    for i in range(total):
        ret, frame = cap.read()
        if not ret:
            # pad the rest as zeros (low confidence)
            kp_seq = kp_seq[:i]
            total = i
            break
        kp_seq[i] = model.infer(frame)
        if yolo is not None:
            yolo_detections.append(yolo.infer(frame))
    cap.release()

    if total < 3:
        print("  [skip] fewer than 3 decoded frames")
        return None

    # Signals — fuse right wrist + right elbow speeds.
    sig = compute_fused_speed(kp_seq, img_w=w, img_h=h,
                              smooth_xy=smooth_xy, smooth_v=smooth_v,
                              score_thresh=score_thresh,
                              wrist_prior=wrist_prior)

    # Peak selection mode depends on shot type (can be overridden by mode_override):
    #   - serve:    last_peak           (toss / back-swing crest precede impact)
    #   - forehand: forehand_10_30      (highest speed between frames 10-30)
    #   - backhand: backhand_first_22   (highest speed within first 22 frames)
    #   - unknown:  global_max
    if mode_override is not None:
        pick_mode = mode_override
    else:
        if shot_type == "serve":
            pick_mode = "last_peak"
        elif shot_type == "forehand":
            pick_mode = "forehand_10_30"
        elif shot_type == "backhand":
            pick_mode = "backhand_first_22"
        else:
            pick_mode = "global_max"

    impact_idx = pick_impact_frame(
        sig["speed_fused"], sig["valid_mask"],
        head_pad_ratio=head_pad_ratio,
        tail_pad_ratio=tail_pad_ratio,
        mode=pick_mode,
        peak_prominence_ratio=0.5,
        min_peak_distance=3,
        early_skip_threshold=15,
        backhand_first_22_limit=22,
        forehand_10_30_start=10,
        forehand_10_30_end=30,
        frame_range_start=frame_range_start,
        frame_range_end=frame_range_end,
    )
    speed_only_impact_idx = impact_idx

    # Optional YOLO refinement. With the joint speed/dist score we no
    # longer need shot_type-specific search windows (backhand_first_22,
    # forehand_10_30, etc.) — the physics of "fast swing AND ball at
    # racket" is enough to pick the right frame across the whole video.
    prox = None
    proximity_info = None
    joint_score = None
    if yolo is not None and yolo_detections is not None:
        img_diag = float(np.hypot(w, h))
        prox = compute_ball_racket_distance(
            yolo_detections, img_diag,
            max_interp_gap=proximity_interp_gap,
        )

        # Use the SAME head/tail pad the speed stage used, so the two are
        # consistent. Everything between head and tail is fair game — the
        # shot_type-specific narrow windows are ignored when YOLO is on.
        head_f = max(1, int(total * head_pad_ratio))
        tail_f = max(1, int(total * tail_pad_ratio))

        refined, info, joint_score = pick_impact_by_proximity(
            prox, sig["speed_fused"],
            head_pad=head_f, tail_pad=tail_f,
            dist_floor=proximity_dist_floor,
        )
        proximity_info = info
        both_frames = int(prox["both_mask"].sum())
        interp_frames = int(prox["valid_mask"].sum() - both_frames)
        valid_frames = both_frames + interp_frames

        if valid_frames < 10:
            print(f"  YOLO: only {valid_frames} valid distance frames (<10), using YOLO+speed score anyway")

        if refined is not None:
            impact_idx = refined
            pick_mode = f"{pick_mode}+yolo"
            tag = " (interpolated)" if info.get("interpolated") else ""
            print(f"  YOLO refinement: impact {speed_only_impact_idx} -> "
                  f"{impact_idx}{tag}  "
                  f"(score={info['score_max']:.2f}, "
                  f"speed={info['speed_at_best']:.2f}, "
                  f"dist={info['dist_at_best']:.4f}, "
                  f"detected={both_frames}/{total}, "
                  f"interpolated_gaps={interp_frames})")
        else:
            print(f"  YOLO refinement: skipped ({info['reason']}), "
                  f"keeping speed-based pick {speed_only_impact_idx}  "
                  f"(detected={both_frames}/{total})")

    wrist_score_at_impact = float(sig["wrist"]["score"][impact_idx])
    elbow_score_at_impact = float(sig["elbow"]["score"][impact_idx])
    impact_speed_fused = float(sig["speed_fused"][impact_idx])
    valid_ratio = float(sig["valid_mask"].mean())

    print(f"  impact frame = {impact_idx} / {total - 1}  "
          f"(mode={pick_mode}, v_fused={impact_speed_fused:.2f}px, "
          f"v_wrist={sig['wrist']['speed_smooth'][impact_idx]:.2f}, "
          f"v_elbow={sig['elbow']['speed_smooth'][impact_idx]:.2f}, "
          f"wrist_score={wrist_score_at_impact:.2f}, "
          f"elbow_score={elbow_score_at_impact:.2f}, "
          f"valid={valid_ratio:.2f})")

    # Head/tail exclusion frames (used for both plotting and top-k selection)
    head_pad_frames = max(1, int(total * head_pad_ratio))
    tail_pad_frames = max(1, int(total * tail_pad_ratio))

    # Score array for plotting (purple stars)
    plot_score_array = None
    if joint_score is not None:
        plot_score_array = joint_score  # Use YOLO joint score if available

    # Pass 2: re-open to grab impact frame and +/- context, or top K frames.
    cap = cv2.VideoCapture(video_path)
    saved = []

    # Determine which frames to save
    if save_top_k > 0:
        # Build score arrays for ranking
        score_arrays = {}
        score_labels = {}

        # Always compute speed score array
        speed = sig["speed_fused"]
        # Normalize speed to [0, 1]
        valid_speed = speed[head_pad_frames:total - tail_pad_frames]
        if len(valid_speed) > 0:
            min_s = np.min(valid_speed)
            max_s = np.max(valid_speed)
            speed_range = max_s - min_s
            if speed_range > 0:
                speed_norm = (speed - min_s) / speed_range
            else:
                speed_norm = np.full_like(speed, 0.5, dtype=np.float64)
        else:
            speed_norm = np.full_like(speed, 0.5, dtype=np.float64)
        # Set head/tail excluded regions to -inf
        speed_score_array = np.full_like(speed_norm, -np.inf, dtype=np.float64)
        speed_score_array[head_pad_frames:total - tail_pad_frames] = speed_norm[head_pad_frames:total - tail_pad_frames]
        score_arrays['speed'] = speed_score_array
        score_labels['speed'] = '速度评分'

        # If YOLO joint score is available, use it
        if joint_score is not None:
            score_arrays['joint'] = joint_score.copy()
            score_labels['joint'] = '综合评分'

        # Determine which score arrays to use for frame selection
        # If YOLO has few valid frames (<10), use both joint and speed scores
        # Otherwise, use only joint score (if available) or speed score
        arrays_to_use = []
        if joint_score is not None:
            if valid_frames is not None and valid_frames < 10:
                # Few YOLO detections: use both scores
                arrays_to_use = [('joint', score_arrays['joint']), ('speed', score_arrays['speed'])]
            else:
                # Enough YOLO detections: use only joint score
                arrays_to_use = [('joint', score_arrays['joint'])]
        else:
            # No YOLO score: use only speed score
            arrays_to_use = [('speed', score_arrays['speed'])]

        # Collect top K frames from each selected score array
        all_top_k_frames = []
        frame_sources = {}  # Map frame index to (score_type, rank, score_value)

        for score_type, score_array in arrays_to_use:
            # Select top K frames based on score array
            # Exclude -inf scores (invalid or excluded)
            valid_scores = score_array.copy()
            valid_scores[np.isneginf(valid_scores)] = np.nan
            # Get indices sorted by score descending
            sorted_indices = np.argsort(valid_scores)[::-1]  # descending
            # Take first K that are not NaN
            top_k_indices = []
            for idx in sorted_indices:
                if not np.isnan(valid_scores[idx]) and len(top_k_indices) < save_top_k:
                    top_k_indices.append(idx)

            # Store frames with their metadata
            for rank, idx in enumerate(top_k_indices, start=1):
                if idx not in frame_sources:  # Avoid duplicates, keep first occurrence
                    frame_sources[idx] = (score_type, rank, valid_scores[idx])
                    all_top_k_frames.append(idx)

        # Sort frames by frame number for consistent output
        all_top_k_frames.sort()
        frames_to_save = all_top_k_frames
        use_top_k = True

        # For plotting, use joint score if available, otherwise speed score
        plot_score_array = joint_score if joint_score is not None else speed_score_array
        # For labeling in images, we need to know which score array was used for each frame
        ranking_info = frame_sources  # Will be used in the loop to label frames
    else:
        # Use context frames around impact
        frames_to_save = [impact_idx + offset for offset in range(-save_context, save_context + 1)]
        frames_to_save = [idx for idx in frames_to_save if 0 <= idx < total]
        use_top_k = False
        ranking_score_array = None

    # Prepare metadata for top-k frames
    frame_metadata = None
    score_labels_map = {'speed': '速度评分', 'joint': '综合评分'}
    if use_top_k:
        frame_metadata = ranking_info  # Defined in the save-top-k block

    for loop_rank, idx in enumerate(frames_to_save, start=1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        offset = idx - impact_idx
        if use_top_k:
            # Get score type and rank from metadata
            if frame_metadata and idx in frame_metadata:
                score_type, rank_in_score, score_value = frame_metadata[idx]
                tag = f"{score_type}_top{rank_in_score}"
                score_label = score_labels_map.get(score_type, '评分')
            else:
                # Fallback (should not happen)
                score_type = 'unknown'
                rank_in_score = loop_rank
                score_value = plot_score_array[idx] if plot_score_array is not None else 0.0
                tag = f"top{loop_rank}"
                score_label = '评分'
        else:
            tag = {-1: "前", 0: "中", 1: "后"}.get(offset, f"{offset:+d}")
            score_type = None
            rank_in_score = None
            score_value = None

        wrist_px = sig["wrist"]["xy_px"][idx]
        elbow_px = sig["elbow"]["xy_px"][idx]
        v_f = sig["speed_fused"][idx]
        v_w = sig["wrist"]["speed_smooth"][idx]
        v_e = sig["elbow"]["speed_smooth"][idx]
        sc_w = sig["wrist"]["score"][idx]
        sc_e = sig["elbow"]["score"][idx]
        if use_top_k:
            lines = [
                f"{name}",
                f"击球{tag}  frame={idx}/{total-1}",
                f"融合速度={v_f:.1f}  腕={v_w:.1f}({sc_w:.2f})  肘={v_e:.1f}({sc_e:.2f})",
            ]
            # Add rank and score
            if score_value is not None:
                lines.append(f"排名第{rank_in_score}  {score_label}={score_value:.3f}")
        else:
            lines = [
                f"{name}",
                f"击球{tag}  frame={idx}/{total-1}  offset={offset:+d}",
                f"融合速度={v_f:.1f}  腕={v_w:.1f}({sc_w:.2f})  肘={v_e:.1f}({sc_e:.2f})",
            ]

        ball_xy = None
        racket_xy = None
        racket_size = None
        if prox is not None:
            if prox["both_mask"][idx]:
                d = prox["dist"][idx]
                lines.append(f"球拍距离={d:.3f}  (both detected)")
            else:
                has_b = np.isfinite(prox["ball_xy"][idx]).all()
                has_r = np.isfinite(prox["racket_xy"][idx]).all()
                lines.append(f"YOLO: 球={'OK' if has_b else '缺'}  "
                             f"拍={'OK' if has_r else '缺'}")
            ball_xy = prox["ball_xy"][idx]
            racket_xy = prox["racket_xy"][idx]
            racket_size = prox["racket_sz"][idx]

        annotated = annotate_frame(frame, lines,
                                   wrist_px=wrist_px, elbow_px=elbow_px,
                                   ball_xy=ball_xy, racket_xy=racket_xy,
                                   racket_size=racket_size)
        if use_top_k:
            fname = f"impact_{tag}_frame{idx:05d}.jpg"
        else:
            fname = f"impact_{tag}_offset{offset:+d}_frame{idx:05d}.jpg"
        path = os.path.join(out_dir, fname)
        cv2.imwrite(path, annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
        saved.append(path)
    cap.release()

    # Velocity curve plot — include excluded regions and all local peaks
    # so the plot alone tells the whole selection story.
    all_peaks = _find_local_maxima(sig["speed_fused"],
                                   min_distance=3)
    curve_path = os.path.join(out_dir, f"{name}_velocity_curve.png")

    # Compute joint score for plotting if YOLO is used
    joint_for_plot = None
    if prox is not None:
        # Compute normalization parameters from valid frames
        valid_mask = prox["valid_mask"]
        valid_indices = np.where(valid_mask)[0]
        if len(valid_indices) > 0:
            valid_speeds = sig["speed_fused"][valid_mask]
            valid_dists = prox["dist_interp"][valid_mask]

            min_speed = np.min(valid_speeds)
            max_speed = np.max(valid_speeds)
            speed_range = max_speed - min_speed

            min_dist = np.min(valid_dists)
            max_dist = np.max(valid_dists)
            dist_range = max_dist - min_dist
        else:
            min_speed = max_speed = 0.0
            speed_range = 0.0
            min_dist = max_dist = 0.0
            dist_range = 0.0

        joint_for_plot = np.full(total, np.nan, dtype=np.float64)
        for t in range(total):
            if valid_mask[t]:
                # Normalize speed [0, 1]
                if speed_range > 0:
                    norm_speed = (sig["speed_fused"][t] - min_speed) / speed_range
                else:
                    norm_speed = 0.5

                # Normalize proximity: higher = closer (distance smaller)
                if dist_range > 0:
                    norm_proximity = (max_dist - prox["dist_interp"][t]) / dist_range
                else:
                    norm_proximity = 0.5

                # Combined score: weighted average favoring proximity (70% distance, 30% speed)
                joint_for_plot[t] = 0.3*norm_speed + 0.7*norm_proximity

    save_velocity_curve(
        fused=sig["speed_fused"],
        wrist=sig["wrist"]["speed_smooth"],
        elbow=sig["elbow"]["speed_smooth"],
        impact_idx=impact_idx,
        out_path=curve_path,
        title=f"{name} — fused wrist+elbow speed (mode={pick_mode}, "
              f"wrist_prior={wrist_prior:.2f})",
        head_pad=head_pad_frames, tail_pad=tail_pad_frames,
        all_peaks=all_peaks,
        proximity=prox,
        speed_only_impact_idx=speed_only_impact_idx,
        joint_score=plot_score_array,
        top_k=max(3, save_top_k),
    )
    saved.append(curve_path)

    # Dump per-frame signals for later debugging / reuse as impact anchor.
    csv_path = os.path.join(out_dir, f"{name}_wrist_signal.csv")
    yolo_on = prox is not None
    with open(csv_path, "w", encoding="utf-8") as f:
        header = ("frame,"
                 "wrist_x,wrist_y,wrist_score,wrist_speed_raw,wrist_speed_smooth,"
                 "elbow_x,elbow_y,elbow_score,elbow_speed_raw,elbow_speed_smooth,"
                 "speed_fused,valid")
        if yolo_on:
            header += (",ball_x,ball_y,racket_x,racket_y,racket_diag,"
                       "dist_raw,dist_interp,both_detected,valid_interp,"
                       "joint_score")
        f.write(header + "\n")
        w_sig = sig["wrist"]
        e_sig = sig["elbow"]
        # Precompute the joint score the same way pick_impact_by_proximity did,
        # so the CSV matches the curve and the printed selection.
        if yolo_on:
            # Compute normalization parameters from valid frames
            valid_mask = prox["valid_mask"]
            valid_indices = np.where(valid_mask)[0]
            if len(valid_indices) > 0:
                valid_speeds = sig["speed_fused"][valid_mask]
                valid_dists = prox["dist_interp"][valid_mask]

                min_speed = np.min(valid_speeds)
                max_speed = np.max(valid_speeds)
                speed_range = max_speed - min_speed

                min_dist = np.min(valid_dists)
                max_dist = np.max(valid_dists)
                dist_range = max_dist - min_dist
            else:
                min_speed = max_speed = 0.0
                speed_range = 0.0
                min_dist = max_dist = 0.0
                dist_range = 0.0

            joint = np.full(total, np.nan, dtype=np.float64)
            for t in range(total):
                if valid_mask[t]:
                    # Normalize speed [0, 1]
                    if speed_range > 0:
                        norm_speed = (sig["speed_fused"][t] - min_speed) / speed_range
                    else:
                        norm_speed = 0.5

                    # Normalize proximity: higher = closer (distance smaller)
                    if dist_range > 0:
                        norm_proximity = (max_dist - prox["dist_interp"][t]) / dist_range
                    else:
                        norm_proximity = 0.5

                    # Combined score: weighted average favoring proximity (70% distance, 30% speed)
                    joint[t] = 0.3*norm_speed + 0.7*norm_proximity
        for t in range(total):
            row = (f"{t},"
                   f"{w_sig['xy_px'][t,0]:.2f},{w_sig['xy_px'][t,1]:.2f},"
                   f"{w_sig['score'][t]:.3f},{w_sig['speed_raw'][t]:.3f},"
                   f"{w_sig['speed_smooth'][t]:.3f},"
                   f"{e_sig['xy_px'][t,0]:.2f},{e_sig['xy_px'][t,1]:.2f},"
                   f"{e_sig['score'][t]:.3f},{e_sig['speed_raw'][t]:.3f},"
                   f"{e_sig['speed_smooth'][t]:.3f},"
                   f"{sig['speed_fused'][t]:.3f},{int(sig['valid_mask'][t])}")
            if yolo_on:
                bx, by = prox["ball_xy"][t]
                rx, ry = prox["racket_xy"][t]
                rs = prox["racket_sz"][t]
                dr = prox["dist"][t]
                di = prox["dist_interp"][t]
                bm = int(prox["both_mask"][t])
                vi = int(prox["valid_mask"][t])
                js = joint[t]
                # Format inf/nan consistently
                dr_s = f"{dr:.4f}" if np.isfinite(dr) else ""
                di_s = f"{di:.4f}" if np.isfinite(di) else ""
                js_s = f"{js:.3f}" if np.isfinite(js) else ""
                row += (f",{bx:.2f},{by:.2f},{rx:.2f},{ry:.2f},"
                        f"{rs:.2f},{dr_s},{di_s},{bm},{vi},{js_s}")
            f.write(row + "\n")
    saved.append(csv_path)

    return {
        "video": name,
        "shot_type": shot_type,
        "pick_mode": pick_mode,
        "impact_idx": impact_idx,
        "speed_only_impact_idx": speed_only_impact_idx,
        "yolo_used": prox is not None,
        "yolo_both_frames": int(prox["both_mask"].sum()) if prox is not None else 0,
        "yolo_refined": (prox is not None and impact_idx != speed_only_impact_idx),
        "total_frames": total,
        "fps": fps,
        "wrist_score_at_impact": wrist_score_at_impact,
        "elbow_score_at_impact": elbow_score_at_impact,
        "fused_speed_at_impact": impact_speed_fused,
        "valid_ratio": valid_ratio,
        "saved_files": saved,
    }


# ---------------------------------------------------------------------------
# Standard library building & DTW comparison
# ---------------------------------------------------------------------------
def extract_segment_from_csv(csv_path, top_k=3, head_pad_ratio=0.20, tail_pad_ratio=0.20):
    """
    从 extract_frame_samples.py 生成的 CSV 中提取候选帧和姿态序列。

    选取逻辑：
      1. 从 speed_fused 取 top-K（必选）
      2. 如果有 joint_score 且有效值 >= top-K，从 joint_score 也取 top-K
      3. 合并两个列表并去重（最多 2*K 个候选）
      4. 所有候选帧必须在 [head_pad, total - tail_pad] 区间内

    Args:
        csv_path: *_wrist_signal.csv 文件路径
        top_k: 每个信号取 top-K 个帧（默认 3）
        head_pad_ratio: 排除开头的比例（默认 0.20）
        tail_pad_ratio: 排除结尾的比例（默认 0.20）

    Returns:
        {
          "candidates": [25, 27, 28, 53, 54, 56],  # 最多 2*K 个
          "segment_range": [25, 56],   # [min, max]
          "selection_mode": "joint+speed" 或 "speed",
          "video_name_hint": "backhand_1",
          "csv_path": csv_path
        }
        如果数据不足，返回 None。
    """
    import pandas as pd
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"  [error] cannot read {csv_path}: {e}")
        return None

    total_frames = len(df)
    head = max(1, int(total_frames * head_pad_ratio))
    tail = max(1, int(total_frames * tail_pad_ratio))
    allowed_start = head
    allowed_end = total_frames - tail

    # 1. 必选：speed_fused top-K（排除头尾）
    if "speed_fused" not in df.columns:
        print(f"  [error] {csv_path} has no speed_fused column")
        return None

    valid_speed = df[
        df["speed_fused"].notna()
        & np.isfinite(df["speed_fused"])
        & (df["frame"] >= allowed_start)
        & (df["frame"] < allowed_end)
    ]
    if len(valid_speed) < top_k:
        print(f"  [skip] {csv_path} has only {len(valid_speed)} valid speed "
              f"frames in allowed window [{allowed_start}, {allowed_end})")
        return None

    speed_top = valid_speed.nlargest(top_k, "speed_fused")
    speed_candidates = set(speed_top["frame"].tolist())

    # 2. 可选：joint_score top-K（排除头尾）
    joint_candidates = set()
    mode = "speed"
    if "joint_score" in df.columns:
        valid_joint = df[
            df["joint_score"].notna()
            & np.isfinite(df["joint_score"])
            & (df["joint_score"] > 0)
            & (df["frame"] >= allowed_start)
            & (df["frame"] < allowed_end)
        ]
        if len(valid_joint) >= top_k:
            joint_top = valid_joint.nlargest(top_k, "joint_score")
            joint_candidates = set(joint_top["frame"].tolist())
            mode = "joint+speed"
            print(f"  [info] {os.path.basename(csv_path)}: using joint+speed "
                  f"(joint={len(valid_joint)} valid)")
        else:
            print(f"  [info] {os.path.basename(csv_path)}: only {len(valid_joint)} "
                  f"valid joint_score frames, using speed only")

    # 3. 合并去重
    all_candidates = sorted(speed_candidates | joint_candidates)
    seg_min, seg_max = min(all_candidates), max(all_candidates)

    csv_dir = os.path.dirname(csv_path)
    video_name_guess = os.path.basename(csv_dir)

    return {
        "candidates": all_candidates,
        "segment_range": [seg_min, seg_max],
        "selection_mode": mode,
        "video_name_hint": video_name_guess,
        "csv_path": csv_path,
    }


def extract_angles_from_video(video_path, frame_indices, model):
    """
    从视频中提取指定帧的关节角度序列。

    Args:
        video_path: 视频文件路径
        frame_indices: 要提取的帧号列表（sorted）
        model: MoveNetThunder 实例

    Returns:
        angles: (N, 8) ndarray, N = len(frame_indices)
        valid_mask: (N,) bool, 某帧的角度是否有效（非全 NaN）
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, None

    angles = np.full((len(frame_indices), 8), np.nan, dtype=np.float64)
    for i, idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        kp = model.infer(frame)  # (17, 3)
        angles[i] = compute_joint_angles(kp)
    cap.release()

    valid_mask = ~np.isnan(angles).all(axis=1)
    return angles, valid_mask


def build_standard_library(input_dir, output_json, model, top_k=3,
                           video_root=None, copy_videos=False, library_videos_dir=None,
                           head_pad_ratio=0.20, tail_pad_ratio=0.20):
    """
    批量处理标准库视频，提取候选帧和姿态序列，存入 JSON。

    Args:
        input_dir: 包含已处理视频输出的目录（impact_check）
        output_json: 输出的 standard_library.json 路径
        model: MoveNetThunder 实例
        top_k: 每个视频取 top-K 候选帧
        video_root: 原始视频所在目录（如果 None，默认为 "shots"）
        copy_videos: 是否把原视频拷贝到标准库目录
        library_videos_dir: 拷贝目标目录（如果 copy_videos=True 但此项为 None，
                           自动创建 "library_videos"）

    假设目录结构：
        input_dir/
          正手_001/
            正手_001_wrist_signal.csv
          反手_002/
            反手_002_wrist_signal.csv
        video_root/
          正手_001.mp4
          反手_002.mp4
    """
    import json
    import shutil

    if video_root is None:
        video_root = "shots"
    if copy_videos:
        if library_videos_dir is None:
            library_videos_dir = "library_videos"
        # 转成绝对路径避免相对路径问题
        library_videos_dir = os.path.abspath(library_videos_dir)
        # 确保目标目录存在
        os.makedirs(library_videos_dir, exist_ok=True)
        print(f"Video copy destination: {library_videos_dir}")

    library = {"videos": []}

    # 扫描所有子目录，找 *_wrist_signal.csv
    csv_files = glob.glob(os.path.join(input_dir, "*", "*_wrist_signal.csv"))
    print(f"Found {len(csv_files)} CSV files in {input_dir}")

    for csv_path in csv_files:
        seg_info = extract_segment_from_csv(csv_path, top_k=top_k,
                                           head_pad_ratio=head_pad_ratio,
                                           tail_pad_ratio=tail_pad_ratio)
        if seg_info is None:
            continue

        video_name = seg_info["video_name_hint"]
        # 先在 video_root 里找 .mp4
        video_path = os.path.join(video_root, f"{video_name}.mp4")
        if not os.path.exists(video_path):
            print(f"  [skip] video not found: {video_path}")
            continue

        # 拷贝视频到标准库目录
        if copy_videos:
            dest_path = os.path.join(library_videos_dir, f"{video_name}.mp4")
            try:
                shutil.copy2(video_path, dest_path)
                print(f"  [copy] {os.path.basename(video_path)}")
                video_path_for_json = dest_path
            except Exception as e:
                print(f"  [error] copy failed: {e}, using original path")
                video_path_for_json = video_path
        else:
            video_path_for_json = video_path

        seg_min, seg_max = seg_info["segment_range"]
        frame_indices = list(range(seg_min, seg_max + 1))
        angles, valid_mask = extract_angles_from_video(video_path, frame_indices, model)
        if angles is None:
            print(f"  [skip] failed to extract angles from {video_path}")
            continue

        # 推断 shot_type
        shot_type = shot_type_from_name(video_name)

        entry = {
            "name": video_name,
            "shot_type": shot_type,
            "candidates": seg_info["candidates"],
            "segment_range": seg_info["segment_range"],
            "selection_mode": seg_info["selection_mode"],
            "angles": angles.tolist(),  # (N, 8)
            "valid_mask": valid_mask.tolist(),
            "metadata": {
                "video_path": video_path_for_json,
                "csv_path": csv_path,
            }
        }
        library["videos"].append(entry)
        print(f"  [OK] {video_name}: {len(frame_indices)} frames, "
              f"candidates={seg_info['candidates']} (via {seg_info['selection_mode']})")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)
    print(f"\nStandard library built: {len(library['videos'])} videos → {output_json}")
    if copy_videos:
        print(f"Videos copied to {library_videos_dir}/")



def dtw_compare(user_angles, standard_angles, shot_type="unknown"):
    """
    DTW 对齐两个角度序列，返回归一化距离和详细偏差分析。

    根据 shot_type 选择关注的关节：
    - forehand/serve: 只看右侧（index 0-3）
    - backhand: 只看左侧（index 4-7）
    - unknown: 看全部 8 个关节

    Args:
        user_angles: (M, 8) ndarray
        standard_angles: (N, 8) ndarray
        shot_type: "forehand"/"backhand"/"serve"/"unknown"

    Returns:
        {
          "distance": float,  # 归一化的 DTW 距离
          "path": [(i, j), ...],  # 对齐路径
          "per_joint_error": [err0, err1, ..., err7],  # 每个关节的平均偏差（度）
          "active_joints": [0, 1, 2, 3] or [4, 5, 6, 7],  # 参与对比的关节索引
          "alignment_info": {
            "user_frames": M,
            "standard_frames": N,
            "path_length": len(path)
          }
        }
    """
    try:
        from fastdtw import fastdtw
    except ImportError:
        print("[warning] fastdtw not installed, using naive DTW (slow)")
        return naive_dtw_with_details(user_angles, standard_angles, shot_type)

    # 确定关注的关节
    if shot_type in ["forehand", "serve"]:
        active_joints = [0, 1, 2, 3]  # 右侧：右肩、右肘、右髋、右膝
    elif shot_type == "backhand":
        active_joints = [4, 5, 6, 7]  # 左侧：左肩、左肘、左髋、左膝
    else:
        active_joints = list(range(8))  # 全部

    def angle_dist(a, b):
        # 只计算 active_joints 的距离
        valid = np.isfinite(a) & np.isfinite(b)
        # 进一步限制到 active_joints
        active_mask = np.zeros(8, dtype=bool)
        active_mask[active_joints] = True
        valid = valid & active_mask

        if not valid.any():
            return 100.0  # large penalty if no overlap
        diff = a[valid] - b[valid]
        return float(np.sqrt((diff ** 2).mean()))

    distance, path = fastdtw(user_angles, standard_angles, dist=angle_dist)
    normalized_dist = distance / len(path)

    # 计算每个关节的平均偏差（带符号）
    per_joint_error = np.zeros(8)  # 绝对值偏差
    per_joint_signed_error = np.zeros(8)  # 带符号偏差（正=用户大，负=用户小）
    per_joint_count = np.zeros(8)

    for i, j in path:
        for k in active_joints:  # 只统计 active_joints
            if np.isfinite(user_angles[i, k]) and np.isfinite(standard_angles[j, k]):
                diff = user_angles[i, k] - standard_angles[j, k]  # 带符号
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
        "distance": normalized_dist,
        "path": path,
        "per_joint_error": per_joint_error.tolist(),  # 绝对值
        "per_joint_signed_error": per_joint_signed_error.tolist(),  # 带符号
        "active_joints": active_joints,
        "alignment_info": {
            "user_frames": len(user_angles),
            "standard_frames": len(standard_angles),
            "path_length": len(path)
        }
    }


def naive_dtw_with_details(seq1, seq2, shot_type="unknown"):
    """Naive O(MN) DTW fallback, returns detailed format like dtw_compare."""
    # 确定关注的关节
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
            # 限制到 active_joints
            active_mask = np.zeros(8, dtype=bool)
            active_mask[active_joints] = True
            valid = valid & active_mask

            if not valid.any():
                d = 100.0
            else:
                diff = seq1[i-1][valid] - seq2[j-1][valid]
                d = float(np.sqrt((diff ** 2).mean()))
            cost[i, j] = d + min(cost[i-1, j], cost[i, j-1], cost[i-1, j-1])

    # 简单估算 per_joint_error（假设对角对齐）
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
        "path": [],  # naive 版本不返回路径
        "per_joint_error": per_joint_error.tolist(),
        "per_joint_signed_error": per_joint_signed_error.tolist(),
        "active_joints": active_joints,
        "alignment_info": {
            "user_frames": M,
            "standard_frames": N,
            "path_length": 0  # unknown
        }
    }


def compare_with_library(user_video_path, library_json, model, top_k=3,
                        head_pad_ratio=0.20, tail_pad_ratio=0.20, user_csv_dir="impact_check"):
    """
    对比用户视频与标准库，返回最相似的标准视频及相似度。

    Args:
        user_video_path: 用户视频路径
        library_json: standard_library.json 路径
        model: MoveNetThunder 实例
        top_k: 用户视频取 top-K 候选帧
        user_csv_dir: 用户视频 CSV 所在目录（默认 "impact_check"）

    Returns:
        {
          "user_video": "用户_正手.mp4",
          "user_candidates": [18, 22, 26],
          "user_segment_range": [18, 26],
          "best_match": {
            "name": "正手_标准_001",
            "distance": 5.23,
            "shot_type": "forehand"
          },
          "all_comparisons": [
            {"name": "正手_标准_001", "distance": 5.23},
            {"name": "正手_标准_002", "distance": 6.78},
            ...
          ]
        }
    """
    import json

    # 1. 先跑用户视频提取候选帧（需要先有 CSV，或者现场跑）
    # 这里假设用户已经跑过 extract_frame_samples.py，有 CSV
    user_name = os.path.splitext(os.path.basename(user_video_path))[0]
    user_csv = os.path.join(user_csv_dir, user_name, f"{user_name}_wrist_signal.csv")
    if not os.path.exists(user_csv):
        print(f"[error] user video CSV not found: {user_csv}")
        print(f"        Run extract_frame_samples.py on {user_video_path} first with --use-yolo")
        return None

    user_seg = extract_segment_from_csv(user_csv, top_k=top_k,
                                       head_pad_ratio=head_pad_ratio,
                                       tail_pad_ratio=tail_pad_ratio)
    if user_seg is None:
        return None

    seg_min, seg_max = user_seg["segment_range"]
    frame_indices = list(range(seg_min, seg_max + 1))
    user_angles, user_valid = extract_angles_from_video(user_video_path, frame_indices, model)
    if user_angles is None:
        print(f"[error] failed to extract angles from {user_video_path}")
        return None

    user_shot_type = shot_type_from_name(user_name)

    # 2. 加载标准库
    with open(library_json, "r", encoding="utf-8") as f:
        library = json.load(f)

    # 3. 遍历同类型标准视频，DTW 对比
    comparisons = []
    best_match_details = None

    for std_entry in library["videos"]:
        if std_entry["shot_type"] != user_shot_type:
            continue  # 只和同类型动作对比
        std_angles = np.array(std_entry["angles"], dtype=np.float64)
        dtw_result = dtw_compare(user_angles, std_angles, shot_type=user_shot_type)

        comparison_entry = {
            "name": std_entry["name"],
            "distance": dtw_result["distance"],
            "shot_type": std_entry["shot_type"],
        }

        # 保存最佳匹配的详细信息
        if best_match_details is None or dtw_result["distance"] < best_match_details["distance"]:
            # 关节名称和定义映射
            joint_names = [
                "右肩", "右肘", "右髋", "右膝",
                "左肩", "左肘", "左髋", "左膝"
            ]
            joint_definitions = [
                "右肘-右肩-右髋夹角（手臂抬起程度）",
                "右肩-右肘-右腕夹角（手臂弯曲程度，180°=伸直）",
                "右肩-右髋-右膝夹角（上身前倾/后仰）",
                "右髋-右膝-右踝夹角（腿部弯曲程度，180°=伸直）",
                "左肘-左肩-左髋夹角（手臂抬起程度）",
                "左肩-左肘-左腕夹角（手臂弯曲程度，180°=伸直）",
                "左肩-左髋-左膝夹角（上身前倾/后仰）",
                "左髋-左膝-左踝夹角（腿部弯曲程度，180°=伸直）",
            ]

            # 只看参与对比的关节（active_joints）
            active_joints = dtw_result["active_joints"]
            per_joint_err = np.array(dtw_result["per_joint_error"])
            per_joint_signed = np.array(dtw_result["per_joint_signed_error"])

            # 只从 active_joints 中找 top-3（按绝对值偏差排序）
            active_joint_errors = [
                (i, joint_names[i], per_joint_err[i], per_joint_signed[i])
                for i in active_joints
                if np.isfinite(per_joint_err[i])
            ]
            active_joint_errors.sort(key=lambda x: x[2], reverse=True)  # 按绝对值排序

            top_issues = []
            for idx, name, abs_err, signed_err in active_joint_errors[:3]:
                direction = "偏大" if signed_err > 0 else "偏小"
                top_issues.append({
                    "joint": name,
                    "definition": joint_definitions[idx],
                    "avg_error_degrees": float(abs_err),
                    "signed_error_degrees": float(signed_err),
                    "direction": direction
                })

            # 确定关注的侧
            if user_shot_type in ["forehand", "serve"]:
                focus_side = "右侧"
            elif user_shot_type == "backhand":
                focus_side = "左侧"
            else:
                focus_side = "全身"

            best_match_details = {
                "name": std_entry["name"],
                "distance": dtw_result["distance"],
                "shot_type": std_entry["shot_type"],
                "focus_side": focus_side,
                "per_joint_error": {
                    joint_names[i]: {
                        "abs_error": dtw_result["per_joint_error"][i],
                        "signed_error": dtw_result["per_joint_signed_error"][i],
                        "definition": joint_definitions[i]
                    }
                    for i in active_joints  # 只保存 active_joints
                },
                "top_issues": top_issues,
                "alignment_info": dtw_result["alignment_info"],
                # 保存原始角度数据供 LLM 分析
                "user_angles": user_angles.tolist(),
                "standard_angles": std_angles.tolist(),
                "user_segment": {
                    "candidates": user_seg["candidates"],
                    "range": user_seg["segment_range"],
                    "selection_mode": user_seg["selection_mode"]
                },
                "standard_segment": {
                    "candidates": std_entry["candidates"],
                    "range": std_entry["segment_range"],
                    "selection_mode": std_entry.get("selection_mode", "unknown")
                }
            }

        comparisons.append(comparison_entry)

    if not comparisons:
        print(f"[warning] no matching {user_shot_type} videos in library")
        return None

    # 4. 排序
    comparisons.sort(key=lambda x: x["distance"])

    result = {
        "user_video": user_name,
        "user_candidates": user_seg["candidates"],
        "user_segment_range": user_seg["segment_range"],
        "best_match": best_match_details,
        "all_comparisons": comparisons,
    }

    print(f"\n=== Comparison Result ===")
    print(f"User video: {user_name} ({user_shot_type})")
    print(f"Candidates: {user_seg['candidates']}, segment: {user_seg['segment_range']}")
    print(f"Best match: {best_match_details['name']} (distance={best_match_details['distance']:.2f})")
    print(f"关注侧: {best_match_details['focus_side']}")
    print(f"\nTop issues to improve ({best_match_details['focus_side']}):")
    for issue in best_match_details["top_issues"]:
        sign_str = f"+{issue['signed_error_degrees']:.1f}" if issue['signed_error_degrees'] > 0 else f"{issue['signed_error_degrees']:.1f}"
        print(f"  {issue['joint']}: {sign_str}° ({issue['direction']})")
        print(f"    定义: {issue['definition']}")
    print(f"\nAll matches ({len(comparisons)} total):")
    for c in comparisons[:5]:  # 只显示 top-5
        print(f"  {c['name']}: {c['distance']:.2f}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()

    # Mode selection
    ap.add_argument("--build-library", action="store_true",
                    help="Build standard library mode: batch-process all videos "
                         "in --input-dir and extract pose segments into a JSON file.")
    ap.add_argument("--compare", type=str, default=None, metavar="USER_VIDEO",
                    help="Compare mode: compare USER_VIDEO against the standard "
                         "library (--library-json) and output similarity report.")
    ap.add_argument("--compare-dir", type=str, default=None, metavar="USER_DIR",
                    help="Batch compare mode: compare all mp4 videos in USER_DIR "
                         "against the standard library and output reports.")
    ap.add_argument("--user-csv-dir", default="impact_check",
                    help="Directory containing user video CSVs (used by --compare "
                         "and --compare-dir to locate *_wrist_signal.csv files). "
                         "Default: impact_check")
    ap.add_argument("--library-json", default="standard_library.json",
                    help="Path to standard library JSON (used by --build-library "
                         "output and --compare input).")
    ap.add_argument("--library-top-k", type=int, default=3,
                    help="Number of top candidate frames to extract per video "
                         "in library mode (default 3).")
    ap.add_argument("--video-root", default="shots",
                    help="Directory containing original video files (used by "
                         "--build-library to locate videos based on CSV names).")
    ap.add_argument("--copy-videos", action="store_true",
                    help="Copy original videos into library_videos/ when "
                         "building the standard library (keeps everything in "
                         "one place for easier deployment).")
    ap.add_argument("--library-videos-dir", default="library_videos",
                    help="Destination directory for copied videos when "
                         "--copy-videos is enabled (default: library_videos/).")

    # Common parameters (used in all modes)
    ap.add_argument("--input-dir", default="shots", help="directory with MP4s")
    ap.add_argument("--output-dir", default="impact_check",
                    help="where to write annotated impact frames")
    ap.add_argument("--pattern", default="*.mp4")
    ap.add_argument("--score-thresh", type=float, default=0.2,
                    help="wrist confidence below this is interpolated")
    ap.add_argument("--smooth-xy", type=int, default=3,
                    help="moving-average window for wrist xy (frames)")
    ap.add_argument("--smooth-v", type=int, default=3,
                    help="moving-average window for velocity (frames)")
    ap.add_argument("--context", type=int, default=1,
                    help="save impact ± this many neighbor frames")
    ap.add_argument("--save-top-k", type=int, default=0,
                    help="save top K highest-scoring frames (including the best impact). "
                         "If >0, overrides --context and saves only these frames.")
    ap.add_argument("--head-pad", type=float, default=0.20,
                    help="fraction of frames at the start to exclude from peak "
                         "search (default 0.20)")
    ap.add_argument("--tail-pad", type=float, default=0.20,
                    help="fraction of frames at the end to exclude from peak "
                         "search (default 0.20)")
    ap.add_argument("--wrist-prior", type=float, default=0.7,
                    help="weight of wrist vs elbow in the fused speed signal "
                         "(default 0.7; wrist contributes 70%%, elbow 30%%, "
                         "further modulated by per-frame MoveNet confidence)")
    ap.add_argument("--mode", type=str, default=None,
                    help="Override peak selection mode for all videos. Options: "
                         "'global_max_raw' (simple global max), 'global_max' "
                         "(global max with head/tail exclusion), 'last_peak', "
                         "'backhand_first_22', 'forehand_10_30'")
    ap.add_argument("--frame-range-start", type=int, default=None,
                    help="Start frame for impact search (inclusive)")
    ap.add_argument("--frame-range-end", type=int, default=None,
                    help="End frame for impact search (exclusive)")
    ap.add_argument("--save-range-start", type=int, default=None,
                    help="Start frame for saving all frames (inclusive)")
    ap.add_argument("--save-range-end", type=int, default=None,
                    help="End frame for saving all frames (exclusive)")

    # YOLOv8 ball + racket detection (optional).
    ap.add_argument("--use-yolo", action="store_true",
                    help="Enable YOLOv8 ball+racket detection. The speed-based "
                         "pick is refined by finding the frame near a top "
                         "velocity peak with smallest ball<->racket distance. "
                         "Works with off-the-shelf COCO-pretrained weights "
                         "(both 'sports ball' and 'tennis racket' are COCO "
                         "classes, so no fine-tuning is required).")
    ap.add_argument("--yolo-weights", default="yolov8s.pt",
                    help="Path to YOLOv8 weights file (default: yolov8s.pt). "
                         "If the file doesn't exist locally, ultralytics will "
                         "auto-download it on first use. Recommended: "
                         "yolov8s.pt (fast+good) or yolov8m.pt (better small "
                         "object recall for the ball).")
    ap.add_argument("--yolo-conf", type=float, default=0.20,
                    help="YOLO confidence threshold (default 0.20, lower than "
                         "typical 0.25 because the tennis ball is tiny and "
                         "often close to the detector's minimum confidence).")
    ap.add_argument("--yolo-imgsz", type=int, default=640,
                    help="YOLO inference image size (default 640). Try 960 or "
                         "1280 if ball recall is poor on high-res videos.")
    ap.add_argument("--yolo-device", default=None,
                    help="YOLO device, e.g. 'cuda:0' or 'cpu'. Default: "
                         "ultralytics auto-selects (uses GPU if available).")
    ap.add_argument("--proximity-interp-gap", type=int, default=3,
                    help="Max gap (in frames) to linearly interpolate in the "
                         "ball<->racket distance signal when YOLO briefly "
                         "drops the ball. Default 3 — covers most single-frame "
                         "and two-frame dropouts at impact.")
    ap.add_argument("--proximity-dist-floor", type=float, default=0.005,
                    help="Lower bound on normalized distance used in the "
                         "speed/dist joint score (default 0.005 ~ 1 tennis "
                         "ball width). Prevents a single ultra-close frame "
                         "from dominating the score; increase if YOLO is "
                         "noisy and you see the pick flicker to tiny-dist "
                         "outliers.")
    args = ap.parse_args()

    # Mode dispatch: --build-library, --compare, or normal extraction
    if args.build_library:
        print("=== Building Standard Library ===")
        model = MoveNetThunder()
        build_standard_library(
            input_dir=args.output_dir,  # 从已处理的输出目录读 CSV
            output_json=args.library_json,
            model=model,
            top_k=args.library_top_k,
            video_root=args.video_root,
            copy_videos=args.copy_videos,
            library_videos_dir=args.library_videos_dir,
            head_pad_ratio=args.head_pad,
            tail_pad_ratio=args.tail_pad,
        )
        return

    if args.compare:
        print("=== Comparing User Video with Library ===")
        model = MoveNetThunder()
        result = compare_with_library(
            user_video_path=args.compare,
            library_json=args.library_json,
            model=model,
            top_k=args.library_top_k,
            head_pad_ratio=args.head_pad,
            tail_pad_ratio=args.tail_pad,
            user_csv_dir=args.user_csv_dir,
        )
        if result:
            # Optionally save result to JSON
            out_path = f"{os.path.splitext(os.path.basename(args.compare))[0]}_comparison.json"
            import json
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nComparison result saved to {out_path}")
        return

    if args.compare_dir:
        print("=== Batch Comparing User Videos with Library ===")
        import json

        # 找到所有 mp4
        user_videos = sorted(glob.glob(os.path.join(args.compare_dir, "*.mp4")))
        if not user_videos:
            print(f"No *.mp4 files found in {args.compare_dir}")
            return

        print(f"Found {len(user_videos)} videos to compare")
        model = MoveNetThunder()

        results_summary = []
        for i, video_path in enumerate(user_videos, 1):
            video_name = os.path.basename(video_path)
            print(f"\n[{i}/{len(user_videos)}] Comparing {video_name}...")

            result = compare_with_library(
                user_video_path=video_path,
                library_json=args.library_json,
                model=model,
                top_k=args.library_top_k,
                head_pad_ratio=args.head_pad,
                tail_pad_ratio=args.tail_pad,
                user_csv_dir=args.user_csv_dir,
            )

            if result:
                # 保存单个视频的详细结果
                out_path = f"{os.path.splitext(video_name)[0]}_comparison.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"  → {out_path}")

                # 添加到汇总
                results_summary.append({
                    "video": video_name,
                    "best_match": result["best_match"]["name"],
                    "distance": result["best_match"]["distance"],
                    "shot_type": result["best_match"]["shot_type"],
                })
            else:
                print(f"  → Failed to compare (no matching CSV or library entry)")

        # 保存汇总结果
        if results_summary:
            summary_path = "batch_comparison_summary.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(results_summary, f, indent=2, ensure_ascii=False)
            print(f"\n=== Batch Summary ===")
            print(f"Successfully compared: {len(results_summary)}/{len(user_videos)} videos")
            print(f"Summary saved to {summary_path}")
            print(f"\nTop matches:")
            for r in results_summary[:10]:
                print(f"  {r['video'][:30]:30s} → {r['best_match']:20s} (dist={r['distance']:.2f})")
        return

    # Normal extraction mode (unchanged)
    videos = sorted(glob.glob(os.path.join(args.input_dir, args.pattern)))
    if not videos:
        print(f"No {args.pattern} under {args.input_dir}")
        return

    print(f"Found {len(videos)} videos")
    print(f"Edge exclusion: head {args.head_pad*100:.0f}% / tail {args.tail_pad*100:.0f}%")
    print(f"Fusion: wrist_prior={args.wrist_prior:.2f} "
          f"(elbow prior={1-args.wrist_prior:.2f})")
    if args.mode:
        print(f"Mode override: all videos will use '{args.mode}' mode")
    else:
        print(f"Peak-selection rules:")
        print(f"  serve    -> last   significant peak")
        print(f"  forehand -> highest speed between frames 10-30")
        print(f"  backhand -> highest speed within first 22 frames")
        print(f"  unknown  -> global argmax in window")

    model = MoveNetThunder()

    yolo = None
    if args.use_yolo:
        if not HAS_YOLO:
            print("ERROR: --use-yolo was passed but ultralytics is not "
                  "installed. Run `pip install ultralytics` first.")
            return
        print(f"YOLO enabled: weights={args.yolo_weights}, "
              f"conf={args.yolo_conf}, imgsz={args.yolo_imgsz}, "
              f"device={args.yolo_device or 'auto'}")
        print(f"  impact picked by argmax(speed / ball_racket_dist), "
              f"shot_type window limits ignored. "
              f"Short ball detection gaps up to {args.proximity_interp_gap} "
              f"frames are interpolated.")
        yolo = YoloBallRacketDetector(
            weights_path=args.yolo_weights,
            conf=args.yolo_conf,
            device=args.yolo_device,
            imgsz=args.yolo_imgsz,
        )

    os.makedirs(args.output_dir, exist_ok=True)
    summary_path = os.path.join(args.output_dir, "impact_summary.csv")
    rows = []
    for vp in videos:
        try:
            info = process_video(vp, args.output_dir, model,
                                 score_thresh=args.score_thresh,
                                 smooth_xy=args.smooth_xy,
                                 smooth_v=args.smooth_v,
                                 save_context=args.context,
                                 head_pad_ratio=args.head_pad,
                                 tail_pad_ratio=args.tail_pad,
                                 wrist_prior=args.wrist_prior,
                                 mode_override=args.mode,
                                 frame_range_start=args.frame_range_start,
                                 frame_range_end=args.frame_range_end,
                                 yolo=yolo,
                                 proximity_interp_gap=args.proximity_interp_gap,
                                 proximity_dist_floor=args.proximity_dist_floor,
                                 save_top_k=args.save_top_k)
            if info:
                rows.append(info)
        except Exception as e:
            print(f"  [error] {vp}: {e}")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("video,shot_type,pick_mode,impact_idx,speed_only_impact_idx,"
                "yolo_used,yolo_both_frames,yolo_refined,"
                "total_frames,fps,wrist_score_at_impact,elbow_score_at_impact,"
                "fused_speed_at_impact,valid_ratio\n")
        for r in rows:
            f.write(f"{r['video']},{r['shot_type']},{r['pick_mode']},"
                    f"{r['impact_idx']},{r['speed_only_impact_idx']},"
                    f"{int(r['yolo_used'])},{r['yolo_both_frames']},"
                    f"{int(r['yolo_refined'])},"
                    f"{r['total_frames']},{r['fps']:.2f},"
                    f"{r['wrist_score_at_impact']:.3f},"
                    f"{r['elbow_score_at_impact']:.3f},"
                    f"{r['fused_speed_at_impact']:.3f},"
                    f"{r['valid_ratio']:.3f}\n")
    print(f"\nSummary written to {summary_path}")
    print("Check impact_*.jpg images and *_velocity_curve.png in each video's folder.")


if __name__ == "__main__":
    main()