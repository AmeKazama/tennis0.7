import json
import math
from pathlib import Path

ANGLE_KEYS = [
    "right_elbow", "left_elbow",
    "right_shoulder", "left_shoulder",
    "right_wrist", "left_wrist",
    "torso_rotation",
    "right_knee", "left_knee",
    "right_hip", "left_hip",
    "trunk_lean",
]

ANGLE_WEIGHTS = {
    "serve": {
        "right_elbow": 1.7,
        "right_shoulder": 1.4,
        "right_wrist": 0.8,
        "torso_rotation": 1.2,
        "right_knee": 1.2,
        "right_hip": 1.0,
        "trunk_lean": 0.9,
        "left_elbow": 0.8,
        "left_shoulder": 0.8,
        "left_wrist": 0.5,
        "left_knee": 0.7,
        "left_hip": 0.7,
    }
}

PHASE_ORDER = [
    ("prepare_to_backswing", "start", "backswing_peak", 0.20),
    ("backswing_to_forward", "backswing_peak", "forward_start", 0.25),
    ("forward_to_impact", "forward_start", "impact", 0.35),
    ("impact_to_finish", "impact", "end", 0.20),
]

KEYFRAME_WEIGHTS = {
    "start": 0.10,
    "backswing_peak": 0.25,
    "forward_start": 0.25,
    "impact": 0.30,
    "end": 0.10,
}


def load_final_annotation(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data[0] if data else None
    return data


def load_phase_library(library_dir=None, shot_type=None):
    if library_dir is None:
        library_dir = Path(__file__).resolve().parents[3] / "264"
    library_dir = Path(library_dir)
    entries = []
    if not library_dir.exists():
        return entries
    for path in sorted(library_dir.glob("*_final.json")):
        ann = load_final_annotation(path)
        if not ann:
            continue
        if shot_type and ann.get("shot_type") != shot_type:
            continue
        ann = dict(ann)
        ann["_source_file"] = str(path)
        entries.append(ann)
    return entries


def extract_mediapipe_annotation(video_path, window, shot_type, shot_id, impact_frame=None):
    """Convert one uploaded-user shot window into the serve00x_final.json shape."""
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("mediapipe/opencv/numpy not available") from exc

    if not window:
        return None

    frame_ids = [int(item[0]) for item in window]
    start_frame = min(frame_ids)
    end_frame = max(frame_ids)
    if impact_frame is None:
        impact_frame = frame_ids[len(frame_ids) // 2]
    impact_frame = int(max(start_frame, min(end_frame, impact_frame)))

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {video_path}")

    fps = round(cap.get(cv2.CAP_PROP_FPS) or 30.0, 2)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    pose = mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.5)

    def calc_angle(a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba, bc = a - b, c - b
        n1 = np.linalg.norm(ba) + 1e-6
        n2 = np.linalg.norm(bc) + 1e-6
        cos = np.clip(np.dot(ba, bc) / (n1 * n2), -1.0, 1.0)
        return round(float(np.degrees(np.arccos(cos))), 2)

    frame_angles = {}
    for fid in range(start_frame, end_frame + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fid)
        ret, frame = cap.read()
        if not ret:
            continue
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)
        if not result.pose_landmarks:
            continue
        lm = result.pose_landmarks.landmark
        pt = lambda i: np.array([lm[i].x * w, lm[i].y * h])
        ms = (pt(11) + pt(12)) / 2
        mh = (pt(23) + pt(24)) / 2
        frame_angles[fid] = {
            "right_elbow": calc_angle(pt(12), pt(14), pt(16)),
            "left_elbow": calc_angle(pt(11), pt(13), pt(15)),
            "right_shoulder": calc_angle(pt(14), pt(12), pt(24)),
            "left_shoulder": calc_angle(pt(13), pt(11), pt(23)),
            "right_wrist": calc_angle(pt(14), pt(16), pt(20)),
            "left_wrist": calc_angle(pt(13), pt(15), pt(19)),
            "torso_rotation": round(float(np.degrees(np.arctan2(
                abs(pt(12)[1] - pt(11)[1]),
                abs(pt(12)[0] - pt(11)[0]) + 1e-6
            ))), 2),
            "right_knee": calc_angle(pt(24), pt(26), pt(28)),
            "left_knee": calc_angle(pt(23), pt(25), pt(27)),
            "right_hip": calc_angle(pt(12), pt(24), pt(26)),
            "left_hip": calc_angle(pt(11), pt(23), pt(25)),
            "trunk_lean": calc_angle(mh, ms, np.array([ms[0], ms[1] - 100])),
        }

    cap.release()
    pose.close()

    if not frame_angles:
        return None

    phase = infer_phase_boundaries(frame_angles, start_frame, end_frame, impact_frame)
    angles = [
        {"frame": fid, "angles": frame_angles[fid]}
        for fid in range(start_frame, end_frame + 1)
        if fid in frame_angles
    ]
    key_angles = {
        name: {"frame": fid, "angles": frame_angles[fid]}
        for name, fid in phase.items()
        if fid in frame_angles
    }
    return {
        "name": f"user_shot_{shot_id:03d}_{shot_type}",
        "shot_type": shot_type,
        "segment_range": [start_frame, end_frame],
        "impact_frame": impact_frame,
        "phase_boundaries": phase,
        "fps": fps,
        "total_frames": total_frames,
        "angles": angles,
        "key_angles": key_angles,
    }


def infer_phase_boundaries(frame_angles, start_frame, end_frame, impact_frame):
    pre_frames = [f for f in frame_angles if start_frame <= f <= impact_frame]
    post_frames = [f for f in frame_angles if impact_frame <= f <= end_frame]
    if not pre_frames:
        pre_frames = [start_frame, impact_frame]

    backswing_peak = min(
        pre_frames,
        key=lambda f: frame_angles.get(f, {}).get("right_elbow", float("inf"))
    )

    search = [f for f in pre_frames if backswing_peak <= f <= impact_frame]
    if len(search) >= 3:
        values = [(f, frame_angles[f].get("right_elbow", 0.0)) for f in search]
        deltas = []
        for (fa, va), (fb, vb) in zip(values, values[1:]):
            deltas.append((fb, abs(vb - va)))
        max_delta = max((d for _, d in deltas), default=0.0)
        threshold = max(3.0, max_delta * 0.35)
        forward_start = next((f for f, d in deltas if d >= threshold), search[0])
    else:
        forward_start = search[0] if search else backswing_peak

    if forward_start > impact_frame:
        forward_start = impact_frame
    if backswing_peak > forward_start:
        backswing_peak = forward_start

    return {
        "start": int(start_frame),
        "backswing_peak": int(backswing_peak),
        "forward_start": int(forward_start),
        "impact": int(impact_frame),
        "end": int(max(post_frames) if post_frames else end_frame),
    }


def _angle_weights(shot_type):
    mapping = ANGLE_WEIGHTS.get(shot_type, {})
    return [float(mapping.get(k, 1.0)) for k in ANGLE_KEYS]


def _angles_to_matrix(annotation, start_frame=None, end_frame=None):
    rows = []
    for item in annotation.get("angles", []):
        frame = item.get("frame")
        if frame is None:
            continue
        if start_frame is not None and frame < start_frame:
            continue
        if end_frame is not None and frame > end_frame:
            continue
        angle_map = item.get("angles", {})
        rows.append([float(angle_map.get(k, float("nan"))) for k in ANGLE_KEYS])
    return rows


def _fill_and_smooth(rows, smooth_window=3):
    if not rows:
        return []
    import numpy as np
    arr = np.array(rows, dtype=np.float64)
    x = np.arange(arr.shape[0])
    for col in range(arr.shape[1]):
        values = arr[:, col]
        valid = np.isfinite(values)
        if valid.sum() == 0:
            arr[:, col] = 0.0
        elif valid.sum() == 1:
            arr[:, col] = values[valid][0]
        else:
            arr[:, col] = np.interp(x, x[valid], values[valid])

    if smooth_window > 1 and arr.shape[0] >= smooth_window:
        pad = smooth_window // 2
        padded = np.pad(arr, ((pad, pad), (0, 0)), mode="edge")
        kernel = np.ones(smooth_window, dtype=np.float64) / smooth_window
        out = np.empty_like(arr)
        for col in range(arr.shape[1]):
            out[:, col] = np.convolve(padded[:, col], kernel, mode="valid")
        arr = out
    return arr.tolist()


def _velocity(rows):
    if not rows:
        return []
    import numpy as np
    arr = np.array(rows, dtype=np.float64)
    if len(arr) == 1:
        return np.zeros_like(arr).tolist()
    return np.gradient(arr, axis=0).tolist()


def _weighted_frame_distance(a, b, va, vb, weights, velocity_weight=0.25):
    num = den = 0.0
    for idx, weight in enumerate(weights):
        av, bv = a[idx], b[idx]
        if not (math.isfinite(av) and math.isfinite(bv)):
            continue
        diff = av - bv
        vdiff = va[idx] - vb[idx]
        num += weight * (diff * diff + velocity_weight * vdiff * vdiff)
        den += weight
    if den <= 0:
        return 100.0
    return math.sqrt(num / den)


def _exact_dtw(seq_a, seq_b, weights, band_ratio=0.25):
    if not seq_a or not seq_b:
        return {"distance": 100.0, "path_length": 0}
    vel_a = _velocity(seq_a)
    vel_b = _velocity(seq_b)
    m, n = len(seq_a), len(seq_b)
    band = max(abs(m - n), int(max(m, n) * band_ratio), 2)
    cost = [[float("inf")] * (n + 1) for _ in range(m + 1)]
    cost[0][0] = 0.0
    for i in range(1, m + 1):
        for j in range(max(1, i - band), min(n, i + band) + 1):
            d = _weighted_frame_distance(
                seq_a[i - 1], seq_b[j - 1],
                vel_a[i - 1], vel_b[j - 1],
                weights,
            )
            cost[i][j] = d + min(cost[i - 1][j], cost[i][j - 1], cost[i - 1][j - 1])
    if not math.isfinite(cost[m][n]):
        return {"distance": 100.0, "path_length": 0}
    return {"distance": cost[m][n] / max(m, n), "path_length": max(m, n)}


def _keyframe_distance(user_ann, std_ann, weights):
    total = used = 0.0
    details = []
    for key, key_weight in KEYFRAME_WEIGHTS.items():
        ua = user_ann.get("key_angles", {}).get(key, {}).get("angles")
        sa = std_ann.get("key_angles", {}).get(key, {}).get("angles")
        if not ua or not sa:
            continue
        urow = [float(ua.get(k, float("nan"))) for k in ANGLE_KEYS]
        srow = [float(sa.get(k, float("nan"))) for k in ANGLE_KEYS]
        zero = [0.0] * len(ANGLE_KEYS)
        dist = _weighted_frame_distance(urow, srow, zero, zero, weights, velocity_weight=0.0)
        total += key_weight * dist
        used += key_weight
        details.append({"phase": key, "distance": dist})
    return (total / used if used else 0.0), details


def phase_aware_dtw_compare(user_ann, std_ann):
    shot_type = user_ann.get("shot_type", std_ann.get("shot_type", "unknown"))
    weights = _angle_weights(shot_type)
    user_phase = user_ann.get("phase_boundaries", {})
    std_phase = std_ann.get("phase_boundaries", {})
    phase_distances = []
    weighted_sum = weight_sum = 0.0
    for phase_name, start_key, end_key, phase_weight in PHASE_ORDER:
        us, ue = user_phase.get(start_key), user_phase.get(end_key)
        ss, se = std_phase.get(start_key), std_phase.get(end_key)
        if us is None or ue is None or ss is None or se is None or ue < us or se < ss:
            continue
        user_rows = _fill_and_smooth(_angles_to_matrix(user_ann, us, ue))
        std_rows = _fill_and_smooth(_angles_to_matrix(std_ann, ss, se))
        dtw = _exact_dtw(user_rows, std_rows, weights)
        phase_distances.append({
            "phase": phase_name,
            "distance": dtw["distance"],
            "user_frames": len(user_rows),
            "standard_frames": len(std_rows),
        })
        weighted_sum += phase_weight * dtw["distance"]
        weight_sum += phase_weight

    sequence_distance = weighted_sum / weight_sum if weight_sum else 100.0
    key_distance, key_details = _keyframe_distance(user_ann, std_ann, weights)
    distance = 0.80 * sequence_distance + 0.20 * key_distance
    return {
        "distance": distance,
        "sequence_distance": sequence_distance,
        "keyframe_distance": key_distance,
        "phase_distances": phase_distances,
        "keyframe_distances": key_details,
        "active_joints": list(range(len(ANGLE_KEYS))),
        "per_joint_error": [],
        "per_joint_signed_error": [],
        "standard": std_ann.get("name", "unknown"),
    }


def compare_user_annotation(user_ann, library_dir=None):
    candidates = []
    for std_ann in load_phase_library(library_dir, user_ann.get("shot_type")):
        result = phase_aware_dtw_compare(user_ann, std_ann)
        result["standard_annotation"] = std_ann
        result["file"] = std_ann.get("_source_file")
        candidates.append(result)
    candidates.sort(key=lambda item: item["distance"])
    return candidates
