"""
独立测试脚本 - 直接运行 service 分析本地视频

用法：
    python test_service_standalone.py your_video.mp4
"""

import asyncio
import sys
import os

# 导入 service
from services.tennis_analysis_service import TennisAnalysisService


async def test_local_video(video_path: str):
    """测试本地视频文件"""

    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return

    print(f"=" * 80)
    print(f"测试视频: {video_path}")
    print(f"=" * 80)

    # 读取视频为字节流（模拟前端上传）
    print("\n[1] 读取视频文件...")
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    print(f"✅ 读取完成，大小: {len(video_bytes) / 1024 / 1024:.2f} MB")

    # 初始化服务
    print("\n[2] 初始化分析服务...")
    service = TennisAnalysisService()
    await service.initialize()

    # 开始分析
    print("\n[3] 开始流式分析...")
    print("=" * 80)

    segment_count = 0

    async for chunk in service.analyze_video_stream(video_bytes):
        chunk_type = chunk.get("type")

        if chunk_type == "segment":
            segment_count += 1
            data = chunk.get("data")

            print(f"\n{'=' * 80}")
            print(f"🎾 片段 #{data['segment_id']}: {data['shot_type_cn']} ({data['shot_type']})")
            print(f"{'=' * 80}")
            print(f"  击球时刻: {data['impact_time']:.2f}s")
            print(f"  帧范围: {data['frame_range'][0]} - {data['frame_range'][1]}")
            print(f"  时间范围: {data['time_range'][0]:.2f}s - {data['time_range'][1]:.2f}s")
            print(f"\n  分析结果:")
            print(f"    评级: {data['analysis']['grade']}")
            print(f"    DTW 距离: {data['analysis']['distance']:.1f}")
            print(f"    关注侧: {data['analysis']['focus_side']}")
            print(f"    帧数: {data['analysis']['num_frames']}")

            print(f"\n  主要问题:")
            for i, issue in enumerate(data['analysis']['top_issues'], 1):
                print(f"    {i}. {issue['joint']}: {issue['signed_error']:+.1f}° ({issue['direction']})")

            print(f"\n  🤖 教练建议:")
            print(f"    {data['coach_advice']}")
            print(f"{'=' * 80}\n")

        elif chunk_type == "summary":
            data = chunk.get("data")
            print(f"\n{'=' * 80}")
            print(f"📊 分析完成")
            print(f"{'=' * 80}")
            print(f"  总片段数: {data['num_segments']}")
            print(f"  总帧数: {data['num_frames']}")
            print(f"  FPS: {data['fps']:.1f}")
            print(f"  时长: {data['duration']:.2f}s")
            print(f"{'=' * 80}")

        elif chunk_type == "error":
            print(f"\n❌ 错误: {chunk.get('message')}")

    if segment_count == 0:
        print(f"\n⚠️  警告: 未检测到任何击球片段！")
        print(f"  可能原因:")
        print(f"    1. RNN 模型输出全是 neutral")
        print(f"    2. 视频中没有明显的击球动作")
        print(f"    3. 视频格式/编码问题")
    else:
        print(f"\n✅ 成功检测到 {segment_count} 个击球片段")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_service_standalone.py <video_path>")
        print("\n示例:")
        print("  python test_service_standalone.py test_video.mp4")
        print("  python test_service_standalone.py /path/to/tennis_video.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    asyncio.run(test_local_video(video_path))