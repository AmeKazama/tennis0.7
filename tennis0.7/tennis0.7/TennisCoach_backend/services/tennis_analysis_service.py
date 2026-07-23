"""
网球视频分析服务 - FastAPI 集成版
提供异步生成器接口供 main.py 调用
支持 YOLO 辅助的精确击球帧检测
"""

import os
import sys
import json
import tempfile
import asyncio
import uuid
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional

# 导入核心分析功能
from services.tennis_final import (
    run_analysis,
    DoubaoService,
    format_analysis_report,
    format_enhanced_analysis_report,
    YoloBallRacketDetector,
    HAS_YOLO,
    keras,
)


POSE_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
)


class TennisAnalysisService:
    """网球视频分析服务"""

    def __init__(self, model_path: str = "tennis_rnn_converted.keras",
                 yolo_weights: Optional[str] = "yolov8s.pt",
                 use_yolo: bool = True):
        """
        初始化服务

        Args:
            model_path: RNN 模型文件路径
            yolo_weights: YOLO 模型权重路径（可选）
            use_yolo: 是否使用 YOLO 辅助检测
        """
        self.model_path = model_path
        self.yolo_weights = yolo_weights
        self.use_yolo = use_yolo and HAS_YOLO and yolo_weights and os.path.exists(yolo_weights)

        self.model = None
        self.doubao_service = None
        self.yolo_detector = None

    async def initialize(self):
        """异步初始化（加载模型和豆包服务）"""
        if self.model is None:
            print(f"[服务] 加载 RNN 模型: {self.model_path}")
            self.model = keras.saving.load_model(self.model_path)
            print(f"[服务] RNN 模型加载完成")

        if self.doubao_service is None:
            self.doubao_service = DoubaoService()
            print(f"[服务] 豆包服务已初始化")

        if self.use_yolo and self.yolo_detector is None:
            try:
                self.yolo_detector = YoloBallRacketDetector(
                    weights_path=self.yolo_weights,
                    conf=0.20,
                    device=None  # 自动选择
                )
                print(f"[服务] YOLO 检测器已初始化")
            except Exception as e:
                print(f"[服务] YOLO 初始化失败，降级到纯关键点检测: {e}")
                self.yolo_detector = None

    def _load_standard_annotation(self, standard_file: Optional[str]) -> Optional[Dict[str, Any]]:
        """读取最佳匹配标准动作的 final.json，返回 segment_range/fps 等播放区间信息。"""
        if not standard_file:
            return None
        json_path = Path(standard_file)
        if not json_path.is_absolute():
            json_path = Path(__file__).resolve().parents[3] / standard_file
        if not json_path.exists():
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ann = data[0] if isinstance(data, list) and data else data
            if not isinstance(ann, dict):
                return None
            return {
                "name": ann.get("name"),
                "shot_type": ann.get("shot_type"),
                "segment_range": ann.get("segment_range"),
                "impact_frame": ann.get("impact_frame"),
                "phase_boundaries": ann.get("phase_boundaries"),
                "fps": ann.get("fps"),
                "total_frames": ann.get("total_frames"),
            }
        except Exception as e:
            print(f"[服务] 标准动作标注读取失败: {e}")
            return None
    def _find_pose_landmarker_model(self) -> Optional[Path]:
        """Find the MediaPipe Tasks pose landmarker model file."""
        env_path = os.getenv("MEDIAPIPE_POSE_MODEL")
        candidates = []
        if env_path:
            candidates.append(Path(env_path))

        base_dir = Path(__file__).resolve().parent.parent
        candidates.extend([
            base_dir / "models" / "pose_landmarker_lite.task",
            base_dir / "models" / "pose_landmarker_full.task",
            base_dir / "weights" / "pose_landmarker_lite.task",
            base_dir / "weights" / "pose_landmarker_full.task",
            base_dir / "services" / "pose_landmarker_lite.task",
            base_dir / "pose_landmarker_lite.task",
        ])

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _draw_tasks_pose_landmarks(self, frame, landmarks, width: int, height: int):
        """Draw MediaPipe Tasks normalized pose landmarks on an OpenCV frame."""
        import cv2

        points = []
        for landmark in landmarks:
            visibility = getattr(landmark, "visibility", 1.0)
            presence = getattr(landmark, "presence", 1.0)
            if visibility < 0.35 or presence < 0.35:
                points.append(None)
                continue

            x = int(landmark.x * width)
            y = int(landmark.y * height)
            if x < 0 or y < 0 or x >= width or y >= height:
                points.append(None)
                continue
            points.append((x, y))

        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx >= len(points) or end_idx >= len(points):
                continue
            start = points[start_idx]
            end = points[end_idx]
            if start is None or end is None:
                continue
            cv2.line(frame, start, end, (80, 255, 170), 3)

        for point in points:
            if point is not None:
                cv2.circle(frame, point, 4, (120, 255, 220), -1)

    def _create_video_clip(
        self,
        video_path: str,
        frame_start: int,
        frame_end: int,
        prefix: str,
    ) -> Optional[str]:
        """按分析帧范围生成 H.264 片段，确保浏览器和手机端可以直接播放。"""
        import cv2
        import subprocess
        import imageio_ffmpeg

        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            start = max(1, int(frame_start))
            end = max(start, int(frame_end))
            if total_frames > 0:
                end = min(end, total_frames)

            fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
            start_seconds = max(0.0, (start - 1) / fps)
            duration_seconds = max(1.0 / fps, (end - start + 1) / fps)
            cap.release()
            cap = None

            output_dir = Path("uploads") / "action_analysis"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_name = f"{prefix}_{uuid.uuid4().hex}.mp4"
            output_path = output_dir / output_name

            command = [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-y",
                "-ss", f"{start_seconds:.6f}",
                "-i", str(video_path),
                "-t", f"{duration_seconds:.6f}",
                "-map", "0:v:0",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-avoid_negative_ts", "make_zero",
                str(output_path),
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=max(60, int(duration_seconds * 8)),
                check=False,
            )
            if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
                error_tail = (result.stderr or "")[-500:]
                print(f"[服务] FFmpeg 切片失败: {error_tail}")
                return None

            return f"/uploads/action_analysis/{output_name}"
        except Exception as e:
            print(f"[服务] 视频片段生成失败: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    def _create_video_poster(self, video_url: Optional[str]) -> Optional[str]:
        """提取视频第一帧为 JPEG，供前端在播放前显示封面。"""
        if not video_url:
            return None

        import cv2

        video_path = Path(video_url.lstrip("/"))
        if not video_path.exists():
            return None

        poster_path = video_path.with_suffix(".jpg")
        cap = None
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return None

            ok, frame = cap.read()
            if not ok or frame is None:
                return None

            encoded, buffer = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 88],
            )
            if not encoded:
                return None

            poster_path.write_bytes(buffer.tobytes())
            return f"/{poster_path.as_posix()}"
        except Exception as e:
            print(f"[服务] 视频首帧封面生成失败: {e}")
            return None
        finally:
            if cap is not None:
                cap.release()

    def _create_segment_media(self, video_path: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成单个动作对应的 H.264 原片和骨架片段。"""
        segment_id = int(analysis_result.get("shot_id") or 0)
        frame_start = analysis_result.get("frame_start")
        frame_end = analysis_result.get("frame_end")
        media = {
            "segment_video_url": None,
            "segment_pose_video_url": None,
            "segment_video_poster_url": None,
            "segment_pose_video_poster_url": None,
        }
        if frame_start is None or frame_end is None:
            return media

        raw_url = self._create_video_clip(
            video_path,
            frame_start,
            frame_end,
            f"segment_{segment_id}",
        )
        media["segment_video_url"] = raw_url
        media["segment_video_poster_url"] = self._create_video_poster(raw_url)
        if not raw_url:
            return media

        raw_path = Path(raw_url.lstrip("/"))
        if not raw_path.exists():
            return media

        pose_intermediate_url = self._create_pose_overlay_video(str(raw_path))
        if not pose_intermediate_url:
            return media

        pose_intermediate_path = Path(pose_intermediate_url.lstrip("/"))
        try:
            if pose_intermediate_path.exists():
                pose_url = self._create_video_clip(
                    str(pose_intermediate_path),
                    1,
                    2_147_483_647,
                    f"segment_pose_{segment_id}",
                )
                media["segment_pose_video_url"] = pose_url
                media["segment_pose_video_poster_url"] = self._create_video_poster(pose_url)
        finally:
            if pose_intermediate_path.exists():
                try:
                    pose_intermediate_path.unlink()
                except OSError:
                    pass

        return media

    def _create_pose_overlay_video(self, video_path: str) -> Optional[str]:
        """使用 MediaPipe 在原视频上绘制人体骨骼，并返回可被前端访问的静态 URL。"""
        cap = None
        writer = None
        pose = None

        try:
            import cv2
            import mediapipe as mp

            output_dir = Path("uploads") / "action_analysis"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_stem = f"pose_{uuid.uuid4().hex}"

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"[服务] 骨骼可视化视频生成失败: 无法打开视频 {video_path}")
                return None

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            if width <= 0 or height <= 0:
                print("[服务] 骨骼可视化视频生成失败: 视频尺寸无效")
                return None

            output_name = None
            output_path = None
            for fourcc_name, ext in [("avc1", "mp4"), ("H264", "mp4"), ("mp4v", "mp4"), ("VP80", "webm")]:
                candidate_name = f"{output_stem}.{ext}"
                candidate_path = output_dir / candidate_name
                candidate_writer = cv2.VideoWriter(
                    str(candidate_path),
                    cv2.VideoWriter_fourcc(*fourcc_name),
                    fps,
                    (width, height),
                )
                if candidate_writer.isOpened():
                    writer = candidate_writer
                    output_name = candidate_name
                    output_path = candidate_path
                    break
                candidate_writer.release()

            if writer is None or output_name is None or output_path is None:
                print("[服务] 骨骼可视化视频生成失败: 无法创建视频写入器")
                return None

            if hasattr(mp, "solutions"):
                pose_module = mp.solutions.pose
                drawing_utils = mp.solutions.drawing_utils
                landmark_spec = drawing_utils.DrawingSpec(color=(120, 255, 220), thickness=2, circle_radius=3)
                connection_spec = drawing_utils.DrawingSpec(color=(80, 255, 170), thickness=3, circle_radius=2)
                pose = pose_module.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )

                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = pose.process(rgb)
                    if result.pose_landmarks:
                        drawing_utils.draw_landmarks(
                            frame,
                            result.pose_landmarks,
                            pose_module.POSE_CONNECTIONS,
                            landmark_drawing_spec=landmark_spec,
                            connection_drawing_spec=connection_spec,
                        )

                    writer.write(frame)
            else:
                model_path = self._find_pose_landmarker_model()
                if model_path is None:
                    print(
                        "[服务] 骨骼可视化视频生成失败: 新版 mediapipe.tasks 需要 "
                        "pose_landmarker_lite.task，请放到 models/ 或设置 MEDIAPIPE_POSE_MODEL"
                    )
                    return None

                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision

                # Pass model bytes instead of a filesystem path. MediaPipe's
                # native layer can fail to open non-ASCII Windows paths.
                base_options = mp_python.BaseOptions(model_asset_buffer=model_path.read_bytes())
                options = vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.VIDEO,
                    num_poses=1,
                    min_pose_detection_confidence=0.5,
                    min_pose_presence_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                pose = vision.PoseLandmarker.create_from_options(options)

                frame_index = 0
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    timestamp_ms = int(frame_index * 1000 / fps)
                    result = pose.detect_for_video(image, timestamp_ms)
                    if result.pose_landmarks:
                        self._draw_tasks_pose_landmarks(
                            frame,
                            result.pose_landmarks[0],
                            width,
                            height,
                        )

                    writer.write(frame)
                    frame_index += 1

            print(f"[服务] 骨骼可视化视频已生成: {output_path}")
            return f"/uploads/action_analysis/{output_name}"

        except Exception as e:
            print(f"[服务] 骨骼可视化视频生成失败: {e}")
            return None

        finally:
            if pose is not None:
                pose.close()
            if cap is not None:
                cap.release()
            if writer is not None:
                writer.release()
    async def analyze_video_stream(self, video_bytes: bytes) -> AsyncGenerator[Dict[str, Any], None]:
        """
        分析视频并流式返回结果。
        核心改动：用 asyncio.Queue + threading 桥接同步 run_analysis 和异步生成器，
        每分析完一个片段立刻调豆包并 yield，无需等整个视频跑完。
        """
        import threading

        temp_video_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_bytes)
                temp_video_path = tmp.name

            print(f"[服务] 视频已保存到: {temp_video_path}")

            await self.initialize()

            class ServiceArgs:
                left_handed = False
                evaluate = None
                save = None
                skeleton_dir = "skeleton_data"
                save_video_clips = False
                f = None
                video_fps = 30.0

            args = ServiceArgs()

            # Queue 用于桥接同步线程和异步生成器
            loop = asyncio.get_event_loop()
            queue: asyncio.Queue = asyncio.Queue()

            # 每分析完一段，同步线程通过此回调放入 queue
            def on_shot_ready(analysis_result):
                asyncio.run_coroutine_threadsafe(
                    queue.put(("shot", analysis_result)), loop
                )

            # 用于存储 summary 信息
            _summary_holder = {}

            def run_in_thread():
                try:
                    shot_counter, skeleton_recorder, total_frames, fps = run_analysis(
                        temp_video_path,
                        self.model,
                        args,
                        service_mode=True,
                        on_shot_ready=on_shot_ready,
                    )
                    service_results = list(skeleton_recorder.service_results)
                    _summary_holder["data"] = {
                        "num_segments": len(service_results),
                        "num_frames": total_frames,
                        "fps": fps,
                        "duration": total_frames / fps,
                        "shots": service_results
                    }
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    asyncio.run_coroutine_threadsafe(
                        queue.put(("error", str(e))), loop
                    )
                finally:
                    # 通知异步侧视频已跑完
                    asyncio.run_coroutine_threadsafe(
                        queue.put(("done", None)), loop
                    )

            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()

            # 从 queue 取结果，边取边处理
            while True:
                msg_type, data = await queue.get()

                if msg_type == "done":
                    break

                elif msg_type == "error":
                    yield {"type": "error", "message": data}
                    break

                elif msg_type == "shot":
                    res = data
                    print(f"[服务] 处理片段 {res['shot_id']} - {res['shot_type']}")

                    # 立刻格式化并调豆包
                    report = format_enhanced_analysis_report(
                        shot_id=res["shot_id"],
                        shot_type=res["shot_type"],
                        dtw_distance=res.get("distance", 999),
                        issues=res.get("issues", []),
                        best_match_name=res.get("best_match", "unknown"),
                        phase_dtw=res.get("phase_dtw"),
                        user_annotation=res.get("user_annotation")
                    )

                    # 建议生成和片段视频生成并行执行，完成后作为同一条结果返回。
                    advice_result, media_result = await asyncio.gather(
                        self.doubao_service.get_coach_advice(report),
                        asyncio.to_thread(self._create_segment_media, temp_video_path, res),
                        return_exceptions=True,
                    )
                    if isinstance(advice_result, Exception):
                        print(f"[服务] 豆包调用失败: {advice_result}")
                        coach_advice = "建议生成中..."
                    else:
                        coach_advice = advice_result or "建议生成中..."
                        print(f"[服务] 豆包建议(片段{res['shot_id']}): {coach_advice}")

                    if isinstance(media_result, Exception):
                        print(f"[服务] 片段媒体生成失败: {media_result}")
                        media_result = {
                            "segment_video_url": None,
                            "segment_pose_video_url": None,
                            "segment_video_poster_url": None,
                            "segment_pose_video_poster_url": None,
                        }

                    phase_dtw = res.get("phase_dtw") or {}
                    standard_file = phase_dtw.get("standard_file")
                    standard_annotation = self._load_standard_annotation(standard_file)

                    yield {
                        "type": "segment",
                        "data": {
                            "segment_id": res["shot_id"],
                            "shot_type": res["shot_type"],
                            "shot_type_cn": {
                                "forehand": "正手",
                                "backhand": "反手",
                                "serve": "发球"
                            }.get(res["shot_type"], res["shot_type"]),
                            "analysis": {
                                "grade": res["grade"],
                                "distance": res["distance"],
                                "best_match": res.get("best_match"),
                                "top_issues": res["issues"],
                                "phase_dtw": phase_dtw,
                                "user_annotation": res.get("user_annotation")
                            },
                            "best_match": res.get("best_match"),
                            "standard_file": standard_file,
                            "standard_annotation": standard_annotation,
                            "frame_start": res.get("frame_start"),
                            "frame_end": res.get("frame_end"),
                            "impact_frame": res.get("impact_frame"),
                            "time_range": res.get("time_range"),
                            "impact_time": res.get("impact_time"),
                            "segment_video_url": media_result.get("segment_video_url"),
                            "segment_pose_video_url": media_result.get("segment_pose_video_url"),
                            "segment_video_poster_url": media_result.get("segment_video_poster_url"),
                            "segment_pose_video_poster_url": media_result.get("segment_pose_video_poster_url"),
                            "coach_advice": coach_advice
                        }
                    }

            thread.join(timeout=5)

            # 推送 summary；逐段媒体已经随每条 segment 返回。
            if "data" in _summary_holder:
                total_frames = int(_summary_holder["data"].get("num_frames") or 0)
                if total_frames > 0:
                    source_video_url = await asyncio.to_thread(
                        self._create_video_clip,
                        temp_video_path,
                        1,
                        total_frames,
                        "source_video",
                    )
                    if source_video_url:
                        _summary_holder["data"]["source_video_url"] = source_video_url
                        _summary_holder["data"]["source_video_poster_url"] = (
                            await asyncio.to_thread(self._create_video_poster, source_video_url)
                        )

                yield {"type": "summary", "data": _summary_holder["data"]}

        except Exception as e:
            print(f"[服务] 分析异常: {e}")
            import traceback
            traceback.print_exc()
            yield {"type": "error", "message": f"视频分析失败: {str(e)}"}

        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                    print(f"[服务] 临时文件已删除: {temp_video_path}")
                except Exception as e:
                    print(f"[服务] 临时文件删除失败: {e}")

    async def analyze_video_complete(self, video_bytes: bytes) -> Dict[str, Any]:
        """
        分析视频并返回完整结果(非流式,适合前端直接使用)

        Args:
            video_bytes: 视频文件的二进制数据

        Returns:
            包含 segments 和 summary 的完整分析结果
        """
        segments = []
        summary = None
        error = None

        try:
            async for result in self.analyze_video_stream(video_bytes):
                result_type = result.get("type")

                if result_type == "segment":
                    # 提取 data 字段作为 segment
                    segments.append(result.get("data", {}))
                elif result_type == "summary":
                    summary = result.get("data", {})
                elif result_type == "error":
                    error = result.get("message", "未知错误")
        except Exception as e:
            error = f"分析异常: {str(e)}"

        return {
            "segments": segments,
            "summary": summary,
            "error": error
        }

    async def close(self):
        """关闭服务（清理资源）"""
        if self.doubao_service:
            await self.doubao_service.close()
            print(f"[服务] 豆包服务已关闭")


# 全局服务实例
_service_instance = None


async def get_analysis_service(yolo_weights: str = "yolov8s.pt",
                               use_yolo: bool = True) -> TennisAnalysisService:
    """
    获取全局服务实例（单例模式）
    供 main.py 调用

    Args:
        yolo_weights: YOLO 权重文件路径
        use_yolo: 是否启用 YOLO 辅助检测
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = TennisAnalysisService(
            model_path="services/tennis_rnn_converted.keras",
            yolo_weights=yolo_weights,
            use_yolo=use_yolo
        )
        await _service_instance.initialize()

    return _service_instance


# 测试代码
if __name__ == "__main__":
    async def test():
        print("🚀 测试网球分析服务...")

        service = await get_analysis_service()

        # 读取测试视频
        test_video_path = "test_video.mp4"
        if not os.path.exists(test_video_path):
            print(f"❌ 测试视频不存在: {test_video_path}")
            return

        with open(test_video_path, "rb") as f:
            video_bytes = f.read()

        print(f"📹 开始分析测试视频 ({len(video_bytes)} bytes)...")

        async for result in service.analyze_video_stream(video_bytes):
            result_type = result.get("type")
            print(f"\n📦 收到结果: {result_type}")
            print(json.dumps(result, ensure_ascii=False, indent=2))

        await service.close()
        print("\n✅ 测试完成")

    asyncio.run(test())









