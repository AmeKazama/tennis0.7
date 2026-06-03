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
                    _summary_holder["data"] = {
                        "num_segments": len(shot_counter.results),
                        "num_frames": total_frames,
                        "fps": fps,
                        "duration": total_frames / fps,
                        "shots": shot_counter.results
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

                    coach_advice = None
                    try:
                        coach_advice = await self.doubao_service.get_coach_advice(report)
                        print(f"[服务] 豆包建议(片段{res['shot_id']}): {coach_advice}")
                    except Exception as e:
                        print(f"[服务] 豆包调用失败: {e}")
                        coach_advice = "建议生成中..."

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
                                "top_issues": res["issues"],
                                "phase_dtw": res.get("phase_dtw"),
                                "user_annotation": res.get("user_annotation")
                            },
                            "coach_advice": coach_advice
                        }
                    }

            thread.join(timeout=5)

            # 推送 summary
            if "data" in _summary_holder:
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

