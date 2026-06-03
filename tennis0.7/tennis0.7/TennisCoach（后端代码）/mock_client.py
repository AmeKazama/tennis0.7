import asyncio
import websockets
import json
import random
import sys

WS_URL = "ws://10.24.51.159:9000/ws/joints"

# 预设姿势数据（包含描述和关节角度）
POSE_PRESETS = {
    "标准准备姿势": {
        "description": "标准网球准备姿势，膝盖微弯，重心适中",
        "data": {"left_elbow": 150, "right_elbow": 155, "left_knee": 115, "right_knee": 120}
    },
    "左膝过弯": {
        "description": "左膝弯曲过度（<90度），重心过低",
        "data": {"left_elbow": 155, "right_elbow": 160, "left_knee": 72, "right_knee": 125}
    },
    "右膝过弯": {
        "description": "右膝弯曲过度（<90度），重心过低",
        "data": {"left_elbow": 150, "right_elbow": 158, "left_knee": 120, "right_knee": 78}
    },
    "双膝过弯": {
        "description": "双膝都弯曲过度，重心严重偏低",
        "data": {"left_elbow": 145, "right_elbow": 150, "left_knee": 68, "right_knee": 75}
    },
    "左肘过低": {
        "description": "左肘位置过低，可能影响挥拍",
        "data": {"left_elbow": 95, "right_elbow": 155, "left_knee": 115, "right_knee": 120}
    },
    "右肘过低": {
        "description": "右肘位置过低，可能影响挥拍",
        "data": {"left_elbow": 150, "right_elbow": 98, "left_knee": 120, "right_knee": 118}
    },
    "站姿过直": {
        "description": "膝盖完全伸直，缺乏弹性",
        "data": {"left_elbow": 165, "right_elbow": 170, "left_knee": 178, "right_knee": 175}
    },
    "正手击球准备": {
        "description": "正手击球前的准备姿势",
        "data": {"left_elbow": 130, "right_elbow": 110, "left_knee": 105, "right_knee": 100}
    }
}


def print_presets():
    """打印所有预设姿势"""
    print("\n" + "=" * 60)
    print("📋 可用预设姿势：")
    print("=" * 60)
    for idx, (name, info) in enumerate(POSE_PRESETS.items(), 1):
        print(f"  {idx}. {name}")
        print(f"     {info['description']}")
        print(f"     角度: 左肘{info['data']['left_elbow']}° 右肘{info['data']['right_elbow']}° "
              f"左膝{info['data']['left_knee']}° 右膝{info['data']['right_knee']}°")
        print()


def get_random_pose():
    """随机获取一个姿势"""
    return random.choice(list(POSE_PRESETS.items()))


async def send_single_pose(websocket, pose_name, pose_data):
    """发送单个姿势"""
    print(f"\n🎯 发送姿势: {pose_name}")
    print(f"📊 数据: {pose_data}")
    await websocket.send(json.dumps(pose_data))
    print("✅ 发送成功")

    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
        result = json.loads(response)
        print(f"\n📥 收到后端回复:")
        print(f"   关节角度: 左肘{result['left_elbow']}° 右肘{result['right_elbow']}° "
              f"左膝{result['left_knee']}° 右膝{result['right_knee']}°")
        print(f"   AI建议: {result['content']}")
        print(f"   TTS: {result['tts']}")
        
        source = result.get('source', '未知')
        source_emoji = {
            '豆包': '🤖',
            '默认': '📋',
            '超时': '⏰',
            '错误': '❌',
            '初始': '📌'
        }.get(source, '❓')
        print(f"   来源: {source_emoji} {source}")
    except asyncio.TimeoutError:
        print("⏰ 等待回复超时（15秒）")
    except Exception as e:
        print(f"❌ 接收回复失败: {e}")


async def loop_send_pose(websocket, interval=10):
    """循环发送姿势"""
    print(f"\n🔄 开始循环发送模式（间隔 {interval} 秒）...")
    print("   按 Ctrl+C 停止\n")
    count = 0

    try:
        while True:
            count += 1
            pose_name, pose_info = get_random_pose()
            print(f"--- [{count}] {pose_name} ---")
            await send_single_pose(websocket, pose_name, pose_info['data'])
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n⏹️  循环发送已停止")


async def interactive_mode(websocket):
    """交互模式"""
    print_presets()

    while True:
        print("\n" + "-" * 60)
        print("请选择操作:")
        print("  1-8. 发送对应预设姿势")
        print("  r. 随机发送一个姿势")
        print("  l. 循环发送（每10秒）")
        print("  q. 退出")
        choice = input("请输入选项: ").strip().lower()

        if choice == 'q':
            break
        elif choice == 'r':
            pose_name, pose_info = get_random_pose()
            await send_single_pose(websocket, pose_name, pose_info['data'])
        elif choice == 'l':
            await loop_send_pose(websocket, interval=10)
        elif choice.isdigit():
            idx = int(choice) - 1
            presets_list = list(POSE_PRESETS.items())
            if 0 <= idx < len(presets_list):
                pose_name, pose_info = presets_list[idx]
                await send_single_pose(websocket, pose_name, pose_info['data'])
            else:
                print("❌ 无效的选项")
        else:
            print("❌ 无效的选项")


async def main():
    print("=" * 60)
    print("🎾 网球 AI 教练 - 模拟数据客户端")
    print("=" * 60)
    print(f"连接地址: {WS_URL}")
    print()

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket 连接成功！\n")
            await interactive_mode(websocket)

    except ConnectionRefusedError:
        print("❌ 无法连接到服务器！")
        print("   请检查:")
        print("   1. 后端服务是否已启动（python main.py）")
        print("   2. 连接地址是否正确（当前: " + WS_URL + "）")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
