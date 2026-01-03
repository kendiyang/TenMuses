#!/usr/bin/env python3
"""
Phase 2 动态工作流测试脚本

测试：
1. 编译动态工作流
2. 执行动态工作流
3. WebSocket实时流式输出
4. 工具库功能
"""

import asyncio
import json
import aiohttp
import websockets
from datetime import datetime

# 配置
API_URL = "http://localhost:8000/api"
WS_URL = "ws://localhost:8000/api/v1/ws/run"

# 示例登录信息
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"

# ============================================================================
# 工具函数
# ============================================================================

async def register_and_login():
    """注册测试用户并获取JWT Token"""
    async with aiohttp.ClientSession() as session:
        # 注册
        try:
            async with session.post(
                f"{API_URL}/v1/auth/register",
                json={
                    "email": TEST_USER_EMAIL,
                    "username": "testuser",
                    "password": TEST_USER_PASSWORD,
                    "creator_level": 3
                }
            ) as resp:
                if resp.status in [200, 400]:  # 400可能是用户已存在
                    print("✅ 用户已准备好")
        except Exception as e:
            print(f"注册失败: {e}")
            return None
        
        # 登录
        try:
            async with session.post(
                f"{API_URL}/v1/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            ) as resp:
                data = await resp.json()
                token = data.get("access_token")
                print(f"✅ 登录成功，Token: {token[:20]}...")
                return token
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return None


async def test_workflow_compilation(token: str):
    """测试工作流编译"""
    print("\n" + "="*60)
    print("📋 测试 1: 工作流编译")
    print("="*60)
    
    # 定义一个简单的3节点工作流
    graph = {
        "nodes": [
            {
                "id": "node-1",
                "type": "llm",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "研究",
                    "description": "进行数据研究",
                    "llm_config": {
                        "provider": "openai",
                        "model": "gpt-4-turbo-preview",
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "system_prompt": "你是一位专业的研究员。"
                    }
                }
            },
            {
                "id": "node-2",
                "type": "llm",
                "position": {"x": 300, "y": 100},
                "data": {
                    "label": "写作",
                    "description": "撰写内容",
                    "llm_config": {
                        "provider": "openai",
                        "model": "gpt-4-turbo-preview",
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                }
            },
            {
                "id": "node-3",
                "type": "llm",
                "position": {"x": 500, "y": 100},
                "data": {
                    "label": "审核",
                    "description": "质量审查",
                    "llm_config": {
                        "provider": "openai",
                        "model": "gpt-4-turbo-preview",
                        "temperature": 0.3,
                        "max_tokens": 500
                    }
                }
            }
        ],
        "edges": [
            {
                "id": "edge-1-2",
                "source": "node-1",
                "target": "node-2",
                "type": "normal"
            },
            {
                "id": "edge-2-3",
                "source": "node-2",
                "target": "node-3",
                "type": "normal"
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with session.post(
                f"{API_URL}/v1/dynamic/workflows/compile",
                json=graph,
                headers=headers
            ) as resp:
                data = await resp.json()
                
                if resp.status == 200:
                    print(f"✅ 编译成功")
                    print(f"   节点数: {data['nodeCount']}")
                    print(f"   边数: {data['edgeCount']}")
                    print(f"   节点类型: {data['nodeTypes']}")
                    print(f"   开始节点: {data['startNodes']}")
                    print(f"   结束节点: {data['endNodes']}")
                    if data.get('warnings'):
                        print(f"   ⚠️ 警告: {data['warnings']}")
                    return graph
                else:
                    print(f"❌ 编译失败: {data}")
                    return None
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None


async def test_workflow_validation(token: str):
    """测试工作流验证"""
    print("\n" + "="*60)
    print("✅ 测试 2: 工作流验证")
    print("="*60)
    
    # 定义一个有错误的工作流（缺少LLM配置）
    invalid_graph = {
        "nodes": [
            {
                "id": "node-1",
                "type": "llm",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "无配置节点",
                    "description": "缺少LLM配置的节点"
                    # 注意：没有llm_config
                }
            }
        ],
        "edges": []
    }
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with session.post(
                f"{API_URL}/v1/dynamic/validate",
                json=invalid_graph,
                headers=headers
            ) as resp:
                data = await resp.json()
                
                print(f"验证结果: {'✅ 有效' if data['valid'] else '❌ 无效'}")
                if data['errors']:
                    print(f"❌ 错误:")
                    for error in data['errors']:
                        print(f"   - {error}")
                if data['warnings']:
                    print(f"⚠️ 警告:")
                    for warning in data['warnings']:
                        print(f"   - {warning}")
                
                return data
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None


async def test_list_tools(token: str):
    """测试工具库列表"""
    print("\n" + "="*60)
    print("🔧 测试 3: 工具库")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with session.get(
                f"{API_URL}/v1/dynamic/tools",
                headers=headers
            ) as resp:
                data = await resp.json()
                
                print(f"✅ 可用工具数: {len(data['tools'])}")
                for tool_name, description in data['tools'].items():
                    print(f"   - {tool_name}: {description}")
                
                return data
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None


async def test_workflow_templates(token: str):
    """测试工作流模板"""
    print("\n" + "="*60)
    print("📚 测试 4: 工作流模板")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with session.get(
                f"{API_URL}/v1/dynamic/templates",
                headers=headers
            ) as resp:
                data = await resp.json()
                
                print(f"✅ 可用模板数: {len(data['templates'])}")
                for template in data['templates']:
                    print(f"\n   📌 {template['name']}")
                    print(f"      ID: {template['id']}")
                    print(f"      描述: {template['description']}")
                    print(f"      节点: {template['nodeCount']}, 类型: {template['nodeTypes']}")
                
                return data
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None


async def test_workflow_execution(token: str, graph: dict):
    """测试动态工作流执行"""
    print("\n" + "="*60)
    print("▶️ 测试 5: 工作流执行")
    print("="*60)
    
    input_data = {
        "topic": "人工智能的未来发展趋势",
        "max_length": 1000
    }
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with session.post(
                f"{API_URL}/v1/dynamic/workflows/execute",
                json={"graph_data": graph, "input_data": input_data},
                headers=headers
            ) as resp:
                data = await resp.json()
                
                if resp.status == 200:
                    print(f"✅ 执行启动成功")
                    print(f"   Thread ID: {data['threadId']}")
                    print(f"   WebSocket URL: {data['wsUrl']}")
                    print(f"   状态: {data['status']}")
                    print(f"   节点数: {data['graphNodes']}")
                    print(f"   边数: {data['graphEdges']}")
                    
                    return data
                else:
                    print(f"❌ 启动失败: {data}")
                    return None
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None


async def test_websocket_stream(thread_id: str):
    """测试WebSocket实时流"""
    print("\n" + "="*60)
    print("📡 测试 6: WebSocket 实时流")
    print("="*60)
    
    try:
        uri = f"{WS_URL}/{thread_id}"
        print(f"连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 发送开始信号
            await websocket.send(json.dumps({
                "action": "start",
                "input": {
                    "topic": "人工智能的未来发展趋势",
                    "max_length": 1000
                }
            }))
            
            # 接收事件
            event_count = 0
            token_count = 0
            start_time = datetime.now()
            
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    event = json.loads(message)
                    
                    event_count += 1
                    
                    event_type = event.get("type", "unknown")
                    
                    if event_type == "connected":
                        print(f"✅ 已连接")
                    elif event_type == "run_started":
                        print(f"▶️ 运行开始")
                    elif event_type == "node_started":
                        node_id = event.get("nodeId", "?")
                        print(f"🔧 节点开始: {node_id}")
                    elif event_type == "token":
                        token_count += 1
                        content = event.get("payload", {}).get("content", "")
                        finished = event.get("payload", {}).get("finished", False)
                        if token_count % 10 == 0:
                            print(f"📝 收到 {token_count} 个Token...")
                        if finished:
                            print(f"✅ Token流完成 (总共 {token_count} 个Token)")
                    elif event_type == "error":
                        print(f"❌ 错误: {event}")
                    elif event_type == "run_completed":
                        print(f"✅ 运行完成")
            
            except asyncio.TimeoutError:
                print(f"⏱️ 超时 (等待30秒无消息)")
            except Exception as e:
                print(f"❌ 接收失败: {e}")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n📊 统计:")
            print(f"   事件数: {event_count}")
            print(f"   Token数: {token_count}")
            print(f"   耗时: {elapsed:.1f}秒")
    
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")


# ============================================================================
# 主测试程序
# ============================================================================

async def main():
    """运行所有测试"""
    print("\n" + "🎯 "*20)
    print("        TenMuses Phase 2 动态工作流测试套件")
    print("🎯 "*20 + "\n")
    
    # 1. 登录
    token = await register_and_login()
    if not token:
        print("\n❌ 登录失败，无法继续")
        return
    
    # 2. 测试编译
    graph = await test_workflow_compilation(token)
    
    # 3. 测试验证
    await test_workflow_validation(token)
    
    # 4. 测试工具库
    await test_list_tools(token)
    
    # 5. 测试模板
    await test_workflow_templates(token)
    
    # 6. 测试执行
    if graph:
        exec_result = await test_workflow_execution(token, graph)
        
        # 7. 测试WebSocket
        if exec_result and exec_result.get('threadId'):
            await test_websocket_stream(exec_result['threadId'])
    
    print("\n" + "✅ "*20)
    print("        所有测试完成")
    print("✅ "*20 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
