"""
rally_cutter_final.py  ——  网球回合自动切割（可直接运行版）
=====================================================================
【准备工作：下载两个权重文件】

  1. TrackNet 球追踪权重（约 64MB）：
     https://drive.google.com/file/d/1XEYZ4myUN7QT-NeBYJI0xteLsvs-ZAOl/view
     → 保存为  weights/tracknet.pth

  2. 球场关键点检测权重（约 64MB）：
     https://drive.google.com/file/d/1f-Co64ehgq4uddcQm1aFBDtbnyZhQvgG/view
     → 保存为  weights/court_detector.pth
     （如果下载不到，不用管，程序会自动切换手动标定模式）

【安装依赖】
  conda create -n tennis python=3.10 -y
  conda activate tennis
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
  pip install opencv-python numpy scipy

  另需安装 ffmpeg 并加入系统 PATH：
  https://ffmpeg.org/download.html  （Windows 下载 release build，解压后把 bin 加入环境变量）

【运行】
  # 首次运行（弹窗手动点4个球场角点）：
  python rally_cutter_final.py --video 你的视频.mp4

  # 再次运行同机位视频（自动加载上次标定）：
  python rally_cutter_final.py --video 另一段.mp4

  # 强制重新标定：
  python rally_cutter_final.py --video 你的视频.mp4 --recalib

  # CPU 模式（无 GPU）：
  python rally_cutter_final.py --video 你的视频.mp4 --device cpu
=====================================================================
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'   # 消除 Windows 下 OMP 重复加载警告

import cv2
import numpy as np
import subprocess
import json
import argparse
import csv
import shutil
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter
import torch
import torch.nn as nn


def get_ffmpeg_exe():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
#  1. TrackNet / CourtDetectorNet 网络结构
#     完全按照 yastrebksv 权重的真实 key 结构对齐：
#       conv1~conv18，每层命名为 convN.block（Conv2d+BN+ReLU）
#
#     通道变化（从权重 shape 实测）：
#       编码器 conv1-10：9→64→64→128→128→256→256→256→512→512→512
#       解码器 conv11-18：512→256→256→256→128→128→64→64→256(输出)
#       中间穿插 MaxPool(编码) 和 Upsample(解码)
#
#     TrackNet   输入通道=9（3帧×RGB），输出取conv18的256通道热力图求最大值
#     CourtDetector 输入通道=3（单帧RGB），输出相同，取前15通道作关键点
# ══════════════════════════════════════════════════════════════════

class _ConvBNRelu(nn.Module):
    """与权重 key convN.block 对应：block.0=Conv2d, block.2=BN（block.1=ReLU不存参数）"""
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=True),
            nn.ReLU(inplace=True),
            nn.BatchNorm2d(out_ch),
        )
    def forward(self, x):
        return self.block(x)


class _TrackNetBase(nn.Module):
    """
    通用骨干，TrackNet 和 CourtDetectorNet 共用同一结构，
    只有第一层输入通道不同（9 vs 3）。
    """
    def __init__(self, in_channels: int):
        super().__init__()
        self.pool = nn.MaxPool2d(2, 2)
        self.up   = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        # ── 编码器 conv1~conv10 ──
        self.conv1  = _ConvBNRelu(in_channels, 64)
        self.conv2  = _ConvBNRelu(64,  64)
        # pool → 320×180
        self.conv3  = _ConvBNRelu(64,  128)
        self.conv4  = _ConvBNRelu(128, 128)
        # pool → 160×90
        self.conv5  = _ConvBNRelu(128, 256)
        self.conv6  = _ConvBNRelu(256, 256)
        self.conv7  = _ConvBNRelu(256, 256)
        # pool → 80×45
        self.conv8  = _ConvBNRelu(256, 512)
        self.conv9  = _ConvBNRelu(512, 512)
        self.conv10 = _ConvBNRelu(512, 512)
        # pool → 40×22

        # ── 解码器 conv11~conv18 ──
        # up → 80×45（注意：40×22 上采样后为 80×44，需要对齐）
        self.conv11 = _ConvBNRelu(512, 256)
        self.conv12 = _ConvBNRelu(256, 256)
        self.conv13 = _ConvBNRelu(256, 256)
        # up → 160×90（或88）
        self.conv14 = _ConvBNRelu(256, 128)
        self.conv15 = _ConvBNRelu(128, 128)
        # up → 320×180（或176）
        self.conv16 = _ConvBNRelu(128, 64)
        self.conv17 = _ConvBNRelu(64,  64)
        # up → 640×360（或352）
        self.conv18 = _ConvBNRelu(64,  256)

    def _encode(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.pool(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.pool(x)
        x = self.conv5(x)
        x = self.conv6(x)
        x = self.conv7(x)
        x = self.pool(x)
        x = self.conv8(x)
        x = self.conv9(x)
        x = self.conv10(x)
        x = self.pool(x)
        return x

    def _decode(self, x):
        x = self.up(x)
        x = self.conv11(x)
        x = self.conv12(x)
        x = self.conv13(x)
        x = self.up(x)
        x = self.conv14(x)
        x = self.conv15(x)
        x = self.up(x)
        x = self.conv16(x)
        x = self.conv17(x)
        x = self.up(x)
        x = self.conv18(x)
        return x   # (B, 256, H, W)

    def forward(self, x):
        return self._decode(self._encode(x))


class TrackNet(_TrackNetBase):
    """
    球追踪网络。
    输入：9通道（3帧BGR各3通道），640×360
    输出：热力图最大值通道对应球位置
    从 256 通道输出中取最大激活值通道，等效单通道热力图。
    """
    def __init__(self):
        super().__init__(in_channels=9)

    def forward(self, x):
        out = super().forward(x)          # (B, 256, H, W)
        return out.max(dim=1, keepdim=True).values  # (B, 1, H, W)


class CourtDetectorNet(_TrackNetBase):
    """
    球场关键点检测网络。
    输入：3通道（单帧BGR），640×360
    conv18输出实际是15通道（从权重shape实测：conv18 64->15）
    """
    def __init__(self):
        # 先用父类初始化（conv18暂时是256通道）
        super().__init__(in_channels=3)
        # 覆盖conv18为真实的15通道输出
        self.conv18 = _ConvBNRelu(64, 15)

    def forward(self, x):
        out = super().forward(x)          # (B, 15, H, W)
        return torch.sigmoid(out)


# ══════════════════════════════════════════════════════════════════
#  3. 公共工具：权重加载
# ══════════════════════════════════════════════════════════════════

def load_weights(model: nn.Module, path: str, device) -> bool:
    """
    加载权重，兼容多种保存格式：
      - 纯 state_dict
      - {'model_state_dict': ...}
      - {'state_dict': ...}
    返回是否成功。
    """
    if not os.path.exists(path):
        return False
    try:
        ckpt = torch.load(path, map_location=device)
        if isinstance(ckpt, dict):
            state = (ckpt.get('model_state_dict')
                     or ckpt.get('state_dict')
                     or ckpt)
        else:
            state = ckpt
        # 去掉 DataParallel 的 "module." 前缀
        state = {k.replace('module.', ''): v for k, v in state.items()}
        missing, unexpected = model.load_state_dict(state, strict=False)
        if missing:
            print(f"  [警告] 缺少 {len(missing)} 个权重键（可能是架构版本差异，通常不影响推理）")
        return True
    except Exception as e:
        print(f"  [错误] 权重加载失败: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
#  4. 球追踪器（YOLOv8 版本，带卡尔曼滤波补帧）
#
#  权重下载：
#    https://huggingface.co/RJTPP/tennis-ball-detection
#    → 点 Files → 下载 tennisball.pt
#    → 保存为 weights/tennisball.pt
#
#  安装依赖：pip install ultralytics
# ══════════════════════════════════════════════════════════════════

class KalmanBallFilter:
    """
    简单卡尔曼滤波器，用于在 YOLO 漏检时预测球的位置。
    状态向量：[x, y, vx, vy]（位置 + 速度）
    """
    def __init__(self):
        self.kf = cv2.KalmanFilter(4, 2)
        # 状态转移矩阵（匀速运动模型）
        self.kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=np.float32)
        # 观测矩阵（只观测位置）
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float32)
        self.kf.processNoiseCov     = np.eye(4, dtype=np.float32) * 1e-2
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1e-1
        self.kf.errorCovPost        = np.eye(4, dtype=np.float32)
        self.initialized = False

    def update(self, x: float, y: float):
        """用观测值更新，返回修正后的位置。"""
        if not self.initialized:
            self.kf.statePost      = np.array([[x],[y],[0],[0]], dtype=np.float32)
            self.kf.errorCovPost   = np.eye(4, dtype=np.float32) * 0.1
            self.initialized = True
            return x, y
        self.kf.predict()
        meas  = np.array([[x],[y]], dtype=np.float32)
        state = self.kf.correct(meas)
        return float(state[0, 0]), float(state[1, 0])

    def predict(self):
        """漏检时调用：推进并返回预测位置"""
        if not self.initialized:
            return None
        state = self.kf.predict()
        return float(state[0, 0]), float(state[1, 0])


def resolve_torch_device(device: str = None) -> str:
    device = str(device).strip() if device is not None else None
    if not device or device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device in ("0", "cuda:0"):
        device = "cuda"
    if device.startswith("cuda") and not torch.cuda.is_available():
        print("[设备] CUDA 不可用，自动切换到 CPU")
        return "cpu"
    return device


class BallTracker:
    """
    YOLOv8 球追踪器。
    - 使用 RJTPP/tennis-ball-detection 的 tennisball.pt 权重
    - 卡尔曼滤波补偿漏检帧（最多连续 MAX_MISS 帧）
    - 流式读帧，不把整个视频载入内存
    """
    MAX_MISS = 8   # 最多连续补帧数，超过则标 None

    def __init__(self, weights_path: str, device: str = 'auto',
                 conf: float = 0.25, imgsz: int = 640,
                 person_weights: str = '', person_conf: float = 0.5):
        from ultralytics import YOLO
        device = resolve_torch_device(device)
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"找不到 YOLOv8 网球权重: {weights_path}\n"
                "请下载：https://huggingface.co/RJTPP/tennis-ball-detection\n"
                "Files → tennisball.pt → 保存为 weights/tennisball.pt"
            )
        self.model  = YOLO(weights_path)
        self.device = device
        self.conf   = conf
        self.imgsz  = imgsz
        self.person_model = None
        self.person_conf  = person_conf
        if person_weights:
            if not os.path.exists(person_weights):
                os.makedirs(os.path.dirname(person_weights) or '.', exist_ok=True)
                url = (f'https://github.com/ultralytics/assets/releases/download'
                       f'/v0.0.0/{os.path.basename(person_weights)}')
                print(f'[BallTracker] 下载人员检测模型: {url} → {person_weights}')
                try:
                    import urllib.request
                    urllib.request.urlretrieve(url, person_weights)
                    print('[BallTracker] 下载完成 ✓')
                except Exception as e:
                    print(f'[BallTracker] 下载失败: {e}，尝试 ultralytics 自动下载')
                    try:
                        _ = YOLO(os.path.basename(person_weights))
                        import shutil
                        src = os.path.join(
                            os.path.expanduser('~'), '.cache', 'ultralytics',
                            os.path.basename(person_weights)
                        )
                        if os.path.exists(src):
                            shutil.copy2(src, person_weights)
                    except Exception as e2:
                        print(f'[BallTracker] 人员检测模型加载失败: {e2}，跳过')
                        person_weights = None
            if person_weights and os.path.exists(person_weights):
                try:
                    self.person_model = YOLO(person_weights)
                    print(f"[BallTracker] 人员检测模型加载完成 ✓  {person_weights}"
                          f"  conf={person_conf}")
                except Exception as e:
                    print(f"[BallTracker] 人员检测模型加载失败: {e}，跳过")
        print(f"[BallTracker] YOLOv8 权重加载完成 ✓  conf={conf}  imgsz={imgsz}")

    def predict_stream(self, video_path: str, orig_w: int, orig_h: int,
                       total: int, batch_size: int = 16,
                       court: 'CourtDetector' = None,
                       viz_path: str = None,
                       court_net_model=None,
                       court_conf_thresh: float = 0.3,
                       out_frames_thresh: int = 60,
                       slow_speed_thresh: float = 0,
                       slow_frames_thresh: int = 0,
                       net_reversal_dist_m: float = 1.0,
                       person_model=None,
                       person_conf: float = 0.5) -> tuple:
        """
        流式批量推理 + 卡尔曼滤波补帧 + 球场可见性检测。

        返回 (positions, court_visible)：
          positions:     每帧球像素坐标列表
          court_visible: 每帧是否有球场（bool列表），无球场帧不纳入回合
        """
        import time
        cap      = cv2.VideoCapture(video_path)
        fps_vid  = cap.get(cv2.CAP_PROP_FPS) or 30.0
        preds         = []
        court_visible = []
        buf      = []
        buf_frames_orig = []
        buf_idx  = []
        kf       = KalmanBallFilter()
        miss_cnt = 0
        trail    = []          # 球轨迹拖尾（最近N帧），每项为 (pos, is_out, is_slow)
        TRAIL_LEN = 15
        consec_out_viz = 0
        consec_slow_viz = 0
        prev_ball_pos = None
        from collections import deque
        court_pos_buffer = deque(maxlen=30)

        # ── 初始化视频写入器 ────────────────────────────────────────
        vw = None
        if viz_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            vw = cv2.VideoWriter(viz_path, fourcc, fps_vid, (orig_w, orig_h))
            print(f"[BallTracker] 可视化视频将保存到: {viz_path}")

        # ── 预计算球场所有线的像素坐标（用于每帧绘制）────────────
        court_lines_px  = None
        court_inner_px  = None
        net_line_px     = None
        net_zone_px     = None
        out_boundary_px = None

        if viz_path and court and court.iH is not None:
            def court2px(cx, cy):
                pt = cv2.perspectiveTransform(
                    np.array([[[cx, cy]]], dtype=np.float32), court.iH
                )
                return int(pt[0,0,0]), int(pt[0,0,1])

            cw = court.corners_cw if hasattr(court, 'corners_cw') else court.corners
            court_lines_px = [(int(p[0]), int(p[1])) for p in cw]
            tl = court2px(0.0,   0.0  )
            tr = court2px(8.23,  0.0  )
            br = court2px(8.23,  23.77)
            bl = court2px(0.0,   23.77)

            net_l      = court2px(0.0,   11.885)
            net_r      = court2px(8.23,  11.885)
            svc_near_l = court2px(0.0,   11.885 - 6.4)
            svc_near_r = court2px(8.23,  11.885 - 6.4)
            svc_far_l  = court2px(0.0,   11.885 + 6.4)
            svc_far_r  = court2px(8.23,  11.885 + 6.4)
            mid_near   = court2px(4.115, 11.885 - 6.4)
            mid_net    = court2px(4.115, 11.885)
            mid_far    = court2px(4.115, 11.885 + 6.4)

            court_inner_px = [
                (svc_near_l, svc_near_r),
                (svc_far_l,  svc_far_r),
                (mid_near,   mid_far),
            ]
            net_line_px = (net_l, net_r)
            net_zone_tl = court2px(0.0,   11.885 - net_reversal_dist_m)
            net_zone_tr = court2px(8.23,  11.885 - net_reversal_dist_m)
            net_zone_br = court2px(8.23,  11.885 + net_reversal_dist_m * 1.5)
            net_zone_bl = court2px(0.0,   11.885 + net_reversal_dist_m * 1.5)
            net_zone_px = np.array(
                [net_zone_tl, net_zone_tr, net_zone_br, net_zone_bl], dtype=np.int32
            )

            if hasattr(court, 'corners_expanded'):
                out_boundary_px = [(int(p[0]), int(p[1])) for p in court.corners_expanded]

        t0 = time.time()
        mode_str = "（含可视化）" if viz_path else ""
        print(f"[BallTracker] YOLOv8 批量追踪 {total} 帧  batch={batch_size}"
              f"{mode_str}  device={self.device}...")

        def draw_frame(frame, ball_pos, is_predicted=False, is_out=False, is_slow=False,
                       person_boxes=None, net_reversal=False):
            out = frame.copy()

            if person_boxes:
                for pbox in person_boxes:
                    x1p, y1p, x2p, y2p = [int(v) for v in pbox]
                    cv2.rectangle(out, (x1p, y1p), (x2p, y2p), (255, 255, 255), 2)

            if out_boundary_px:
                for k in range(4):
                    p1_b = out_boundary_px[k]
                    p2_b = out_boundary_px[(k+1) % 4]
                    dx_b = (p2_b[0]-p1_b[0]) / 24
                    dy_b = (p2_b[1]-p1_b[1]) / 24
                    for seg in range(0, 24, 2):
                        sx1 = int(p1_b[0] + seg * dx_b)
                        sy1 = int(p1_b[1] + seg * dy_b)
                        sx2 = int(p1_b[0] + (seg+1) * dx_b)
                        sy2 = int(p1_b[1] + (seg+1) * dy_b)
                        cv2.line(out, (sx1,sy1), (sx2,sy2), (0,0,200), 1)

            if court_lines_px:
                pts = np.array(court_lines_px, dtype=np.int32)
                cv2.polylines(out, [pts], isClosed=True, color=(255,255,255), thickness=2)

            if court_inner_px:
                for p1_i, p2_i in court_inner_px:
                    cv2.line(out, p1_i, p2_i, (180,180,180), 1)

            if net_line_px:
                p1, p2 = net_line_px
                dx = (p2[0]-p1[0]) / 20
                dy = (p2[1]-p1[1]) / 20
                for seg in range(0, 20, 2):
                    x1 = int(p1[0] + seg * dx)
                    y1 = int(p1[1] + seg * dy)
                    x2 = int(p1[0] + (seg+1) * dx)
                    y2 = int(p1[1] + (seg+1) * dy)
                    cv2.line(out, (x1,y1), (x2,y2), (0,255,255), 2)

            if net_zone_px is not None:
                overlay = out.copy()
                cv2.fillPoly(overlay, [net_zone_px], (180, 100, 180))
                cv2.addWeighted(overlay, 0.25, out, 0.75, 0, out)

            for ti, (tp, tp_out, tp_slow) in enumerate(trail):
                alpha = (ti + 1) / len(trail)
                if tp_out:
                    color_t = (0, 0, 255)
                elif tp_slow:
                    color_t = (255, 0, 255)
                else:
                    r = int(255 * alpha)
                    g = int(255 * (1 - alpha * 0.5))
                    color_t = (0, g, r)
                radius = max(2, int(4 * alpha))
                cv2.circle(out, (int(tp[0]), int(tp[1])), radius, color_t, -1)

            if ball_pos:
                bx, by = int(ball_pos[0]), int(ball_pos[1])
                if is_out:
                    color = (0, 0, 255)
                elif is_slow:
                    color = (255, 0, 255)
                elif is_predicted:
                    color = (0, 165, 255)
                else:
                    color = (0, 255, 0)
                cv2.circle(out, (bx, by), 8, color, -1)
                cv2.circle(out, (bx, by), 10, (255,255,255), 1)
                if is_out:
                    label = "OUT"
                    cv2.circle(out, (bx, by), 18, (0, 0, 255), 2)
                elif is_slow:
                    label = "SLOW"
                elif is_predicted:
                    label = "ball(pred)"
                else:
                    label = "ball"
                cv2.putText(out, label, (bx+12, by-6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            # 触网特效：白色闪环 + 黄色 NET 文字
            if net_reversal and ball_pos:
                bx, by = int(ball_pos[0]), int(ball_pos[1])
                for r in range(10, 50, 6):
                    cv2.circle(out, (bx, by), r, (0, 255, 255), max(1, 4 - r // 12))
                cv2.circle(out, (bx, by), 20, (255, 255, 255), 3)
                cv2.putText(out, "NET", (bx - 30, by - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

            return out

        def flush(frames_bgr, frame_indices, frames_orig):
            nonlocal miss_cnt, consec_out_viz, consec_slow_viz, prev_ball_pos

            # ── 球场可见性检测（CourtDetectorNet）────────────────────
            batch_court_visible = [True] * len(frames_bgr)
            if court_net_model is not None:
                for j_c, f_bgr in enumerate(frames_bgr):
                    inp = cv2.resize(f_bgr, (640, 360))
                    inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                    inp_t = torch.FloatTensor(inp.transpose(2,0,1)).unsqueeze(0)
                    if next(court_net_model.parameters()).is_cuda:
                        inp_t = inp_t.cuda()
                    with torch.no_grad():
                        hms = court_net_model(inp_t)[0].cpu().numpy()
                    max_conf = max(hms[ch].max() for ch in range(4))
                    batch_court_visible[j_c] = max_conf >= court_conf_thresh

            # ── YOLO 球检测 ───────────────────────────────────────────
            results = self.model.predict(
                frames_bgr,
                conf=self.conf,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False,
            )

            # ── 人员检测（可选）────────────────────────────────────────
            person_boxes_list = [[] for _ in range(len(frames_bgr))]
            if self.person_model is not None:
                person_results = self.person_model.predict(
                    frames_bgr,
                    conf=self.person_conf,
                    imgsz=self.imgsz,
                    device=self.device,
                    verbose=False,
                )
                for j_p, pr in enumerate(person_results):
                    if pr.boxes is not None and len(pr.boxes) > 0:
                        for bi in range(len(pr.boxes)):
                            if int(pr.boxes.cls[bi].item()) == 0:
                                person_boxes_list[j_p].append(
                                    pr.boxes.xyxy[bi].cpu().numpy()
                                )

            for j, res in enumerate(results):
                court_visible.append(batch_court_visible[j])
                boxes = res.boxes
                is_pred = False
                if boxes is not None and len(boxes) > 0:
                    best = boxes.conf.argmax()
                    xyxy = boxes.xyxy[best].cpu().numpy()
                    cx   = float((xyxy[0] + xyxy[2]) / 2)
                    cy   = float((xyxy[1] + xyxy[3]) / 2)
                    cx, cy = kf.update(cx, cy)
                    preds.append((cx, cy))
                    miss_cnt = 0
                else:
                    miss_cnt += 1
                    if miss_cnt <= BallTracker.MAX_MISS:
                        pred = kf.predict()
                        preds.append(pred)
                        cx, cy = (pred[0], pred[1]) if pred else (None, None)
                        is_pred = True
                    else:
                        preds.append(None)
                        cx, cy = None, None

                # ── 判断球是否在人员检测框 1.5 倍范围内 ──────────────
                ball_near_person = False
                if cx is not None and person_boxes_list[j]:
                    for pbox in person_boxes_list[j]:
                        x1p, y1p, x2p, y2p = pbox
                        bw, bh = x2p - x1p, y2p - y1p
                        cx_box, cy_box = (x1p + x2p) / 2, (y1p + y2p) / 2
                        x1e = cx_box - bw * 0.75
                        x2e = cx_box + bw * 0.75
                        y1e = cy_box - bh * 0.75
                        y2e = cy_box + bh * 0.75
                        if x1e <= cx <= x2e and y1e <= cy <= y2e:
                            ball_near_person = True
                            break

                # ── 落地/击球/触网检测（对称窗口 + 速度幅度过滤）────────
                # 修复：原代码用 arr[-1] 作为 y2，导致 vy_after 窗口随 k 变化，
                # 不同 k 对应的速度尺度不一致，空中帧极易误触发。
                # 修正：以缓冲区中间帧为锚点，取对称 HALF 帧差分估计速度，
                # 并加入 vy 幅度阈值和 vy/vx 比例约束（真实落地主要在 y 方向反转）。
                j_abs = frame_indices[j]
                ball_near_bounce = False
                ball_near_hit = False
                ball_net_reversal = False
                if cx is not None and court is not None \
                        and hasattr(court, 'H') and court.H is not None:
                    cp = court.pixel_to_court(cx, cy)
                    court_pos_buffer.append((j_abs, cp[0], cp[1]))
                    if len(court_pos_buffer) >= 25:
                        arr  = list(court_pos_buffer)
                        HALF = 8
                        mid  = len(arr) // 2
                        if (arr[mid - HALF][2] is not None
                                and arr[mid][2] is not None
                                and arr[mid + HALF][2] is not None):
                            vy_before = arr[mid][2] - arr[mid - HALF][2]
                            vy_after  = arr[mid + HALF][2] - arr[mid][2]
                            speed_ok  = (abs(vy_before) > 0.04
                                         and abs(vy_after) > 0.04)
                            if vy_before * vy_after < 0 and speed_ok:
                                cy_mid = arr[mid][2]
                                # 触网检测：网 5m 内的慢速（球速由调用方判定）
                                net_limit = net_reversal_dist_m * 1.5 if cy_mid > 11.885 else net_reversal_dist_m
                                if abs(cy_mid - 11.885) < net_limit and abs(j_abs - arr[mid][0]) <= 5:
                                    ball_net_reversal = True
                                # 落地/击球：看 vy/vx 比例
                                vx_b_vals = [
                                    arr[t][1] - arr[t - 1][1]
                                    for t in range(mid - HALF + 1, mid)
                                    if arr[t][1] is not None
                                    and arr[t - 1][1] is not None
                                ]
                                vx_a_vals = [
                                    arr[t][1] - arr[t - 1][1]
                                    for t in range(mid + 1, mid + HALF)
                                    if arr[t][1] is not None
                                    and arr[t - 1][1] is not None
                                ]
                                if len(vx_b_vals) >= 3 and len(vx_a_vals) >= 3:
                                    vx_b = sum(vx_b_vals) / len(vx_b_vals)
                                    vx_a = sum(vx_a_vals) / len(vx_a_vals)
                                    # 真实落地：y 方向变化幅度应明显大于 x 方向
                                    vy_ratio = (abs(vy_after - vy_before)
                                                / (abs(vx_a - vx_b) + 1e-6))
                                    if vy_ratio >= 1.5:
                                        if abs(j_abs - arr[mid][0]) <= 5:
                                            if vx_b * vx_a > 0:
                                                ball_near_bounce = True
                                            else:
                                                ball_near_hit = True

                # ── 可视化 ────────────────────────────────────────────
                if vw is not None:
                    ball_pos = (cx, cy) if cx is not None else None
                    # 判断球是否在网范围内（用于慢速+网标紫）
                    ball_near_net = False
                    if cx is not None and court is not None \
                            and hasattr(court, 'H') and court.H is not None:
                        cp_viz = court.pixel_to_court(cx, cy)
                        net_limit = net_reversal_dist_m * 1.5 if cp_viz[1] > 11.885 else net_reversal_dist_m
                        if abs(cp_viz[1] - 11.885) < net_limit:
                            ball_near_net = True
                    ball_is_out = False
                    if ball_pos and court is not None:
                        if court.is_out_px(ball_pos[0], ball_pos[1]):
                            consec_out_viz += 1
                        else:
                            consec_out_viz = 0
                        ball_is_out = (consec_out_viz >= out_frames_thresh)
                    ball_is_slow = False
                    if ball_pos and slow_speed_thresh > 0 and prev_ball_pos is not None:
                        if ball_near_person or ball_near_bounce or ball_near_hit:
                            consec_slow_viz = 0
                        else:
                            speed = np.hypot(ball_pos[0] - prev_ball_pos[0],
                                             ball_pos[1] - prev_ball_pos[1])
                            if speed < slow_speed_thresh:
                                consec_slow_viz += 1
                            else:
                                consec_slow_viz = 0
                        ball_is_slow = (consec_slow_viz >= slow_frames_thresh) and ball_near_net
                    if ball_pos:
                        trail.append((ball_pos, ball_is_out, ball_is_slow))
                        if len(trail) > TRAIL_LEN:
                            trail.pop(0)
                    prev_ball_pos = ball_pos
                    orig = frames_orig[j] if frames_orig else frames_bgr[j]
                    annotated = draw_frame(orig, ball_pos, is_pred, ball_is_out, ball_is_slow,
                                           person_boxes=person_boxes_list[j],
                                           net_reversal=ball_net_reversal)
                    if not batch_court_visible[j]:
                        mask = np.zeros_like(annotated)
                        annotated = cv2.addWeighted(annotated, 0.5, mask, 0.5, 0)
                        cv2.putText(annotated, "NO COURT - SKIPPED",
                                    (orig_w//2 - 180, orig_h//2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (80,80,80), 3)
                    vw.write(annotated)

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            buf.append(frame)
            buf_frames_orig.append(frame if viz_path else None)
            buf_idx.append(frame_idx)
            frame_idx += 1

            if len(buf) >= batch_size:
                flush(buf, buf_idx, buf_frames_orig)
                buf.clear(); buf_idx.clear(); buf_frames_orig.clear()

            if frame_idx % 1000 == 0:
                elapsed = time.time() - t0
                fps_est = frame_idx / max(elapsed, 1e-6)
                remain  = (total - frame_idx) / max(fps_est, 1e-6)
                print(f"  {frame_idx}/{total} ({100*frame_idx//total}%)  "
                      f"{fps_est:.1f}帧/s  剩余约{remain:.0f}s")

        cap.release()
        if buf:
            flush(buf, buf_idx, buf_frames_orig)
        if vw:
            vw.release()
            print(f"[BallTracker] 可视化视频已保存: {viz_path}")

        hit = sum(1 for p in preds if p is not None)
        n   = len(preds)
        cv  = sum(1 for v in court_visible if v)
        elapsed = time.time() - t0
        print(f"[BallTracker] 完成：{n}帧  检测到球 {hit}帧 ({100*hit//max(n,1)}%)"
              f"  球场可见 {cv}帧 ({100*cv//max(n,1)}%)  总耗时 {elapsed:.1f}s")
        return preds, court_visible


# ══════════════════════════════════════════════════════════════════
#  5. 球场检测器（自动 + 手动标定两种模式）
# ══════════════════════════════════════════════════════════════════

# 标准单打球场4个角（米）
# 标定顺序：0=左上, 1=右上, 2=左下, 3=右下
_COURT_STD = np.float32([
    [0.0,   0.0  ],   # 0=左上
    [8.23,  0.0  ],   # 1=右上
    [0.0,   23.77],   # 2=左下
    [8.23,  23.77],   # 3=右下
])


class CourtDetector:
    def __init__(self, weights_path: str = '', device: str = 'auto'):
        device = resolve_torch_device(device)
        self.dev    = torch.device(device)
        self.H      = None
        self.iH     = None
        self.corners = None

        self.model = None
        if weights_path and os.path.exists(weights_path):
            net = CourtDetectorNet().to(self.dev)
            ok  = load_weights(net, weights_path, self.dev)
            if ok:
                net.eval()
                self.model = net
                print("[CourtDetector] 模型加载完成 ✓")
            else:
                print("[CourtDetector] 模型加载失败，将使用手动标定")
        else:
            print("[CourtDetector] 未找到权重文件，将使用手动标定")

    @torch.no_grad()
    def _auto_detect(self, frame: np.ndarray) -> bool:
        oh, ow = frame.shape[:2]
        inp = cv2.resize(frame, (640, 360))
        inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        inp = torch.FloatTensor(inp.transpose(2, 0, 1)).unsqueeze(0).to(self.dev)

        hms = self.model(inp)[0].cpu().numpy()   # (15, 360, 640)

        debug_img = cv2.resize(frame, (640, 360))
        colors_dbg = [
            (0,255,0),(0,200,255),(255,100,0),(200,0,255),
            (0,255,255),(255,0,255),(255,255,0),(128,255,0),
            (0,128,255),(255,128,0),(128,0,255),(0,255,128),
            (255,0,128),(128,128,255),(255,128,128),
        ]
        kp_labels = [
            '0-近端左','1-近端右','2-远端右','3-远端左',
            '4-发球左','5-发球右','6-网左','7-网右',
            '8-中线近','9-中线远','10','11','12','13','14'
        ]
        print(f"  [CourtDetector] 全部15个关键点置信度：")
        for ch in range(15):
            hm = hms[ch]
            hy, hx = np.unravel_index(hm.argmax(), hm.shape)
            conf = hm.max()
            print(f"    ch{ch:2d} {kp_labels[ch]}: 置信度={conf:.3f}  位置=({hx},{hy})")
            if conf > 0.1:
                cv2.circle(debug_img, (hx, hy), 6, colors_dbg[ch], -1)
                cv2.putText(debug_img, f"{ch}:{conf:.2f}",
                            (hx+5, hy-5), cv2.FONT_HERSHEY_SIMPLEX,
                            0.35, colors_dbg[ch], 1)
        cv2.imwrite("court_detection_debug.jpg", debug_img)
        print(f"  [CourtDetector] 检测结果已保存: court_detection_debug.jpg")

        corners = []
        for ch in range(4):
            hm = hms[ch]
            conf = hm.max()
            if conf < 0.05:
                print(f"  [CourtDetector] 关键点{ch} 置信度过低 ({conf:.3f})，切换手动标定")
                return False
            hy, hx = np.unravel_index(hm.argmax(), hm.shape)
            corners.append([hx * ow / 640, hy * oh / 360])
            print(f"  [CourtDetector] 使用关键点{ch}: 置信度={conf:.3f}")

        self.corners = np.float32(corners)
        self._calc_homography()
        return True

    def _manual_calibrate(self, frame: np.ndarray) -> bool:
        self._pts = []
        oh, ow   = frame.shape[:2]
        scale    = min(1.0, 1280 / ow)
        dw, dh   = int(ow * scale), int(oh * scale)
        disp     = cv2.resize(frame, (dw, dh))

        labels = ['1-左上角', '2-右上角', '3-左下角', '4-右下角']
        colors = [(0, 255, 0), (0, 200, 255), (255, 100, 0), (200, 0, 255)]

        def on_click(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(self._pts) < 4:
                rx, ry = x / scale, y / scale
                self._pts.append([rx, ry])
                print(f"  ✓ {labels[len(self._pts)-1]}: ({rx:.0f}, {ry:.0f})")

        win = '球场标定 — 依次点击4个角点  [任意键确认 / ESC取消]'
        cv2.namedWindow(win)
        cv2.setMouseCallback(win, on_click)
        print('\n[标定] 请依次点击球场4个角点：')
        print('  近端底线左角 → 近端底线右角 → 远端底线右角 → 远端底线左角')

        while True:
            tmp = disp.copy()
            for i, pt in enumerate(self._pts):
                px, py = int(pt[0] * scale), int(pt[1] * scale)
                cv2.circle(tmp, (px, py), 9, colors[i], -1)
                cv2.putText(tmp, labels[i], (px + 12, py - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[i], 2)
            if len(self._pts) < 4:
                hint = f'请点击: {labels[len(self._pts)]}'
            else:
                hint = '标定完成！按任意键继续'
            cv2.putText(tmp, hint, (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.imshow(win, tmp)

            k = cv2.waitKey(1)
            if k == 27:
                cv2.destroyAllWindows()
                return False
            if len(self._pts) == 4 and k != -1:
                break

        cv2.destroyAllWindows()
        self.corners = np.float32(self._pts)
        self._calc_homography()
        return True

    def set_manual_corners(self, points) -> bool:
        if points is None or len(points) != 4:
            return False
        self.corners = np.float32([[float(p["x"]), float(p["y"])] for p in points])
        self._calc_homography()
        return True

    def calibrate(self, frame: np.ndarray, allow_manual: bool = True) -> bool:
        """先尝试自动检测，失败则弹窗手动标定"""
        if self.model is not None:
            print('[CourtDetector] 尝试自动检测...')
            if self._auto_detect(frame):
                print('[CourtDetector] 自动检测成功 ✓')
                return True
            print('[CourtDetector] 自动检测失败，切换手动标定')
        if not allow_manual:
            print('[CourtDetector] API 模式禁止 OpenCV 弹窗手动标定')
            return False
        return self._manual_calibrate(frame)

    def _calc_homography(self):
        self.H,  _ = cv2.findHomography(self.corners, _COURT_STD)
        self.iH, _ = cv2.findHomography(_COURT_STD, self.corners)
        c = self.corners
        self.corners_cw = np.array([c[0], c[1], c[3], c[2]], dtype=np.float32)
        self._margin = 0.3
        self._bottom_margin = 0.0
        self._px_per_m = float(np.hypot(
            self.corners_cw[1][0]-self.corners_cw[0][0],
            self.corners_cw[1][1]-self.corners_cw[0][1]
        )) / 8.23
        self._update_expanded()

    def set_margin(self, margin_m: float):
        self._margin = margin_m
        if hasattr(self, 'corners_cw'):
            self._px_per_m = float(np.hypot(
                self.corners_cw[1][0]-self.corners_cw[0][0],
                self.corners_cw[1][1]-self.corners_cw[0][1]
            )) / 8.23
            self._update_expanded()

    def set_bottom_margin(self, margin_m: float):
        self._bottom_margin = margin_m
        if hasattr(self, 'corners_cw'):
            self._update_expanded()

    def _update_expanded(self):
        margin_px = self._margin * self._px_per_m
        self.corners_expanded = CourtDetector._expand_polygon(self.corners_cw, margin_px)
        if self._bottom_margin != 0.0:
            bottom_px = self._bottom_margin * self._px_per_m
            self.corners_expanded[2][1] += bottom_px
            self.corners_expanded[3][1] += bottom_px

    @staticmethod
    def _expand_polygon(pts: np.ndarray, margin_px: float) -> np.ndarray:
        n = len(pts)
        expanded = []
        for i in range(n):
            prev_pt = pts[(i-1) % n]
            curr_pt = pts[i]
            next_pt = pts[(i+1) % n]
            def edge_normal(p1, p2):
                dx, dy = float(p2[0]-p1[0]), float(p2[1]-p1[1])
                length = np.hypot(dx, dy) + 1e-6
                return np.array([dy/length, -dx/length])
            n1 = edge_normal(prev_pt, curr_pt)
            n2 = edge_normal(curr_pt, next_pt)
            bisector = n1 + n2
            bl = float(np.linalg.norm(bisector)) + 1e-6
            bisector = bisector / bl
            cos_half = max(float(np.dot(n1, bisector)), 0.1)
            offset = bisector * (margin_px / cos_half)
            expanded.append([curr_pt[0]+offset[0], curr_pt[1]+offset[1]])
        return np.array(expanded, dtype=np.float32)

    def pixel_to_court(self, px: float, py: float):
        if self.H is None:
            return None
        res = cv2.perspectiveTransform(
            np.array([[[px, py]]], dtype=np.float32), self.H
        )
        return float(res[0, 0, 0]), float(res[0, 0, 1])

    def pixel_speed_to_ms(self, px1: float, py1: float,
                           px2: float, py2: float, fps: float) -> float:
        """
        将两帧之间的像素位移转换为真实速度（m/s）。

        ──── 为什么需要这个方法 ────
        透视投影下，球场远端的 1 米在画面里只占近端的约一半像素。
        直接比较像素位移会导致：
          · 远端慢速球因像素小被误判为"慢速"→ 在正常回合中触发切割
          · 近端快速球因像素大反而难以触发慢速检测
        需要按球在画面中的 y 位置乘以透视缩放系数进行校正。

        ──── 两条路径 ────
        优先路径（精确）：单应矩阵 pixel_to_court → 直接得到球场坐标欧氏距离（m）
        回退路径（近似）：根据"近端/远端基线像素长度"线性插值缩放系数，
                          再将像素位移除以该系数得到米数。

        回退路径的系数计算：
          · 近端基线（画面下方，y 大）：白线像素长 / 8.23m → near_px_per_m
          · 远端基线（画面上方，y 小）：白线像素长 / 8.23m → far_px_per_m
          · 在球的 y 位置做线性插值 → local_px_per_m
          · dist_m = pixel_dist / local_px_per_m
        """
        # ── 优先路径：单应矩阵（精确，已处理全部透视畸变）────────────
        if self.H is not None:
            c1 = self.pixel_to_court(px1, py1)
            c2 = self.pixel_to_court(px2, py2)
            if c1 is not None and c2 is not None:
                dist_m = float(np.hypot(c2[0] - c1[0], c2[1] - c1[1]))
                return dist_m * fps

        # ── 回退路径：透视缩放系数线性插值 ───────────────────────────
        if not hasattr(self, 'corners_cw') or self.corners_cw is None:
            # 无任何标定信息，返回原始像素距离（调用者自己决定如何使用）
            return float(np.hypot(px2 - px1, py2 - py1))

        # corners_cw = [左上, 右上, 右下, 左下]（顺时针梯形）
        cw           = self.corners_cw
        far_left,  far_right  = cw[0], cw[1]   # 远端基线（画面靠上，y 小）
        near_right, near_left = cw[2], cw[3]   # 近端基线（画面靠下，y 大）

        COURT_W_M     = 8.23   # 单打球场宽度（米）
        far_px_per_m  = float(np.hypot(far_right[0]  - far_left[0],
                                       far_right[1]  - far_left[1])) / COURT_W_M
        near_px_per_m = float(np.hypot(near_right[0] - near_left[0],
                                       near_right[1] - near_left[1])) / COURT_W_M

        # 在两帧中点的像素 y 坐标处插值
        mid_py = (py1 + py2) / 2.0
        far_y  = float(far_left[1]  + far_right[1])  / 2.0
        near_y = float(near_left[1] + near_right[1]) / 2.0

        if abs(near_y - far_y) < 1.0:
            local_px_per_m = (far_px_per_m + near_px_per_m) / 2.0
        else:
            t = (mid_py - far_y) / (near_y - far_y)
            t = max(0.0, min(1.0, t))                           # 限制在 [0,1]
            local_px_per_m = far_px_per_m * (1.0 - t) + near_px_per_m * t

        if local_px_per_m < 1e-6:
            return float(np.hypot(px2 - px1, py2 - py1))       # 标定异常保护

        dist_m = float(np.hypot(px2 - px1, py2 - py1)) / local_px_per_m
        return dist_m * fps

    def is_out(self, cx: float, cy: float, margin: float = 0.3) -> bool:
        return (cx < -margin or cx > 8.23 + margin
                or cy < -margin or cy > 23.77 + margin)

    def is_out_px(self, px: float, py: float, margin_px: float = 0.0) -> bool:
        if self.corners is None:
            return False
        corners_for_test = getattr(self, 'corners_expanded', self.corners_cw)
        pts = corners_for_test.reshape((-1, 1, 2)).astype(np.float32)
        dist = cv2.pointPolygonTest(pts, (float(px), float(py)), measureDist=True)
        return dist < 0

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump({'corners': self.corners.tolist()}, f, indent=2)
        print(f'[CourtDetector] 标定已保存: {path}')

    def load(self, path: str):
        with open(path) as f:
            data = json.load(f)
        self.corners = np.float32(data['corners'])
        self._calc_homography()
        print(f'[CourtDetector] 标定已加载: {path}')


# ══════════════════════════════════════════════════════════════════
#  6. 弹跳检测 + 轨迹分析
# ══════════════════════════════════════════════════════════════════

def detect_bounces(cy_list: list, fps: float,
                   cx_list: list = None,
                   W: int = None,
                   min_speed: float = 0.04,
                   min_gap_frames: int = None) -> set:
    """
    基于 Savitzky-Golay 平滑 + 对称差分速度估计，检测球场坐标 y 方向的弹跳帧。

    解决原始代码的三个问题：
      1. 原代码直接对带噪声的逐帧坐标求差分，单帧抖动就会触发假落点。
         → 用 Savitzky-Golay 滤波先平滑再求导，保留极值形状同时抑制噪声。
      2. 原代码用非对称窗口（vy_before 跨 W 帧，vy_after 跨 1~W 帧），
         导致速度尺度不一致，空中段极易误触发。
         → 改为对称半窗口 hw，前后速度具有相同的时间尺度。
      3. 缺乏 vy/vx 比例约束，空中击球引起的小幅 y 方向抖动也会误判。
         → 要求 y 方向速度变化幅度显著大于 x 方向（真实落地主要在 y 轴反转）。

    参数：
      cy_list       每帧球场 y 坐标列表（含 None 表示未检测到球）
      fps           视频帧率
      cx_list       每帧球场 x 坐标列表（含 None），用于 vy/vx 比例约束（可选）
      W             平滑/差分半窗口（帧），None 则自动取 fps*0.1
      min_speed     弹跳前后最小 vy 幅度（米/帧），低于此忽略噪声
      min_gap_frames 两次落点最小间隔帧数，None 则自动取 fps*0.3

    返回：弹跳帧的索引集合（相对于 cy_list 的下标）
    """
    n = len(cy_list)
    if W is None:
        W = max(3, int(fps * 0.1))
    if min_gap_frames is None:
        min_gap_frames = max(10, int(fps * 0.3))

    # ── Step 1: 线性插值填充 None ──────────────────────────────────
    vals = list(cy_list)
    valid_idxs = [i for i, v in enumerate(vals) if v is not None]
    if len(valid_idxs) < W * 2 + 1:
        return set()

    for i in range(n):
        if vals[i] is not None:
            continue
        left  = max((k for k in valid_idxs if k < i), default=None)
        right = min((k for k in valid_idxs if k > i), default=None)
        if left is not None and right is not None:
            t = (i - left) / (right - left)
            vals[i] = cy_list[left] + t * (cy_list[right] - cy_list[left])
        elif left is not None:
            vals[i] = cy_list[left]
        elif right is not None:
            vals[i] = cy_list[right]
        else:
            vals[i] = 0.0

    vals = [v if v is not None else 0.0 for v in vals]

    # ── Step 2: Savitzky-Golay 平滑（保留极值形状，抑制帧间噪声）──
    wl = W * 2 + 1
    if wl > n:
        return set()
    if wl % 2 == 0:
        wl -= 1
    wl = max(wl, 5)
    smooth = savgol_filter(vals, window_length=wl, polyorder=2)

    # ── Step 3: 对称差分估计速度 ───────────────────────────────────
    hw = max(2, W // 2)
    bounces    = set()
    last_bounce = -min_gap_frames

    for j in range(hw, n - hw):
        if cy_list[j] is None:
            continue
        vy_before = smooth[j] - smooth[j - hw]
        vy_after  = smooth[j + hw] - smooth[j]

        # 速度幅度过滤（排除微弱抖动）
        if abs(vy_before) < min_speed or abs(vy_after) < min_speed:
            continue

        # 方向翻转：下降（负）→ 上升（正）= 弹跳
        if not (vy_before < 0 and vy_after > 0):
            continue

        # vy/vx 比例约束（可选）：真实落地的 y 反转幅度应远大于 x 方向变化
        if cx_list is not None:
            cx_b = cx_list[j - hw] if (j - hw < len(cx_list)
                                        and cx_list[j - hw] is not None) else None
            cx_m = cx_list[j]       if (j < len(cx_list)
                                        and cx_list[j] is not None) else None
            cx_a = cx_list[j + hw]  if (j + hw < len(cx_list)
                                        and cx_list[j + hw] is not None) else None
            if cx_b is not None and cx_m is not None and cx_a is not None:
                vx_before = cx_m - cx_b
                vx_after  = cx_a - cx_m
                vy_change = abs(vy_after - vy_before)
                vx_change = abs(vx_after - vx_before)
                vy_ratio  = vy_change / (vx_change + 1e-6)
                if vy_ratio < 1.5:
                    continue

        # 最小间距过滤（防止同一落点多次触发）
        if j - last_bounce >= min_gap_frames:
            bounces.add(j)
            last_bounce = j

    return bounces


def interpolate_positions(pos: list, max_gap: int = 8) -> list:
    """对短暂丢球（≤max_gap 帧）做线性插值"""
    res = list(pos)
    n, i = len(res), 0
    while i < n:
        if res[i] is None:
            j = i + 1
            while j < n and res[j] is None:
                j += 1
            if j - i <= max_gap and i > 0 and j < n:
                x0, y0 = res[i - 1]
                x1, y1 = res[j]
                for k in range(j - i):
                    t = (k + 1) / (j - i + 1)
                    res[i + k] = (x0 + t * (x1 - x0), y0 + t * (y1 - y0))
            i = j
        else:
            i += 1
    return res


def _calc_speed(p1, p2) -> float:
    """两帧之间的像素位移（速度代理）"""
    if p1 is None or p2 is None:
        return 0.0
    return float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))


def detect_rallies(pos: list,
                   court: CourtDetector,
                   fps: float,
                   court_visible: list = None,
                   margin: float = 0.3,
                   min_sec: float = 1.0,
                   buf_after_sec: float = 0.5,
                   out_frames_thresh: int = 5,
                   slow_speed_thresh: float = 0,
                   slow_frames_thresh: int = 0,
                   detect_net_reversal: bool = False,
                   net_reversal_dist_m: float = 1.0,
                   net_reversal_frames: int = 3,
                   net_use_reversal: bool = False) -> list:
    """
    回合结束检测：连续出界 + 慢速球 + 球网方向反转

    1. 出界：连续 out_frames_thresh 帧（即 out_sec 秒）坐标在红线外 → 触发
    2. 慢速：球速低于 slow_speed_thresh 持续 slow_frames_thresh 帧 → 触发
    3. 球网反转：--net 时用方向反转+能量衰减；否则用慢速+5m

    参数：
      margin                出界容差（米），默认 0.0
      out_frames_thresh     连续出界帧数阈值
      net_reversal_dist_m   球网附近检测范围（米），默认 1.0
      net_reversal_frames   速度方向比较的间隔帧数，默认 3
      net_use_reversal      为 True 时使用方向反转+能量衰减模式
    """
    pos_raw           = list(pos)
    no_court_triggers = []

    # ── 无球场帧 → 强制作为回合结束触发点 ──────────────────────────
    if court_visible is not None:
        no_court = sum(1 for v in court_visible if not v)
        print(f'[Segmenter] 无球场帧: {no_court}/{len(pos_raw)}')
        prev_visible = True
        for i, visible in enumerate(court_visible):
            if not visible and prev_visible:
                no_court_triggers.append((i, 'no_court'))
            if not visible:
                pos_raw[i] = None
            prev_visible = visible
        print(f'[Segmenter] 无球场切断点: {len(no_court_triggers)} 个')

    total  = len(pos_raw)
    min_fr = int(min_sec      * fps)
    af_fr  = int(buf_after_sec * fps)

    # ── 诊断：前10个真实检测帧 ────────────────────────────────────
    print('[Segmenter] 前10个真实检测帧诊断（像素空间判断）：')
    count = 0
    for i, p in enumerate(pos_raw):
        if p is None or count >= 10:
            continue
        tag = 'OUT' if court.is_out_px(p[0], p[1]) else 'IN'
        print(f'  帧{i}: 像素({p[0]:.0f},{p[1]:.0f}) [{tag}]')
        count += 1

    # ── 逐帧检测：连续出界帧超过阈值才触发 ────────────────────────
    event_frames = []
    consec_out   = 0
    for i in range(total):
        p = pos_raw[i]
        if p is not None and court.is_out_px(p[0], p[1]):
            consec_out += 1
            if consec_out == out_frames_thresh:
                event_frames.append((i - out_frames_thresh + 1, 'out'))
        else:
            consec_out = 0

    # ── 慢速球检测 ────────────────────────────────────────────────
    if slow_speed_thresh > 0:
        # Pass 1: 预计算落点/击球帧（±20帧窗口）
        bounce_set = set()
        hit_set    = set()
        if court is not None and hasattr(court, 'H') and court.H is not None:
            cx_list_d = []
            cy_list_d = []
            for p in pos_raw:
                if p is not None:
                    cp = court.pixel_to_court(p[0], p[1])
                    cx_list_d.append(cp[0] if cp else None)
                    cy_list_d.append(cp[1] if cp else None)
                else:
                    cx_list_d.append(None)
                    cy_list_d.append(None)
            W_slow = 20
            for i in range(W_slow, total - W_slow):
                cy = cy_list_d[i]
                if cy is None or cy_list_d[i-W_slow] is None or cy_list_d[i+W_slow] is None:
                    continue
                vy_before = cy - cy_list_d[i-W_slow]
                vy_after  = cy_list_d[i+W_slow] - cy
                if vy_before * vy_after >= 0:
                    continue
                vx_before_vals = []
                vx_after_vals  = []
                for k in range(i - W_slow//2, i):
                    if cx_list_d[k] is not None and cx_list_d[k-1] is not None:
                        vx_before_vals.append(cx_list_d[k] - cx_list_d[k-1])
                for k in range(i, i + W_slow//2):
                    if cx_list_d[k] is not None and cx_list_d[k-1] is not None:
                        vx_after_vals.append(cx_list_d[k] - cx_list_d[k-1])
                if len(vx_before_vals) < 3 or len(vx_after_vals) < 3:
                    continue
                vx_before = sum(vx_before_vals) / len(vx_before_vals)
                vx_after  = sum(vx_after_vals)  / len(vx_after_vals)
                if vx_before * vx_after > 0:
                    for d in range(-3, 4):
                        bounce_set.add(i + d)
                else:
                    for d in range(-3, 4):
                        hit_set.add(i + d)

        # Pass 2: 检测慢速事件（同时按是否在网 5m 内分类）
        use_court_spd  = (court is not None
                          and hasattr(court, '_px_per_m') and court._px_per_m > 0
                          and hasattr(court, 'H') and court.H is not None)
        SLOW_M_S       = slow_speed_thresh
        eff_thresh_m   = SLOW_M_S / fps
        if use_court_spd:
            print(f'[Segmenter] 慢速模式: 球场坐标  阈值={SLOW_M_S} m/s'
                  f' ({eff_thresh_m*1000:.1f} mm/帧)')
        else:
            print(f'[Segmenter] 慢速模式: 像素坐标回退  阈值={slow_speed_thresh} px/帧'
                  f'  (球场标定不可用，精度较低)')

        consec_slow     = 0
        prev_p          = None
        prev_cp         = None
        slow_candidates = []   # 远离球网的慢速 → slow
        net_candidates  = []   # 球网 5m 内的慢速 → net_reversal
        for i in range(total):
            p  = pos_raw[i]
            cp = None
            if p is not None and use_court_spd:
                cp = court.pixel_to_court(p[0], p[1])

            if p is not None and prev_p is not None:
                if use_court_spd and cp is not None and prev_cp is not None:
                    spd    = float(np.hypot(cp[0] - prev_cp[0], cp[1] - prev_cp[1]))
                    is_slow = spd < eff_thresh_m
                else:
                    spd    = _calc_speed(prev_p, p)
                    is_slow = spd < slow_speed_thresh

                near_net = cp is not None and (
                    abs(cp[1] - 11.885) < (net_reversal_dist_m * 1.5 if cp[1] > 11.885 else net_reversal_dist_m)
                )

                if not is_slow:
                    consec_slow = 0
                else:
                    consec_slow += 1
                    if consec_slow == slow_frames_thresh:
                        sf = i - slow_frames_thresh + 1
                        if near_net:
                            net_candidates.append(sf)
                        else:
                            slow_candidates.append(sf)
            else:
                consec_slow = 0
            prev_p  = p
            prev_cp = cp

        # 仅网内慢速才触发回合结束（普通慢速不计）
        net_filtered = []
        for sf in net_candidates:
            overlap = False
            for d in range(-slow_frames_thresh, slow_frames_thresh):
                if (sf + d) in bounce_set or (sf + d) in hit_set:
                    overlap = True
                    break
            if not overlap:
                net_filtered.append(sf)

        # ── 触网检测 ──────────────────────────────────────────────────
        if detect_net_reversal and net_use_reversal:
            # 方向反转 + 能量衰减模式（--net 模式）
            NET_ZONE    = min(net_reversal_dist_m, 0.8)
            MIN_VY_PRE  = 0.12
            MAX_E_RATIO = 0.45
            court_pts_r = []
            for p in pos_raw:
                if p is not None:
                    cp = court.pixel_to_court(p[0], p[1])
                    court_pts_r.append(cp)
                else:
                    court_pts_r.append(None)
            W_net = max(net_reversal_frames, 3)
            for i in range(W_net, total - W_net):
                if court_pts_r[i] is None:
                    continue
                cy = court_pts_r[i][1]
                if abs(cy - 11.885) > NET_ZONE:
                    continue
                pre_v = [court_pts_r[j][1] - court_pts_r[j-1][1]
                         for j in range(i-W_net, i)
                         if court_pts_r[j] is not None and court_pts_r[j-1] is not None]
                post_v = [court_pts_r[j][1] - court_pts_r[j-1][1]
                          for j in range(i+1, i+W_net+1)
                          if j < total and court_pts_r[j] is not None and court_pts_r[j-1] is not None]
                if len(pre_v) < W_net//2 or len(post_v) < W_net//2:
                    continue
                vy_pre  = sum(pre_v)  / len(pre_v)
                vy_post = sum(post_v) / len(post_v)
                if vy_pre * vy_post >= 0 or abs(vy_pre) < MIN_VY_PRE:
                    continue
                if abs(vy_post) / (abs(vy_pre) + 1e-6) > MAX_E_RATIO:
                    continue
                event_frames.append((i, 'net_reversal'))
            net_cnt = sum(1 for _, r in event_frames if r == 'net_reversal')
            if net_cnt > 0:
                print(f'[Segmenter] 触网反转触发: {net_cnt} 次')
        elif detect_net_reversal:
            # 默认模式：慢速 + 网范围内
            for nf in net_filtered:
                event_frames.append((nf, 'net_reversal'))
            net_cnt = len(net_filtered)
            if net_cnt > 0:
                print(f'[Segmenter] 触网慢速触发: {net_cnt} 次')
        else:
            # 关闭触网检测 → 网内慢速归入普通 slow
            for nf in net_filtered:
                event_frames.append((nf, 'slow'))

    # ── 合并无球场触发点 ─────────────────────────────────────────
    event_frames.extend(no_court_triggers)

    # ── 按帧号排序 + 分类型去重 ─────────────────────────────────
    # 根源：全局 30 帧去重对触网来回多次触发无效。
    # 修正：每种事件类型独立维护冷却期：
    #   net_reversal → fps×2（≈2s）：同一触网区域来回触发须间隔 2s 以上
    #   slow         → fps×1（≈1s）：连续慢速只触发一次
    #   out / other  → 30 帧（出界检测本身已有 out_frames_thresh 内置缓冲）
    COOLDOWNS = {
        'net_reversal': max(30, int(fps * 2.0)),
        'slow':         max(30, int(fps * 1.0)),
    }
    DEFAULT_COOLDOWN = 30

    event_frames.sort(key=lambda x: x[0])
    filtered     = []
    last_ef_type = {}   # {reason: last_triggered_frame}
    for ef, reason in event_frames:
        cooldown = COOLDOWNS.get(reason, DEFAULT_COOLDOWN)
        last_ef  = last_ef_type.get(reason, -9999)
        if ef - last_ef > cooldown:
            filtered.append((ef, reason))
            last_ef_type[reason] = ef

    out_cnt  = sum(1 for _, r in filtered if 'out' in r)
    slow_cnt = sum(1 for _, r in filtered if r == 'slow')
    net_cnt  = sum(1 for _, r in filtered if r == 'net_reversal')
    print(f'[Segmenter] 触发事件: 出界={out_cnt}  慢速={slow_cnt}  '
          f'触网反转={net_cnt}  合计={len(filtered)}')

    if not filtered:
        print('[Segmenter] 未检测到任何回合结束事件，可能原因：')
        print('  1. 球场标定不准（重跑加 --recalib）')
        print(f'  2. --margin 太小（当前 {margin}m），尝试调大')
        print(f'  3. --out_sec 太大（当前 {out_frames_thresh} 帧），尝试调小')
        return []

    # ── 聚合成回合 ────────────────────────────────────────────────
    rallies, prev_end = [], 0
    for ef, reason in filtered:
        s = prev_end
        # no_court = 场景切换/广告，直接在触发帧截断，不加 buf_after 缓冲
        # 其他事件（出界/慢速/触网）加缓冲以保留结束动作
        if reason == 'no_court':
            e = min(total - 1, ef - 1)
        else:
            e = min(total - 1, ef + af_fr)
        if e - s >= min_fr:
            rallies.append((s, e))
            print(f'  回合{len(rallies):03d}: 帧{s}~{e}  '
                  f'({s/fps:.1f}s~{e/fps:.1f}s)  [{reason}]')
        else:
            print(f'  跳过过短片段({reason}): {(e-s)/fps:.1f}s < {min_sec}s')
        prev_end = e + 1

    print(f'[Segmenter] 共 {len(rallies)} 个回合')
    return rallies


# ══════════════════════════════════════════════════════════════════
#  7. 视频切割输出
# ══════════════════════════════════════════════════════════════════

def cut_video(video: str, rallies: list, outdir: str, fps: float,
              positions: list = None, court=None,
              slow_speed_thresh: float = 8.0, slow_frames_thresh: int = 9,
              trail_len: int = 20):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    print(f'[Cut] 开始标注切割 {len(rallies)} 个回合 → {outdir}')

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        print('[Cut] 无法打开视频')
        return

    # 修复：在进入循环前保存视频宽高，防止被内部变量覆盖
    vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    for i, (s, e) in enumerate(rallies):
        out_path = os.path.join(outdir, f'rally_{i+1:03d}.mp4')
        raw_path = out_path.replace('.mp4', '_raw.mp4')
        vw = cv2.VideoWriter(raw_path, fourcc, fps, (vid_w, vid_h))
        n_frames = e - s + 1

        # ── Step A：检测落点（结果用于慢速门控，不再做视觉显示）────
        # 球落地时有瞬时减速，若不排除这几帧，拖尾会错误变紫（误判慢速）。
        # predict_stream 里已用 ball_near_bounce 做同样的门控，此处对齐。
        bounce_frames = set()
        if positions and court is not None and hasattr(court, 'H') and court.H is not None:
            cx_list_cut = []
            cy_list_cut = []
            for j in range(n_frames):
                idx = s + j
                p_b = positions[idx] if idx < len(positions) else None
                if p_b is not None:
                    cp = court.pixel_to_court(p_b[0], p_b[1])
                    cx_list_cut.append(cp[0] if cp else None)
                    cy_list_cut.append(cp[1] if cp else None)
                else:
                    cx_list_cut.append(None)
                    cy_list_cut.append(None)
            bounce_frames = detect_bounces(
                cy_list_cut, fps,
                cx_list=cx_list_cut,
                W=max(3, int(fps * 0.1)),
                min_speed=0.04,
                min_gap_frames=max(10, int(fps * 0.3)),
            )

        # ── Step B：预计算该回合球状态（慢速 / 出界）────────────────
        # bounce_frames 门控：落点前后 BOUNCE_GATE 帧内不计入慢速
        BOUNCE_GATE = max(5, int(fps * 0.15))
        is_slow_arr = [False] * n_frames
        is_out_arr  = [False] * n_frames
        consec_slow = 0
        prev_p      = None
        for j in range(n_frames):
            idx = s + j
            p   = positions[idx] if positions and idx < len(positions) else None
            if p is not None and court is not None:
                is_out_arr[j] = court.is_out_px(p[0], p[1])
                if prev_p is not None:
                    near_bounce = any(abs(j - bf) <= BOUNCE_GATE
                                      for bf in bounce_frames)
                    spd = np.hypot(p[0] - prev_p[0], p[1] - prev_p[1])
                    if near_bounce or spd >= slow_speed_thresh or slow_speed_thresh <= 0:
                        consec_slow = 0
                    else:
                        consec_slow += 1
                    is_slow_arr[j] = consec_slow >= slow_frames_thresh
            prev_p = p

        # ── 逐帧标注写出 ──────────────────────────────────────────
        cap.set(cv2.CAP_PROP_POS_FRAMES, s)
        for j in range(n_frames):
            ret, frame = cap.read()
            if not ret:
                break
            out = frame.copy()
            p = positions[s + j] if positions and s + j < len(positions) else None

            # 轨迹拖尾（绿→黄渐变 / 紫慢速 / 红出界）
            trail_start = max(0, j - trail_len)
            for tj in range(trail_start, j):
                tp = positions[s + tj] if positions and s + tj < len(positions) else None
                if tp is None:
                    continue
                alpha = (tj - trail_start + 1) / (j - trail_start + 1)
                if is_out_arr[tj]:
                    color_t = (0, 0, 255)
                elif is_slow_arr[tj]:
                    color_t = (255, 0, 255)
                else:
                    r = int(255 * alpha)
                    g = int(255 * (1 - alpha * 0.5))
                    color_t = (0, g, r)
                radius = max(2, int(4 * alpha))
                cv2.circle(out, (int(tp[0]), int(tp[1])), radius, color_t, -1)

            # 当前球位置（绿点 + 白圈）
            if p is not None:
                bx, by = int(p[0]), int(p[1])
                cv2.circle(out, (bx, by), 6, (0, 255, 0), -1)
                cv2.circle(out, (bx, by), 9, (255, 255, 255), 1)

            vw.write(out)

        vw.release()

        # ffmpeg 重编码为 H.264，确保浏览器可播放
        ffmpeg_exe = get_ffmpeg_exe()
        if ffmpeg_exe:
            try:
                subprocess.run([
                    ffmpeg_exe, '-y', '-i', raw_path,
                    '-c:v', 'libx264', '-preset', 'fast',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    out_path
                ], capture_output=True, check=True)
                os.unlink(raw_path)
            except Exception as exc:
                print(f'[Cut] H.264 重编码失败，保留原始 mp4: {exc}')
                os.replace(raw_path, out_path)
        else:
            print('[Cut] 未找到 ffmpeg，输出视频可能无法在浏览器播放。请安装 ffmpeg 或 imageio-ffmpeg。')
            os.replace(raw_path, out_path)

        # 提取第一帧作为缩略图
        thumb_path = out_path.replace('.mp4', '.jpg')
        try:
            if not ffmpeg_exe:
                raise RuntimeError('ffmpeg not found')
            subprocess.run([
                ffmpeg_exe, '-y', '-i', out_path,
                '-vframes', '1', '-q:v', '2', thumb_path
            ], capture_output=True, check=True)
        except Exception:
            thumb_cap = cv2.VideoCapture(out_path)
            try:
                ret, thumb = thumb_cap.read()
                if ret:
                    cv2.imwrite(thumb_path, thumb)
            finally:
                thumb_cap.release()

        ss = s / fps
        print(f'  ✅ rally_{i+1:03d}.mp4  {ss:.1f}s~{ss + (e-s)/fps:.1f}s  ({n_frames}帧)')

    cap.release()

    csv_path = os.path.join(outdir, 'timestamps.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['编号', '起始帧', '结束帧', '起始秒', '结束秒'])
        for i, (s, e) in enumerate(rallies):
            w.writerow([i + 1, s, e, f'{s/fps:.3f}', f'{e/fps:.3f}'])
    print(f'  📄 时间戳已保存: {csv_path}')


# ══════════════════════════════════════════════════════════════════
#  8. 主流程
# ══════════════════════════════════════════════════════════════════

def main():
    pa = argparse.ArgumentParser(description='网球回合自动切割')
    pa.add_argument('--video',          required=True,
                    help='输入视频路径')
    pa.add_argument('--output',         default='output_rallies',
                    help='输出目录（默认 output_rallies）')
    pa.add_argument('--ball_weights',   default='weights/tennisball.pt',
                    help='YOLOv8 网球检测权重路径（默认 weights/tennisball.pt）')
    pa.add_argument('--court_weights',  default='weights/court_detector.pth',
                    help='球场检测权重路径（可选）')
    pa.add_argument('--calib',          default='court_calib.json',
                    help='球场标定文件（自动保存/加载）')
    pa.add_argument('--recalib',        action='store_true',
                    help='强制重新标定球场')
    pa.add_argument('--device',         default='auto',
                    choices=['auto', 'cuda', 'cpu'])
    pa.add_argument('--margin',         type=float, default=0.0,
                    help='出界判断容差（米），默认 0.0（红线与白线重合）')
    pa.add_argument('--min_rally_sec',  type=float, default=5.0,
                    help='最短回合时长（秒），默认 5.0')
    pa.add_argument('--buf_after',      type=float, default=2.5,
                    help='出界后保留时长（秒），默认 2.5')
    pa.add_argument('--out_sec',        type=float, default=0.7,
                    help='连续出界持续时间（秒），默认 0.7s')
    pa.add_argument('--court_conf',     type=float, default=0.3,
                    help='球场关键点置信度阈值，默认 0.3')
    pa.add_argument('--bottom_margin',  type=float, default=1,
                    help='近端底线额外扩大范围（米），默认 1')
    pa.add_argument('--slow_speed',     type=float, default=3,
                    help='慢速球速度阈值：有球场标定时为 m/s，否则为像素/帧，默认 0.8')
    pa.add_argument('--slow_sec',       type=float, default=0.3,
                    help='慢速球触发回合结束的持续时间（秒），默认 0.3')
    pa.add_argument('--no-slow',        action='store_true',
                    help='关闭慢速球检测（默认开启）')
    pa.add_argument('--person_weights', default='weights/yolov8n.pt',
                    help='人员检测模型权重（如 weights/yolov8n.pt），设为空字符串则关闭')
    pa.add_argument('--person_conf',    type=float, default=0.5,
                    help='人员检测置信度阈值，默认 0.5')
    pa.add_argument('--net',            action='store_true',
                    help='使用方向反转+能量衰减模式检测触网（否则用慢速+5m）')
    pa.add_argument('--no-net-reversal', action='store_true',
                    help='关闭球网附近速度方向反转检测（默认开启）')
    pa.add_argument('--net_reversal_dist', type=float, default=4,
                    help='球网附近检测范围（米），默认 3.0')
    pa.add_argument('--net_reversal_frames', type=int, default=3,
                    help='速度方向比较的间隔帧数，默认 3')
    pa.add_argument('--viz',            default='debug.mp4',
                    help='可视化视频输出路径，如 debug.mp4（不设则不输出）')
    args = pa.parse_args()

    print('\n' + '='*55)
    print('  网球回合自动切割')
    print('='*55)

    # ── 读取视频信息 ──────────────────────────────────────────────
    cap   = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f'[错误] 无法打开视频: {args.video}')
        return
    fps   = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H_v   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f'\n视频信息: {W}×{H_v} @ {fps:.1f}fps  共 {total} 帧 ({total/fps:.0f}s)')

    # ── Step 1: 球场标定 ─────────────────────────────────────────
    print('\n[Step 1] 球场标定')
    court = CourtDetector(args.court_weights, args.device)

    if not args.recalib and os.path.exists(args.calib):
        court.load(args.calib)
    else:
        seek = min(90, total // 10)
        cap.set(cv2.CAP_PROP_POS_FRAMES, seek)
        ret, frame = cap.read()
        if not ret:
            print('[错误] 无法读取标定帧')
            cap.release()
            return
        if not court.calibrate(frame):
            print('[错误] 球场标定失败，退出')
            cap.release()
            return
        court.save(args.calib)

    # ── Step 2+3: 流式读帧 + 球追踪 ──────────────────────────────
    cap.release()
    print(f'\n[Step 2+3] 流式读帧 + YOLOv8 球追踪')
    try:
        tracker = BallTracker(args.ball_weights, args.device,
                              person_weights=args.person_weights,
                              person_conf=args.person_conf)
    except FileNotFoundError as e:
        print(f'[错误] {e}')
        return
    viz_path = args.viz
    court.set_margin(args.margin)
    if args.bottom_margin > 0:
        court.set_bottom_margin(args.bottom_margin)
        print(f'  近端底线额外扩大: {args.bottom_margin}m')
    court_net  = court.model if hasattr(court, 'model') and court.model is not None else None
    out_frames = max(3, int(args.out_sec * fps))
    print(f'  出界判定: 连续 {out_frames} 帧 ({args.out_sec}s @ {fps:.1f}fps)')
    slow_frames = max(1, int(args.slow_sec * fps)) if not getattr(args, 'no_slow', False) else 0
    if not getattr(args, 'no_slow', False):
        print(f'  慢速球判定: 速度<{args.slow_speed}px/帧  '
              f'持续 {slow_frames} 帧 ({args.slow_sec}s)')
    positions, court_visible = tracker.predict_stream(
        args.video, W, H_v, total,
        court=court,
        viz_path=viz_path,
        court_net_model=court_net,
        court_conf_thresh=args.court_conf,
        out_frames_thresh=out_frames,
        slow_speed_thresh=args.slow_speed if not getattr(args, 'no_slow', False) else 0,
        slow_frames_thresh=slow_frames,
        net_reversal_dist_m=args.net_reversal_dist,
        person_conf=args.person_conf,
    )

    # ── Step 4: 回合边界检测 ─────────────────────────────────────
    print('\n[Step 4] 出界检测 + 回合边界')
    no_net = getattr(args, 'no_net_reversal', False)
    if not no_net:
        print(f'  球网方向反转检测: 距离≤{args.net_reversal_dist}m  '
              f'间隔{args.net_reversal_frames}帧')
    rallies = detect_rallies(
        positions, court, fps,
        court_visible=court_visible,
        margin=args.margin,
        min_sec=args.min_rally_sec,
        buf_after_sec=args.buf_after,
        out_frames_thresh=out_frames,
        slow_speed_thresh=args.slow_speed if not getattr(args, 'no_slow', False) else 0,
        slow_frames_thresh=slow_frames,
        detect_net_reversal=not no_net,
        net_reversal_dist_m=args.net_reversal_dist,
        net_reversal_frames=args.net_reversal_frames,
        net_use_reversal=args.net,
    )
    if not rallies:
        return

    # ── Step 5: 切割输出 ─────────────────────────────────────────
    print(f'\n[Step 5] 切割视频')
    cut_video(args.video, rallies, args.output, fps,
              positions=positions, court=court,
              slow_speed_thresh=args.slow_speed if not getattr(args, 'no_slow', False) else 0,
              slow_frames_thresh=slow_frames)

    print(f'\n✅ 全部完成！输出目录: {args.output}')


def run_cut_pipeline(video_path: str, output_dir: str = 'output_rallies',
                     ball_weights: str = 'weights/tennisball.pt',
                     court_weights: str = 'weights/court_detector.pth',
                     calib_path: str = 'court_calib.json',
                     device: str = 'auto',
                     margin: float = 0.0,
                     bottom_margin: float = 1.0,
                     min_rally_sec: float = 5.0,
                     buf_after: float = 2.5,
                     out_sec: float = 0.7,
                     court_conf: float = 0.3,
                     slow_speed: float = 3.0,
                     slow_sec: float = 0.3,
                     no_slow: bool = False,
                     person_weights: str = 'weights/yolov8n.pt',
                     person_conf: float = 0.5,
                     net: bool = False,
                     no_net_reversal: bool = False,
                     net_reversal_dist: float = 4.0,
                     net_reversal_frames: int = 3,
                     viz: str = '',
                     recalib: bool = False,
                     calibration_points: list = None,
                     allow_manual_calibration: bool = True) -> list:
    """
    程序化调用切割管线，返回产出视频路径列表。
    等价于 CLI 调用 `python main.py --video xxx`。
    """
    import sys
    from argparse import Namespace

    class DummyArgs:
        pass

    a = DummyArgs()
    a.video = video_path
    a.output = output_dir
    a.ball_weights = ball_weights
    a.court_weights = court_weights
    a.calib = calib_path
    a.device = resolve_torch_device(device)
    a.margin = margin
    a.bottom_margin = bottom_margin
    a.min_rally_sec = min_rally_sec
    a.buf_after = buf_after
    a.out_sec = out_sec
    a.court_conf = court_conf
    a.slow_speed = slow_speed
    a.slow_sec = slow_sec
    a.no_slow = no_slow
    a.person_weights = person_weights
    a.person_conf = person_conf
    a.net = net
    a.no_net_reversal = no_net_reversal
    a.net_reversal_dist = net_reversal_dist
    a.net_reversal_frames = net_reversal_frames
    a.viz = viz
    a.recalib = recalib
    a.calibration_points = calibration_points
    a.allow_manual_calibration = allow_manual_calibration

    args = a

    print('\n' + '=' * 55)
    print('  网球回合自动切割（API 模式）')
    print('=' * 55)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise RuntimeError(f'无法打开视频: {args.video}')
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H_v = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f'\n视频信息: {W}×{H_v} @ {fps:.1f}fps  共 {total} 帧 ({total / fps:.0f}s)')

    print('\n[Step 1] 球场标定')
    court = CourtDetector(args.court_weights, args.device)

    if args.calibration_points:
        if not court.set_manual_corners(args.calibration_points):
            cap.release()
            raise RuntimeError('前端球场标定点无效')
        court.save(args.calib)
    elif not args.recalib and os.path.exists(args.calib):
        court.load(args.calib)
    else:
        seek = min(90, total // 10)
        cap.set(cv2.CAP_PROP_POS_FRAMES, seek)
        ret, frame = cap.read()
        if not ret:
            cap.release()
            raise RuntimeError('无法读取标定帧')
        if not court.calibrate(frame, allow_manual=args.allow_manual_calibration):
            cap.release()
            raise RuntimeError('NEED_CALIBRATION: 请在前端依次标记球场四个角点')
        court.save(args.calib)

    cap.release()
    print(f'\n[Step 2+3] 流式读帧 + YOLOv8 球追踪')
    try:
        tracker = BallTracker(args.ball_weights, args.device,
                              person_weights=args.person_weights,
                              person_conf=args.person_conf)
    except FileNotFoundError as e:
        raise RuntimeError(str(e))
    viz_path = args.viz if args.viz else None
    court.set_margin(args.margin)
    if args.bottom_margin > 0:
        court.set_bottom_margin(args.bottom_margin)
        print(f'  近端底线额外扩大: {args.bottom_margin}m')

    court_net = court.model if hasattr(court, 'model') and court.model is not None else None
    out_frames = max(3, int(args.out_sec * fps))
    print(f'  出界判定: 连续 {out_frames} 帧 ({args.out_sec}s @ {fps:.1f}fps)')
    slow_frames = max(1, int(args.slow_sec * fps)) if not getattr(args, 'no_slow', False) else 0
    if not getattr(args, 'no_slow', False):
        print(f'  慢速球判定: 速度<{args.slow_speed}  '
              f'持续 {slow_frames} 帧 ({args.slow_sec}s)')

    person_model = tracker.person_model if hasattr(tracker, 'person_model') else None
    positions, court_visible = tracker.predict_stream(
        args.video, W, H_v, total,
        court=court,
        viz_path=viz_path,
        court_net_model=court_net,
        court_conf_thresh=args.court_conf,
        out_frames_thresh=out_frames,
        slow_speed_thresh=args.slow_speed if not getattr(args, 'no_slow', False) else 0,
        slow_frames_thresh=slow_frames,
        net_reversal_dist_m=args.net_reversal_dist,
        person_model=person_model,
        person_conf=args.person_conf,
    )

    print('\n[Step 4] 出界检测 + 回合边界')
    no_net = getattr(args, 'no_net_reversal', False)
    if not no_net:
        print(f'  触网检测: 距离≤{args.net_reversal_dist}m  '
              f'间隔{args.net_reversal_frames}帧')
    rallies = detect_rallies(
        positions, court, fps,
        court_visible=court_visible,
        margin=args.margin,
        min_sec=args.min_rally_sec,
        buf_after_sec=args.buf_after,
        out_frames_thresh=out_frames,
        slow_speed_thresh=args.slow_speed if not getattr(args, 'no_slow', False) else 0,
        slow_frames_thresh=slow_frames,
        detect_net_reversal=not no_net,
        net_reversal_dist_m=args.net_reversal_dist,
        net_reversal_frames=args.net_reversal_frames,
        net_use_reversal=args.net,
    )
    if not rallies:
        return []

    print(f'\n[Step 5] 切割视频')
    cut_video(args.video, rallies, args.output, fps,
              positions=positions, court=court,
              slow_speed_thresh=args.slow_speed if not getattr(args, 'no_slow', False) else 0,
              slow_frames_thresh=slow_frames)

    out_files = sorted(
        str(p) for p in Path(args.output).glob('rally_*.mp4')
    )
    print(f'\n✅ 全部完成！共 {len(out_files)} 个回合')
    return out_files


if __name__ == '__main__':
    main()
