#!/usr/bin/env python3
"""各推理组件单帧耗时微基准（用 serve005 真实帧）。"""
import time

import cv2
import numpy as np
import tensorflow as tf

from services.tennis_final import YoloBallRacketDetector, HAS_YOLO
from services.extract_human_pose import HumanPoseExtractor

VIDEO = "../../264/serve005.mp4"


def bench(name, fn, n=8, warmup=2):
    for _ in range(warmup):
        fn()
    t = time.perf_counter()
    for _ in range(n):
        fn()
    dt = (time.perf_counter() - t) / n * 1000
    print(f"  {name:<42s} {dt:8.1f} ms/次")
    return dt


cap = cv2.VideoCapture(VIDEO)
ret, frame = cap.read()
cap.release()
print(f"帧尺寸: {frame.shape}")

print("\n[1] TFLite MoveNet 姿态 (主循环每帧):")
hpe = HumanPoseExtractor(frame.shape)
bench("HumanPoseExtractor.extract", lambda: hpe.extract(frame))

print("\n[2] keras RNN 分类 (主循环每帧, 30x26 窗口):")
from services.tennis_analysis_service import TennisAnalysisService

svc = TennisAnalysisService()
svc.model = tf.keras.models.load_model("services/tennis_rnn_converted.keras")
seq = np.random.rand(1, 30, 26).astype(np.float32)
bench("model(seq)", lambda: svc.model(seq, training=False))

print("\n[3] YOLOv8s 球/拍检测 (shot确认窗口每帧):")
if HAS_YOLO:
    det = YoloBallRacketDetector(weights_path="services/yolov8s.pt", conf=0.20, device=None)
    bench("YoloBallRacketDetector.infer", lambda: det.infer(frame))

print("\n[4] mediapipe PoseLandmarker (骨骼视频每帧):")
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

opts = vision.PoseLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path="models/pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.VIDEO,
    min_detection_confidence=0.5,
)
lm = vision.PoseLandmarker.create_from_options(opts)
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

state = {"ts": 0}


def run_lm():
    state["ts"] += 33
    lm.detect_for_video(mp_img, state["ts"])


bench("PoseLandmarker.detect_for_video", run_lm)
print("\n完成")
