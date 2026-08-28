#!/usr/bin/env python3
"""CPU 算法计时：完整走 TennisAnalysisService.analyze_video_stream 管线（与生产同参数）。"""
import asyncio
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from services.tennis_analysis_service import TennisAnalysisService
from services.tennis_final import DoubaoService

MODEL = "services/tennis_rnn_converted.keras"
YOLO = "services/yolov8s.pt"

if "--no-llm" in sys.argv:
    sys.argv.remove("--no-llm")
    async def _no_advice(self, report):
        return ""
    DoubaoService.get_coach_advice = _no_advice
    print("[benchmark] 豆包 LLM 已 patch 跳过\n")

_orig_media = TennisAnalysisService._create_segment_media

def _timed_media(self, video_path, analysis_result, overlay_store=None):
    _t = time.perf_counter()
    _r = _orig_media(self, video_path, analysis_result, overlay_store)
    print(f"  [media] 片段媒体生成(剪辑/封面/骨骼视频)耗时 {time.perf_counter() - _t:.1f}s")
    return _r

TennisAnalysisService._create_segment_media = _timed_media


async def main(video_path: str) -> None:
    with open(video_path, "rb") as f:
        video_bytes = f.read()
    size_mb = len(video_bytes) / 1024 / 1024

    t0 = time.perf_counter()
    service = TennisAnalysisService(model_path=MODEL, yolo_weights=YOLO, use_yolo=True)
    await service.initialize()
    t_init = time.perf_counter() - t0
    print(f"\n[init] 模型加载完成: {t_init:.1f}s (视频 {size_mb:.1f} MB)")

    t1 = time.perf_counter()
    segments = []
    summary = None
    async for chunk in service.analyze_video_stream(video_bytes):
        ct = chunk.get("type")
        now = time.perf_counter() - t1
        if ct == "segment":
            d = chunk.get("data", {})
            segments.append(d)
            a = d.get("analysis", {})
            print(f"  [{now:7.1f}s] segment #{d.get('segment_id')} "
                  f"{d.get('shot_type_cn')} ({d.get('shot_type')}) "
                  f"grade={a.get('grade')} dtw={a.get('distance')}")
        elif ct == "summary":
            summary = chunk.get("data", {})
            print(f"  [{now:7.1f}s] summary 到达")
        elif ct == "error":
            print(f"  [{now:7.1f}s] ERROR: {chunk.get('message')}")

    t_total = time.perf_counter() - t1
    duration = (summary or {}).get("duration")
    print("\n" + "=" * 60)
    print(f"初始化耗时:      {t_init:.1f}s")
    print(f"分析总耗时:      {t_total:.1f}s")
    if duration:
        print(f"视频时长:        {duration:.1f}s  ->  实时倍率 {t_total / duration:.2f}x (处理/视频)")
    print(f"检出片段数:      {len(segments)}")
    await service.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python benchmark_cpu.py <video.mp4>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
