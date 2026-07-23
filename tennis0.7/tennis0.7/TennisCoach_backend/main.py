from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import traceback
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from routers.diary import router as diary_router
from routers.feed import register_feed_static, router as feed_router
from routers.rally_cut import router as rally_router
from routers.rally_favorite import router as rally_favorite_router
from routers.tts import register_tts_static, router as tts_router
from routers.user_profile import router as user_profile_router
from routers.user_follow import router as user_follow_router
from routers.user_device import router as user_device_router
from routers.user_badge import router as user_badge_router
from routers.user_training_stats import router as user_training_stats_router
from routers.action_analysis_record import router as action_analysis_record_router
from routers.action_analysis_segment import router as action_analysis_segment_router
from routers.training_video_record import router as training_video_record_router
from routers.ball_diary import router as ball_diary_router
from routers.community_post import router as community_post_router
from routers.favorite_folder import router as favorite_folder_router
from routers.favorite_item import router as favorite_item_router
from routers.videos import router as videos_router
from database import engine
from db_models.community_post import CommunityPost
from db_models.rally_favorite import RallyFavorite
from sqlalchemy import inspect, text
from services.action_analysis_repository import save_action_analysis_record

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入服务
try:
    from services.tennis_analysis_service import get_analysis_service

    logger.info("[OK] 成功加载所有服务")
except ImportError as e:
    logger.error(f"[ERROR] 服务加载失败: {e}")

    # 降级处理
    async def get_analysis_service():
        raise RuntimeError("分析服务未加载")


app = FastAPI(title="网球 AI 教练后端")
H5_DIR = Path(__file__).resolve().parent / "h5"

if H5_DIR.exists():
    app.mount(
        "/h5",
        StaticFiles(directory=str(H5_DIR), html=True),
        name="h5",
    )

# H5 临时测试：兼容 HBuilderX 打包后从根路径 /assets、/static 加载资源
ASSETS_DIR = H5_DIR / "assets"
STATIC_H5_DIR = H5_DIR / "static"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="h5_assets")

if STATIC_H5_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_H5_DIR)), name="h5_static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options("/{full_path:path}")
async def options_preflight(full_path: str):
    return JSONResponse(
        content={"ok": True},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Private-Network": "true",
        },
    )


# 注册日记/语音相关接口
app.include_router(diary_router)
# 注册回合切割接口
app.include_router(rally_router)
# 回合收藏接口
app.include_router(rally_favorite_router)
# 注册首页视频流接口
app.include_router(feed_router)
# 注册文字转语音接口
app.include_router(tts_router)
# 用户信息接口
app.include_router(user_profile_router)
# 用户关注接口
app.include_router(user_follow_router)
# 用户设备接口
app.include_router(user_device_router)
# 用户勋章接口
app.include_router(user_badge_router)
# 用户训练数据接口
app.include_router(user_training_stats_router)
# 动作分析主记录接口
app.include_router(action_analysis_record_router)
# 动作分析片段记录接口
app.include_router(action_analysis_segment_router)
# 训练视频接口
app.include_router(training_video_record_router)
# 打球日记接口
app.include_router(ball_diary_router)
# 社区发布内容接口
app.include_router(community_post_router)
# 收藏夹接口
app.include_router(favorite_folder_router)
# 收藏内容明细接口
app.include_router(favorite_item_router)
# 短视频接口
app.include_router(videos_router)

# 创建目录并暴露静态资源
Path("uploads/audio").mkdir(parents=True, exist_ok=True)
Path("output_rallies").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/output_rallies", StaticFiles(directory="output_rallies"), name="output_rallies")
register_feed_static(app)
register_tts_static(app)


@app.on_event("startup")
async def startup_event():
    try:
        await asyncio.to_thread(
            RallyFavorite.__table__.create,
            bind=engine,
            checkfirst=True,
        )
        logger.info("[OK] 回合收藏数据表已就绪")
    except Exception as e:
        logger.warning(f"[WARN] 回合收藏数据表初始化失败: {e}")

    try:
        await asyncio.to_thread(
            CommunityPost.__table__.create,
            bind=engine,
            checkfirst=True,
        )

        def ensure_community_post_title():
            columns = {
                column["name"]
                for column in inspect(engine).get_columns("community_post")
            }
            if "title" not in columns:
                alter_statement = "ALTER TABLE community_post ADD COLUMN title VARCHAR(120) NULL"
                if engine.dialect.name in {"mysql", "mariadb"}:
                    alter_statement += " AFTER user_id"
                with engine.begin() as connection:
                    connection.execute(text(alter_statement))

        await asyncio.to_thread(ensure_community_post_title)
        logger.info("[OK] 社区动态标题字段已就绪")
    except Exception as e:
        logger.warning(f"[WARN] 社区动态标题字段初始化失败: {e}")

    try:
        service = await get_analysis_service()
        logger.info("[OK] 视频分析服务已初始化")
    except Exception as e:
        logger.warning(f"[WARN] 视频分析服务初始化失败: {e}")


# ===== 任务存储（内存，重启清空） =====
_task_items: dict = defaultdict(list)
_task_done: dict = {}


@app.post("/api/analyze_video_submit")
async def analyze_video_submit(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    selected_player: Optional[str] = Form(None),
    selected_stroke: Optional[str] = Form(None),
    source_page: str = Form("action_comparison"),
):
    """
    提交视频，立即返回 task_id，后台异步分析
    """
    task_id = str(uuid.uuid4())
    _task_items[task_id] = []
    _task_done[task_id] = False

    video_bytes = await file.read()
    logger.info(f"[任务提交] task_id={task_id}, 文件={file.filename}")

    async def run_task():
        segments = []
        summary = None
        status = "success"
        error_message = None

        try:
            service = await get_analysis_service()
            async for chunk in service.analyze_video_stream(
                video_bytes,
                selected_stroke=selected_stroke,
            ):
                _task_items[task_id].append(chunk)

                chunk_type = chunk.get("type")
                if chunk_type == "segment":
                    segments.append(chunk.get("data", {}))
                elif chunk_type == "summary":
                    summary = chunk.get("data", {})
                elif chunk_type == "error":
                    status = "error"
                    error_message = chunk.get("message")

                logger.info(f"[任务{task_id[:8]}] 新增结果: {chunk_type}")
        except Exception as e:
            status = "error"
            error_message = str(e)
            logger.error(f"[任务{task_id[:8]}] 异常: {e}")
            _task_items[task_id].append({
                "type": "error",
                "message": str(e)
            })
        finally:
            metadata = {
                "analysis_id": task_id,
                "user_id": user_id,
                "source_page": source_page,
                "file_name": file.filename,
                "selected_player": selected_player,
                "selected_stroke": selected_stroke,
            }
            record_id = await asyncio.to_thread(
                save_action_analysis_record,
                metadata,
                segments,
                summary,
                status,
                error_message,
            )
            if record_id:
                _task_items[task_id].append({
                    "type": "record",
                    "data": {"id": record_id, "analysis_id": task_id}
                })

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
        port=6006,
        log_level="info",
        # ws_max_size=16777216,
        # ssl_keyfile="./key.pem",
        # ssl_certfile="./cert.pem"
    )


