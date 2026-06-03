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
        self._tasks[task_id] = {"status": "running", "progress": 0}
        self._results[task_id] = None

        loop = asyncio.get_event_loop()

        def run():
            temp_video = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_bytes)
                    temp_video = tmp.name

                logger.info(f"[切割 {task_id[:8]}] 视频已保存到: {temp_video}")

                out_dir_abs = os.path.abspath(output_dir)
                calib_abs = os.path.abspath(calib_path) if os.path.exists(calib_path) else calib_path

                self._tasks[task_id] = {"status": "running", "progress": 30}

                files = run_cut_pipeline(
                    video_path=temp_video,
                    output_dir=out_dir_abs,
                    calib_path=calib_abs,
                    slow_speed=slow_speed,
                    no_slow=no_slow,
                    no_net_reversal=no_net,
                    **kwargs,
                )

                self._tasks[task_id] = {"status": "running", "progress": 90}
                self._results[task_id] = {
                    "files": [f.replace("\\", "/") for f in files],
                    "count": len(files),
                }
                self._tasks[task_id] = {"status": "done", "progress": 100}
                logger.info(f"[切割 {task_id[:8]}] 完成，共 {len(files)} 个回合")

            except Exception as e:
                logger.error(f"[切割 {task_id[:8]}] 失败: {e}", exc_info=True)
                self._tasks[task_id] = {"status": "error", "error": str(e)}
            finally:
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
