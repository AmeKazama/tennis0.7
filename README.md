# 网球 AI 教练项目开发说明

本项目是一个前后端分离的网球 AI 教练系统。后端负责视频上传、人体姿态识别、动作片段分析、模型推理、AI 教练建议生成；前端负责移动端交互、视频选择/拍摄、上传分析、结果展示、社交和个人主页等功能。

## 1. 项目结构

当前 Git 仓库主要目录如下：

```text
tennis0.7/
├── README.md
├── requirements.txt
└── tennis0.7/
    └── tennis0.7/
        ├── TennisCoach（后端代码）/
        │   ├── main.py
        │   ├── services/
        │   ├── routers/
        │   ├── weights/
        │   └── models/
        └── doubao_service（前端huilderx）/
            ├── App.vue
            ├── main.js
            ├── pages.json
            ├── pages/
            ├── components/
            └── utils/
```

由于历史压缩包和目录迁移原因，项目目录存在多层 `tennis0.7/tennis0.7/tennis0.7` 嵌套。开发时请以实际包含 `TennisCoach（后端代码）` 和 `doubao_service（前端huilderx）` 的目录为准。

## 2. 开发环境

当前项目已验证运行环境如下：

| 模块 | 环境 |
|---|---|
| 操作系统 | Windows |
| Python | Python 3.11.8 |
| 后端框架 | FastAPI + Uvicorn |
| AI/视觉库 | TensorFlow、Keras、PyTorch、OpenCV、NumPy、Pandas |
| 前端框架 | uni-app + Vue 3 |
| 前端 IDE | HBuilderX |
| 移动端测试 | Android 真机优先 |
| 后端默认端口 | 9000 |
| TTS/语音相关端口 | 9002 |

注意：TensorFlow 2.11 及以上版本在 Windows 原生环境下默认不使用 CUDA GPU。本项目在 Windows 下主要按 CPU 推理方式运行。

## 3. 后端启动方式

进入后端目录：

```powershell
cd C:\Users\29327\Desktop\网球\tennis0.7\tennis0.7\tennis0.7\TennisCoach（后端代码）
```

建议使用 Python 3.11 创建虚拟环境：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -r ..\..\..\requirements.txt
```

如果开发成员是在 Git 仓库根目录执行，也可以直接：

```powershell
python -m pip install -r requirements.txt
```

启动后端：

```powershell
python main.py
```

成功启动后，控制台应看到类似：

```text
[OK] 成功加载所有服务
[服务] RNN 模型加载完成
[OK] 视频分析服务已初始化
Uvicorn running on http://0.0.0.0:9000
```

浏览器访问：

```text
http://127.0.0.1:9000/docs
```

如果是真机前端访问，需要使用电脑局域网 IP，例如：

```text
http://192.168.1.53:9000/docs
```

## 4. 前端启动方式

前端目录：

```text
tennis0.7/tennis0.7/doubao_service（前端huilderx）
```

使用 HBuilderX 打开该目录，然后：

```text
运行 -> 运行到手机或模拟器 -> 运行到 Android App 基座
```

推荐使用 Android 真机测试。部分 Android 模拟器或 HBuilderX 标准基座可能不支持某些原生能力。

## 5. 前后端连接配置

前端目前存在写死的后端地址。开发成员如果电脑 IP 不同，需要替换为自己电脑的局域网 IP。

当前已配置地址示例：

```text
http://192.168.1.53:9000
ws://192.168.1.53:9000/ws/joints
```

主要涉及文件：

```text
doubao_service（前端huilderx）/pages/ai-coach/coach-test/coach-test.vue
doubao_service（前端huilderx）/pages/coach-test/coach-test.vue
doubao_service（前端huilderx）/pages/training/highlight-edit/highlight-edit.vue
doubao_service（前端huilderx）/pages/content/diary/diary.vue
```

如果换电脑或换 Wi-Fi，请先执行：

```powershell
ipconfig
```

找到 WLAN 的 IPv4 地址，然后将前端中的 `192.168.1.53` 替换成自己的 IP。

真机测试时请确保：

- 手机和电脑连接同一个 Wi-Fi。
- 后端正在运行。
- Windows 防火墙允许 Python 或 9000 端口通信。
- 手机浏览器可以打开 `http://电脑IP:9000/docs`。

## 6. 重要模型文件

后端运行依赖以下模型文件，开发成员拉取项目后需要确认这些文件存在：

```text
TennisCoach（后端代码）/services/movenet.tflite
TennisCoach（后端代码）/services/tennis_rnn_converted.keras
TennisCoach（后端代码）/services/yolov8s.pt
TennisCoach（后端代码）/weights/tennisball.pt
TennisCoach（后端代码）/weights/yolov8n.pt
TennisCoach（后端代码）/weights/court_detector.pth
TennisCoach（后端代码）/weights/tracknet.pth
```

这些文件属于模型权重，不是 Python 包。如果缺失，后端可能出现模型加载失败、视频分析失败或回合剪辑失败。

## 7. 环境变量配置

项目支持 `.env` 文件，但 `.env` 不应提交到 GitHub。开发成员可参考 `.env.example` 创建自己的 `.env`。

常见配置包括：

```text
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/tennis_app?charset=utf8mb4
DOUBAO_API_KEY=你的豆包 API Key
BAIDU_API_KEY=你的百度语音识别 Key
BAIDU_SECRET_KEY=你的百度语音识别 Secret
```

如果只测试视频分析主链路，百度语音识别配置不完整通常只会出现 warning，不一定影响后端主服务启动。

## 8. 常见问题

### 8.1 前端一直显示“连接中”

通常是前端 WebSocket 地址不对。检查：

```text
ws://电脑IP:9000/ws/joints
```

不要在真机前端中使用 `localhost`，因为手机里的 `localhost` 指的是手机本身，不是电脑。

### 8.2 上传视频时报 OPTIONS 405

说明后端没有正确处理跨域预检请求。当前 `main.py` 已加入 CORS 和全局 OPTIONS 兜底路由。修改后必须重启后端。

### 8.3 pip 已安装但仍提示 No module named xxx

通常是装到了错误的 Python 环境。请使用：

```powershell
python -c "import sys; print(sys.executable)"
python -m pip show 包名
```

确保运行项目的 Python 与安装依赖的 Python 是同一个。

### 8.4 TensorFlow 提示 GPU 不可用

这是 Windows + TensorFlow 新版本的正常提示。本项目可以用 CPU 跑，不影响基本功能。

## 9. Git 提交注意事项

不要提交以下内容：

```text
.venv/
venv/
site-packages/
__pycache__/
.env
.idea/
unpackage/
*.mp4
tts_audio/
```

模型文件本项目允许提交，但后续如果模型变大，建议改用 Git LFS 或网盘统一管理。

## 10. 推荐开发流程

多人协作时，建议每次开发前先同步远端：

```powershell
git pull --rebase
```

开发完成后：

```powershell
git add .
git commit -m "说明本次修改"
git push
```

如果本地和远端同时有修改，不要直接强推。先 `pull --rebase`，解决冲突后再 push。

## 11. 服务器（Linux）部署启动

> 本节面向**生产服务器部署**（Linux + conda + GPU），与上面的 Windows 开发机流程不同。
> 在服务器上**只通过 `start.sh` 启动后端**，不要再手动 `python main.py`，避免环境、代理、日志路径等出现歧义。

### 11.1 启动入口

后端代码目录下有一个统一的启动脚本：

```text
tennis0.7/tennis0.7/tennis0.7/TennisCoach_backend/start.sh
```

所有操作都通过它：

```bash
cd tennis0.7/tennis0.7/tennis0.7/TennisCoach_backend

./start.sh              # 启动（默认子命令）
./start.sh start        # 同上；如已在运行则跳过
./start.sh stop         # 停止（先 SIGTERM，10s 后 SIGKILL）
./start.sh restart      # 重启
./start.sh status       # 查看运行状态
./start.sh logs         # 跟踪 server.log（Ctrl+C 退出）
```

脚本会自动：

- **强制使用 conda `tennis` 环境的 python**（`/root/miniconda3/envs/tennis/bin/python`），避免误用 base 环境
- **屏蔽代理环境变量**（`HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 等），让后端对梯子开关免疫（见 11.2）
- 用 `nohup` 后台运行，关闭终端不影响
- 启动后自动等待 `/health` 就绪，超时会提示查看日志

### 11.2 为什么必须屏蔽代理变量

后端调用的外部 API（豆包 `ark.cn-beijing.volces.com`、百度语音）都是**国内服务**，根本不需要走梯子。但 Python 的 `httpx` / `requests` 默认会读取 shell 里的 `HTTP_PROXY` 等环境变量；如果服务器上开了 clash（监听 `127.0.0.1:7890`），一旦梯子关闭：

- 健康检查 `/health` 仍然返回 200（看似正常）
- 但所有调用豆包 / 百度语音的接口会因连不上 `127.0.0.1:7890` 而**静默失败**

因此脚本启动时统一 `unset` 掉这些变量，保证后端行为与梯子开关完全解耦。

### 11.3 容器重启后的恢复

容器重启后，后端**不会自启**。需要登录后手动执行：

```bash
cd /root/autodl-tmp/tennis0.7/tennis0.7/tennis0.7/TennisCoach_backend
./start.sh start
```

验证：

```bash
curl http://127.0.0.1:6006/health     # 应返回 {"status":"healthy",...}
./start.sh status
```

### 11.4 验证代理变量是否真的被屏蔽

```bash
# 找到后端进程 PID
./start.sh status

# 查看该进程的环境变量（应无任何 proxy 输出）
cat /proc/<PID>/environ | tr '\0' '\n' | grep -i proxy
```
