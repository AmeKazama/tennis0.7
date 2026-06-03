import time
import asyncio
import json
import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import uuid
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from routers.diary import router as diary_router
from routers.moments import router as moments_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入服务
try:
    from services.doubao_service import get_fitness_advice, get_video_analysis_advice
    from services.tennis_analysis_service import get_analysis_service

    logger.info("[OK] 成功加载所有服务")
except ImportError as e:
    logger.error(f"[ERROR] 服务加载失败: {e}")

    # 降级处理
    async def get_fitness_advice(data):
        return "本地模拟：请注意重心稳定"

    async def get_video_analysis_advice(prompt):
        return "本地模拟：动作需要调整"

    async def get_analysis_service():
        raise RuntimeError("分析服务未加载")


app = FastAPI(title="网球 AI 教练后端")

# 注册日记/语音相关接口
app.include_router(diary_router)

# 注册朋友圈相关接口
app.include_router(moments_router)

# 创建上传目录并暴露静态资源
Path("uploads/audio").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# 全局配置
ADVICE_COOLDOWN = 15.0
ANGLE_CHANGE_THRESHOLD = 5
last_advice_time = 0
last_angles = {"left_knee": 180, "right_knee": 180}
cached_advice = "教练已就绪，请开始动作"
advice_source = "初始"
AI_SEMAPHORE = asyncio.Semaphore(1)


@app.on_event("startup")
async def startup_event():
    try:
        service = await get_analysis_service()
        logger.info("[OK] 视频分析服务已初始化")
    except Exception as e:
        logger.warning(f"[WARN] 视频分析服务初始化失败: {e}")


# ===== 任务存储（内存，重启清空） =====
_task_items: dict = defaultdict(list)
_task_done: dict = {}


@app.post("/api/analyze_video_submit")
async def analyze_video_submit(file: UploadFile = File(...)):
    """
    提交视频，立即返回 task_id，后台异步分析
    """
    task_id = str(uuid.uuid4())
    _task_items[task_id] = []
    _task_done[task_id] = False

    video_bytes = await file.read()
    logger.info(f"[任务提交] task_id={task_id}, 文件={file.filename}")

    async def run_task():
        try:
            service = await get_analysis_service()
            async for chunk in service.analyze_video_stream(video_bytes):
                _task_items[task_id].append(chunk)
                logger.info(f"[任务{task_id[:8]}] 新增结果: {chunk.get('type')}")
        except Exception as e:
            logger.error(f"[任务{task_id[:8]}] 异常: {e}")
            _task_items[task_id].append({
                "type": "error",
                "message": str(e)
            })
        finally:
            _task_done[task_id] = True
            logger.info(f"[任务{task_id[:8]}] 完成，共 {len(_task_items[task_id])} 条结果")

    asyncio.create_task(run_task())

    return JSONResponse({"task_id": task_id})


@app.get("/api/analyze_video_poll/{task_id}")
async def analyze_video_poll(task_id: str, offset: int = 0):
    """
    轮询拉取分析结果，offset 是上次拉取到的位置
    前端每次把上次的 total 作为新的 offset 传进来
    """
    if task_id not in _task_done:
        raise HTTPException(status_code=404, detail="task_id 不存在")

    items = _task_items[task_id]
    new_items = items[offset:]

    return JSONResponse({
        "items": new_items,
        "done": _task_done[task_id],
        "total": len(items)
    })


@app.post("/api/analyze_video")
async def analyze_video(file: UploadFile = File(...)):
    """
    视频分析接口（完全流式 SSE 版）
    前端发来文件，后端一边分析，一边向前端推送最新的动作片段和豆包建议。
    """
    try:
        logger.info(f"[视频分析] 收到文件: {file.filename}，准备启动流式分析...")
        video_bytes = await file.read()
        service = await get_analysis_service()

        async def event_generator():
            try:
                async for chunk in service.analyze_video_stream(video_bytes):
                    payload = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {payload}\n\n"

                finish_payload = json.dumps(
                    {"type": "finished", "message": "分析结束"},
                    ensure_ascii=False
                )
                yield f"data: {finish_payload}\n\n"

            except Exception as e:
                logger.error(f"[流式处理异常] {e}")
                traceback.print_exc()
                error_payload = json.dumps(
                    {"type": "error", "message": str(e)},
                    ensure_ascii=False
                )
                yield f"data: {error_payload}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"[ERROR] 接口初始化失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务内部错误: {str(e)}")


@app.post("/api/analyze_video_json")
async def analyze_video_json(file: UploadFile = File(...)):
    """
    Non-streaming video analysis endpoint for clients that cannot reliably read SSE.
    It keeps /api/analyze_video untouched and returns the collected result as JSON.

    返回格式:
    {
        "status": "success",
        "segments": [
            {
                "segment_id": 1,
                "shot_type": "forehand",
                "shot_type_cn": "正手",
                "analysis": {...},
                "coach_advice": "教练建议文本"
            }
        ],
        "summary": {...}
    }
    """
    try:
        logger.info(f"[视频分析JSON] 收到文件: {file.filename}，开始完整分析...")
        video_bytes = await file.read()
        service = await get_analysis_service()

        segments = []
        summary = None

        async for chunk in service.analyze_video_stream(video_bytes):
            chunk_type = chunk.get("type")

            if chunk_type == "segment":
                segment_data = chunk.get("data", {})
                segments.append(segment_data)

                logger.info(
                    f"[片段 {segment_data.get('segment_id')}] "
                    f"类型={segment_data.get('shot_type_cn')}, "
                    f"教练建议={'有' if segment_data.get('coach_advice') else '无'}"
                )

            elif chunk_type == "summary":
                summary = chunk.get("data")

            elif chunk_type == "error":
                error_msg = chunk.get("message", "视频分析失败")
                logger.error(f"[分析错误] {error_msg}")
                raise RuntimeError(error_msg)

        logger.info(f"[分析完成] 共 {len(segments)} 个片段")

        return JSONResponse({
            "status": "success",
            "segments": segments,
            "summary": summary or {
                "num_segments": len(segments),
                "num_frames": 0,
                "fps": 0,
                "duration": 0
            }
        })

    except Exception as e:
        logger.error(f"[ERROR] JSON视频分析失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")


@app.websocket("/ws/joints")
async def websocket_endpoint(websocket: WebSocket):
    """
    实时姿态监控 WebSocket 接口
    """
    global last_advice_time, cached_advice, last_angles, advice_source

    await websocket.accept()
    logger.info(f"[WebSocket] 客户端已连接: {websocket.client.host}")

    try:
        while True:
            try:
                raw_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.warning(f"[WARN] 数据接收失败: {e}")
                break

            le = raw_data.get("left_elbow", 180)
            re = raw_data.get("right_elbow", 180)
            lk = raw_data.get("left_knee", 180)
            rk = raw_data.get("right_knee", 180)

            now = time.time()
            current_tts = True

            knee_abnormal = (lk < 90 or rk < 90)
            cooldown_passed = (now - last_advice_time > ADVICE_COOLDOWN)
            angle_changed = (
                abs(lk - last_angles["left_knee"]) > ANGLE_CHANGE_THRESHOLD
                or abs(rk - last_angles["right_knee"]) > ANGLE_CHANGE_THRESHOLD
            )

            if cooldown_passed and (knee_abnormal or angle_changed):
                real_advice = None
                retry_count = 0

                while retry_count < 4 and real_advice is None:
                    try:
                        async with AI_SEMAPHORE:
                            real_advice = await asyncio.wait_for(
                                get_fitness_advice(raw_data),
                                timeout=45.0
                            )
                    except asyncio.TimeoutError:
                        retry_count += 1
                    except Exception:
                        retry_count += 1

                if real_advice and "失败" not in real_advice and "异常" not in real_advice:
                    cached_advice = real_advice
                    current_tts = True
                    last_advice_time = now
                    last_angles = {
                        "left_knee": lk,
                        "right_knee": rk
                    }
                    advice_source = "豆包"

            response_payload = {
                "left_elbow": le,
                "right_elbow": re,
                "left_knee": lk,
                "right_knee": rk,
                "content": str(cached_advice),
                "tts": current_tts,
                "source": advice_source,
                "timestamp": now
            }

            try:
                await websocket.send_json(response_payload)
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info("[WebSocket] 连接断开")
    except Exception as e:
        logger.error(f"[ERROR] WebSocket 异常: {e}")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "网球 AI 教练"
    }


if __name__ == "__main__":
    logger.info("[START] 网球 AI 教练后端服务启动中...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info",
        # ws_max_size=16777216,
        # ssl_keyfile="./key.pem",
        # ssl_certfile="./cert.pem"
    )
