"""
回合切割 API 路由
接受前端视频 → 后台切割 → 返回片段文件列表
"""

import json
import logging
import asyncio
import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import JSONResponse

from services.rally_cut_service import get_rally_cut_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rally", tags=["rally"])


@router.post("/cut/submit")
async def submit_cut(
    file: UploadFile = File(...),
    manual_points: str | None = Form(None),
    slow_speed: float = Query(3.0, description="慢速速度阈值"),
    no_slow: bool = Query(False, description="关闭慢速检测"),
    no_net: bool = Query(False, description="关闭触网检测"),
    net_reversal_dist: float = Query(4.0, description="触网检测范围（米）"),
    min_rally_sec: float = Query(1.0, description="最短回合时长（秒）"),
):
    """
    提交视频切割任务，立即返回 task_id。
    处理完成后通过 /api/rally/cut/status/{task_id} 获取结果。
    """
    try:
        video_bytes = await file.read()
        if not video_bytes:
            raise HTTPException(status_code=400, detail="文件为空")

        logger.info(f"[切割提交] 文件={file.filename}, 大小={len(video_bytes)} bytes")

        calibration_points = None
        if manual_points:
            try:
                calibration_points = json.loads(manual_points)
                if not isinstance(calibration_points, list) or len(calibration_points) != 4:
                    raise ValueError("manual_points must contain four points")
                for point in calibration_points:
                    if not isinstance(point, dict) or "x" not in point or "y" not in point:
                        raise ValueError("each point must include x and y")
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"标定点格式错误: {exc}") from exc

        service = await get_rally_cut_service()
        task_id = await service.submit_cut(
            video_bytes=video_bytes,
            calibration_points=calibration_points,
            slow_speed=slow_speed,
            no_slow=no_slow,
            no_net=no_net,
            net_reversal_dist=net_reversal_dist,
            min_rally_sec=min_rally_sec,
        )

        return {"task_id": task_id, "status": "submitted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[切割提交] 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cut/status/{task_id}")
async def get_cut_status(task_id: str):
    """
    查询切割任务状态和结果。

    返回:
      - status: running / done / error / not_found
      - progress: 0~100
      - result: 完成后包含 files 列表和 count
    """
    service = await get_rally_cut_service()
    info = service.get_status(task_id)

    if info["status"] == "not_found":
        raise HTTPException(status_code=404, detail="task_id 不存在")

    return info


@router.get("/cut/test")
async def test_cut(
    video_path: str = Query("E:\\Downloads\\apk_ground_truth\\test_video_5.mp4"),
    slow_speed: float = Query(5.0),
    no_net: bool = Query(True),
    net_reversal_dist: float = Query(4.0),
):
    """同步切割本地视频，直接返回结果（供模拟器前端自动调用）"""
    import os
    from services.rally_cutter_core import run_cut_pipeline

    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail=f"视频文件不存在: {video_path}")

    logger.info(f"[测试切割] {video_path}")
    loop = asyncio.get_event_loop()

    def run():
        return run_cut_pipeline(
            video_path=video_path,
            output_dir="output_rallies",
            slow_speed=slow_speed,
            no_net_reversal=no_net,
            net_reversal_dist=net_reversal_dist,
        )

    files = await loop.run_in_executor(None, run)
    files = [f.replace("\\", "/") for f in files]
    return {"status": "done", "files": files, "count": len(files)}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    单独上传视频到服务器，返回可访问的 URL。
    前端可用此 URL 进行预览播放，后续切割时可传 server_path 参数。
    """
    video_bytes = await file.read()
    if not video_bytes:
        raise HTTPException(status_code=400, detail="文件为空")

    ext = Path(file.filename or "video.mp4").suffix or ".mp4"
    filename = f"preview_{uuid.uuid4().hex}{ext}"
    save_dir = Path("uploads/videos")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    save_path.write_bytes(video_bytes)

    url = f"/uploads/videos/{filename}"
    logger.info(f"[上传预览] {file.filename} -> {save_path} ({len(video_bytes)} bytes)")
    return {"url": url, "filename": filename, "size": len(video_bytes)}


@router.get("/files")
async def list_output_files():
    """列出 output_rallies 目录中的所有切割文件"""
    out_dir = Path("output_rallies")
    if not out_dir.exists():
        return {"files": []}

    files = sorted(
        {"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime}
        for p in out_dir.glob("rally_*.mp4")
    )
    return {"files": files, "count": len(files)}
