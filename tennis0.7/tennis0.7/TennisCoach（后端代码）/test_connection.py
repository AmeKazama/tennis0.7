import asyncio
import websockets
import json

async def test():
    print("=" * 50)
    print("测试后端连接")
    print("=" * 50)
    
    urls = [
        "ws://localhost:9000/ws/joints",
        "ws://192.168.1.53:9000/ws/joints"
    ]
    
    for url in urls:
        print(f"\n尝试连接: {url}")
        try:
            async with websockets.connect(url, timeout=3) as websocket:
                print(f"  [OK] 连接成功！")
                
                test_data = {
                    "left_elbow": 150,
                    "right_elbow": 155,
                    "left_knee": 72,
                    "right_knee": 125
                }
                print(f"  [TX] 发送测试数据: {test_data}")
                await websocket.send(json.dumps(test_data))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                result = json.loads(response)
                print(f"  [RX] 收到回复:")
                print(f"     建议: {result.get('content')}")
                print(f"     来源: {result.get('source')}")
                print(f"     TTS: {result.get('tts')}")
                
                return url
                
        except Exception as e:
            print(f"  [ERROR] 连接失败: {e}")
    
    return None

if __name__ == "__main__":
    working_url = asyncio.run(test())
    if working_url:
        print("\n" + "=" * 50)
        print(f"[OK] 可用地址: {working_url}")
        print("请将前端的 WS_URL 改成这个地址！")
        print("=" * 50)
    else:
        print("\n[ERROR] 所有地址都无法连接")
