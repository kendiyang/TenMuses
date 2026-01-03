#!/usr/bin/env python3
"""
WebSocket测试脚本 - 验证工作流执行流式输出
"""

import asyncio
import json
import websockets
from datetime import datetime

# 配置
THREAD_ID = "acc9ca28-6b50-46b2-8b21-0c2b66b567f4"  # 前面创建的Run对应的thread_id
WS_URL = f"ws://localhost:8000/ws/run/{THREAD_ID}"

async def test_websocket():
    """测试WebSocket连接和事件接收"""
    print(f"🔗 连接到 WebSocket: {WS_URL}")
    print("-" * 80)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"✅ WebSocket连接成功")
            print()
            
            event_count = 0
            token_count = 0
            start_time = datetime.now()
            
            # 接收事件直到连接关闭
            async for message in websocket:
                event_count += 1
                
                try:
                    event = json.loads(message)
                except json.JSONDecodeError:
                    print(f"⚠️  无法解析消息: {message[:100]}")
                    continue
                
                event_type = event.get("type", "unknown")
                run_id = event.get("runId", "-")
                thread_id = event.get("threadId", "-")
                node_id = event.get("nodeId", "-")
                
                print(f"[{event_type:15}] runId={run_id[:8]}... threadId={thread_id[:8]}... nodeId={node_id}")
                
                # 处理Token流
                if event_type == "token":
                    payload = event.get("payload", {})
                    content = payload.get("content", "")
                    finished = payload.get("finished", False)
                    token_count += 1
                    print(f"  └─ Token #{token_count}: {repr(content)} (finished={finished})")
                
                # 处理错误
                elif event_type == "error":
                    payload = event.get("payload", {})
                    message_text = payload.get("message", "Unknown error")
                    print(f"  └─ ❌ 错误: {message_text}")
                
                # 处理节点状态
                elif event_type in ["node_started", "node_status", "node_completed"]:
                    payload = event.get("payload", {})
                    label = payload.get("label", "")
                    status = payload.get("status", "")
                    print(f"  └─ {label or status}")
                
                # 处理运行状态
                elif event_type in ["run_started", "run_completed"]:
                    payload = event.get("payload", {})
                    status = payload.get("status", "")
                    print(f"  └─ 状态: {status}")
                    
                print()
                
                # 如果运行完成，断开连接
                if event_type == "run_completed":
                    print("🏁 工作流执行完成")
                    break
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print("-" * 80)
            print(f"📊 统计:")
            print(f"   - 总事件数: {event_count}")
            print(f"   - Token数: {token_count}")
            print(f"   - 耗时: {elapsed:.2f}秒")
            print()
            
            if token_count > 0:
                print("✅ WebSocket流式输出正常工作!")
                return True
            else:
                print("⚠️  未收到任何Token数据")
                return False
                
    except ConnectionRefusedError:
        print("❌ 连接被拒绝 - 请确保后端服务在运行")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⛔ 测试被中断")
        exit(1)
