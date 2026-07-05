"""
回合切割服务 - FastAPI 集成版
异步封装 rally_cutter_core 的同步切割管线
"""

import os
import sys
import json
import uuid
import logging
import tempfile
import threading
import asyncio
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from services.rally_cutter_core import run_cut_pipeline

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


class RallyCutService:
    """回合切割服务"""

    def __init__(self):
        self._tasks: dict = {}
        self._results: dict = {}

    async def submit_cut(self, video_bytes: bytes,
                         output_dir: str = "output_rallies",
                         calib_path: str = "court_calib.json",
                         calibration_points: Optional[list] = None,
                         slow_speed: float = 3.0,
                         no_slow: bool = False,
                         no_net: bool = False,
                         **kwargs) -> str:
        """
        提交切割任务，返回 task_id。

        Args:
            video_bytes: 视频文件二进制数据
            output_dir: 输出目录
            calib_path: 球场标定文件路径
            slow_speed: 慢速速度阈值
            no_slow: 关闭慢速检测
            no_net: 关闭触网检测
            **kwargs: 其他传递给 run_cut_pipeline 的参数
        """
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {"status": "running", "progress": 0, "message": "等待处理"}
        self._results[task_id] = None

        loop = asyncio.get_event_loop()

        def update_task(progress: int = None, message: str = None, status: str = "running", **extra):
            current = dict(self._tasks.get(task_id, {}))
            current["status"] = status
            if progress is not None:
                current["progress"] = progress
            if message is not None:
                current["message"] = message
            current.update(extra)
            self._tasks[task_id] = current

        def start_progress_ticker(stop_event: threading.Event):
            def tick():
                while not stop_event.wait(4):
                    info = self._tasks.get(task_id, {})
                    if info.get("status") != "running":
                        return
                    current = int(info.get("progress") or 30)
                    if current >= 85:
                        continue
                    step = 4 if current < 60 else 2
                    next_progress = min(85, current + step)
                    if next_progress < 45:
                        message = "球场标定与视频解码中"
                    elif next_progress < 75:
                        message = "YOLO 正在追踪网球，CPU 模式可能较慢"
                    else:
                        message = "正在识别回合边界并准备导出"
                    update_task(progress=next_progress, message=message)

            thread = threading.Thread(target=tick, daemon=True)
            thread.start()
            return thread

        def run():
            temp_video = None
            stop_progress = None
            ticker = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_bytes)
                    temp_video = tmp.name

                logger.info(f"[切割 {task_id[:8]}] 视频已保存到: {temp_video}")

                out_dir_abs = os.path.abspath(os.path.join(output_dir, task_id))
                os.makedirs(out_dir_abs, exist_ok=True)
                calib_abs = os.path.abspath(calib_path) if os.path.exists(calib_path) else calib_path

                update_task(progress=30, message="已上传，开始进入回合识别管线")
                stop_progress = threading.Event()
                ticker = start_progress_ticker(stop_progress)

                files = run_cut_pipeline(
                    video_path=temp_video,
                    output_dir=out_dir_abs,
                    calib_path=calib_abs,
                    calibration_points=calibration_points,
                    allow_manual_calibration=False,
                    slow_speed=slow_speed,
                    no_slow=no_slow,
                    no_net_reversal=no_net,
                    **kwargs,
                )

                if stop_progress:
                    stop_progress.set()
                if ticker:
                    ticker.join(timeout=1)

                update_task(progress=90, message="正在整理分割结果")
                output_root_abs = os.path.abspath(output_dir)
                relative_files = [
                    os.path.relpath(f, output_root_abs).replace("\\", "/")
                    for f in files
                ]
                self._results[task_id] = {
                    "files": relative_files,
                    "count": len(files),
                    "message": "" if files else "未识别到满足条件的有效回合，请检查标定点、视频时长或换一段包含完整回合的视频。",
                }
                update_task(progress=100, message="分割完成", status="done")
                logger.info(f"[切割 {task_id[:8]}] 完成，共 {len(files)} 个回合")

            except Exception as e:
                logger.error(f"[切割 {task_id[:8]}] 失败: {e}", exc_info=True)
                update_task(progress=0, message="分割失败", status="error", error=str(e))
            finally:
                if stop_progress:
                    stop_progress.set()
                if temp_video and os.path.exists(temp_video):
                    try:
                        os.unlink(temp_video)
                    except Exception:
                        pass

        asyncio.run_coroutine_threadsafe(
            asyncio.to_thread(run), loop
        )

        return task_id

    def get_status(self, task_id: str) -> dict:
        """获取任务状态"""
        if task_id not in self._tasks:
            return {"status": "not_found"}
        info = dict(self._tasks[task_id])
        if task_id in self._results and self._results[task_id] is not None:
            info["result"] = self._results[task_id]
        return info


# 全局单例
_service = RallyCutService()


async def get_rally_cut_service() -> RallyCutService:
    return _service
