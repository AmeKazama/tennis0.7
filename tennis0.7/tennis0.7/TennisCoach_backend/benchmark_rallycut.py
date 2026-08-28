"""rally_cut 组件级 CPU 微基准：YOLO 球检测逐帧 + CourtDetectorNet 抽样帧。

与生产参数一致（conf=0.25, imgsz=640, device=cpu, 输入 640x360 court 输入），
用 264/serve005.mp4 的真实帧跑，不依赖球场标定。
"""
import sys
import time

import cv2
import numpy as np
import torch

from ultralytics import YOLO
from services.rally_cutter_core import CourtDetectorNet, load_weights

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "../../264/serve005.mp4"
N_FRAMES = 100
COURT_STRIDE = 30  # 生产 court_sample_stride

# ── 读帧 ─────────────────────────────────────────────
cap = cv2.VideoCapture(VIDEO)
frames = []
while len(frames) < N_FRAMES and cap.isOpened():
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
cap.release()
print(f"frames: {len(frames)}, shape: {frames[0].shape}")

# ── 1) YOLO 球检测（逐帧，生产路径） ──────────────────
yolo = YOLO("weights/tennisball.pt")
yolo.predict(frames[:4], conf=0.25, imgsz=640, device="cpu", verbose=False)  # 预热
t = time.perf_counter()
yolo.predict(frames, conf=0.25, imgsz=640, device="cpu", verbose=False)
dt = time.perf_counter() - t
print(f"YOLO tennisball  : {dt/len(frames)*1000:7.2f} ms/帧  (batch={len(frames)})")

t = time.perf_counter()
for f in frames[:20]:
    yolo.predict(f, conf=0.25, imgsz=640, device="cpu", verbose=False)
dt = time.perf_counter() - t
print(f"YOLO 单帧调用    : {dt/20*1000:7.2f} ms/帧")

# ── 2) CourtDetectorNet（抽样帧） ────────────────────
net = CourtDetectorNet()
load_weights(net, "weights/court_detector.pth", torch.device("cpu"))
net.eval()

court_frames = []
for f in frames[::COURT_STRIDE]:
    inp = cv2.resize(f, (640, 360))
    inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    court_frames.append(torch.FloatTensor(inp.transpose(2, 0, 1)).unsqueeze(0))

with torch.no_grad():
    net(court_frames[0])  # 预热
    t = time.perf_counter()
    for x in court_frames:
        net(x)
    dt = time.perf_counter() - t
n = len(court_frames)
print(f"CourtDetectorNet : {dt/max(n,1)*1000:7.2f} ms/帧  (每 {COURT_STRIDE} 帧采 1 次 → 摊销 {dt/max(n,1)*1000/COURT_STRIDE:.3f} ms/帧)")

# ── 3) 每帧总摊销 ────────────────────────────────────
# 生产 batch_size=16 的 YOLO + court 摊销
per_frame = dt / max(n, 1) / COURT_STRIDE
print(f"\n=> rally_cut 模型推理合计 ≈ {0 + per_frame:.1f} + YOLO ms/帧，30fps 视频实时倍率见上")
