# 导入依赖库
import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ====================== 项目配置区(可修改) ======================
# 静态资源根目录
STATIC_ROOT = "static"
# 视频存放子文件夹
VIDEO_DIR = os.path.join(STATIC_ROOT, "videos")
# 封面图片存放子文件夹
COVER_DIR = os.path.join(STATIC_ROOT, "covers")
# 默认每页条数（前端上拉一次加载几条）
DEFAULT_PAGE_SIZE = 3
# ==========================================================

# 实例化FastAPI应用
app = FastAPI(
    title="网球教练-短视频Feed后端",
    description="提供刷视频分页接口，自动扫描本地mp4、png资源",
    version="1.0"
)

# 配置跨域，uniapp小程序/H5前端跨域必备
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有前端域名，上线改成指定域名
    allow_credentials=True,
    allow_methods=["*"],           # 允许所有请求方式 GET/POST
    allow_headers=["*"],           # 放行所有请求头
)

# 自动创建文件夹，不存在则新建，防止报错
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)

# 挂载静态目录：URL /static 映射本地static文件夹，直接访问mp4/png资源
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


def scan_video_resource():
    """
    工具函数：自动扫描videos、covers，按文件名序号匹配视频和封面
    规则：1.mp4 对应 1.png，2.mp4对应2.png，以此类推
    返回组装好的视频列表数组
    """
    video_list = []
    # 遍历视频文件夹所有文件
    for file_name in os.listdir(VIDEO_DIR):
        # 只处理mp4后缀视频
        if not file_name.endswith(".mp4"):
            continue
        # 获取纯数字文件名 如 1.mp4 → "1"
        file_no = file_name.replace(".mp4", "")
        # 拼接封面路径
        cover_name = f"{file_no}.png"
        cover_full_path = os.path.join(COVER_DIR, cover_name)
        # 封面不存在则跳过本条资源
        if not os.path.exists(cover_full_path):
            continue

        # 组装接口返回的资源访问地址（前端请求的网络路径）
        video_url = f"/static/videos/{file_name}"
        cover_url = f"/static/covers/{cover_name}"

        # 生成视频标题和简介（可后续改成自定义配置）
        title_map = {
            "1": "网球正手基础教学",
            "2": "双手反手发力技巧",
            "3": "平击发球稳定练习",
            "4": "网前截击基础",
            "5": "步伐跑动训练"
        }
        desc_map = {
            "1": "新手入门正手挥拍动作、站位讲解",
            "2": "反手转体、击球点、步伐训练",
            "3": "抛球+挥拍连贯，提升发球成功率",
            "4": "近距离网前拦网，手腕控制要点",
            "5": "前后左右跑动，提升接球覆盖范围"
        }

        video_item = {
            "id": int(file_no),
            "title": title_map.get(file_no, f"网球教学{file_no}"),
            "desc": desc_map.get(file_no, "网球基础训练课程"),
            "video_url": video_url,
            "cover_url": cover_url
        }
        video_list.append(video_item)

    # 按id升序排序，保证列表顺序固定
    video_list.sort(key=lambda x: x["id"])
    return video_list


# 核心分页接口：前端刷视频调用【/api/feed/list】
@app.get("/api/feed/list", summary="短视频分页列表｜上拉加载更多")
def get_feed_list(
    page: int = Query(default=1, ge=1, description="当前页码，从1开始"),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, gt=0, description="每页数量")
):
    """
    分页逻辑：
    page=1 取第1~page_size条
    page=2 取page_size+1 ~ 2*page_size条
    前端上拉翻页只需要page+1
    """
    all_video_data = scan_video_resource()
    # 切片计算起止下标
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = all_video_data[start_idx:end_idx]

    return {
        "code": 200,
        "msg": "请求成功",
        "total": len(all_video_data),   # 总条数，前端判断没有更多
        "page": page,
        "page_size": page_size,
        "data": page_data
    }


# 程序入口，直接运行py即可启动服务
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)