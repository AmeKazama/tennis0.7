# 导入依赖库
import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
import shutil

# ====================== 项目配置区(可修改) ======================
STATIC_ROOT = "static"
VIDEO_DIR = os.path.join(STATIC_ROOT, "videos")
COVER_DIR = os.path.join(STATIC_ROOT, "covers")
DEFAULT_PAGE_SIZE = 3
# ==========================================================

app = FastAPI(
    title="网球教练-短视频Feed后端",
    description="提供刷视频分页接口，自动扫描本地mp4、png资源",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

# ------------------------------------------------------------------------------
# 🔥 【改了这里】现在会同时扫描：视频 + 图片
# ------------------------------------------------------------------------------
def scan_all_media():
    media_list = []

    # -------------- 1. 扫描视频 --------------
    # -------------- 1. 扫描视频 --------------
    for file_name in os.listdir(VIDEO_DIR):
        if not file_name.endswith(".mp4"):
            continue
        file_no = file_name.replace(".mp4", "")
        cover_name = f"{file_no}.png"
        cover_path = os.path.join(COVER_DIR, cover_name)

        # ✅ 修复：没有封面也允许显示视频（用视频默认封面）
        # 注释掉这行判断！！！
        # if not os.path.exists(cover_path):
        #     continue

        media_list.append({
            "id": f"vid_{file_no}",
            "type": "video",
            "title": f"网球教学 {file_no}",
            "desc": "训练视频",
            "src": f"/static/videos/{file_name}",
            # 没有封面就用空，前端自动兼容
            "cover": f"/static/covers/{cover_name}" if os.path.exists(cover_path) else ""
        })

    # -------------- 2. 扫描图片（你上传的） --------------
    img_exts = (".png", ".jpg", ".jpeg")
    for file_name in os.listdir(COVER_DIR):
        if not file_name.lower().endswith(img_exts):
            continue
        # 排除视频封面（只加用户上传的图片）
        if file_name[0].isdigit() and file_name.endswith(".png"):
            continue

        media_list.append({
            "id": f"img_{file_name}",
            "type": "image",
            "title": "用户上传图片",
            "desc": "分享图片",
            "src": f"/static/covers/{file_name}",
            "cover": f"/static/covers/{file_name}"
        })

    return media_list


# ------------------------------------------------------------------------------
# 🔥 【改了这里】现在接口返回：视频 + 图片 混合流
# ------------------------------------------------------------------------------
@app.get("/api/feed/list")
def get_feed_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, gt=0)
):
    all_data = scan_all_media()
    start = (page - 1) * page_size
    end = start + page_size
    page_data = all_data[start:end]

    return {
        "code": 200,
        "msg": "请求成功",
        "data": page_data
    }


# ====================== 上传接口（不动） ======================
@app.post("/api/feed/upload")
async def upload_video(video: UploadFile = File(...)):
    # 自动用时间戳重命名，避免中文、重名问题
    import time
    ext = os.path.splitext(video.filename)[-1].lower()  # 拿到 .mp4
    new_filename = f"user_upload_{int(time.time())}{ext}"

    save_path = os.path.join(VIDEO_DIR, new_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # ✅ 返回可播放的 URL（关键！）
    return {
        "code": 200,
        "msg": "上传成功",
        "url": f"/static/videos/{new_filename}"
    }


@app.post("/api/feed/upload-cover")
async def upload_cover(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(("png", "jpg", "jpeg")):
        return {"code": 400, "msg": "仅支持图片"}

    # 自动用时间戳重命名
    import time
    ext = os.path.splitext(file.filename)[-1].lower()
    new_filename = f"user_img_{int(time.time())}{ext}"

    save_path = os.path.join(COVER_DIR, new_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ 返回可访问的图片地址
    return {
        "code": 200,
        "msg": "上传成功",
        "url": f"/static/covers/{new_filename}"
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)