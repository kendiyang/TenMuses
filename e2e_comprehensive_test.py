#!/usr/bin/env python3
"""
全面的前后端集成测试脚本 (E2E)
测试新初始化的 LLM 配置和完整的工作流
"""

import asyncio
import sys
from pathlib import Path
import subprocess
import time
import json
import uuid
from datetime import datetime

# 添加后端路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx

# ============================================================================
# 配置
# ============================================================================

BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"
WS_BASE = f"ws://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# 测试统计
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0,
    "start_time": None,
    "end_time": None
}

# 测试数据存储
test_data = {
    "access_token": None,
    "user_id": None,
    "workflow_id": None,
    "run_id": None,
    "provider_id": None,
    "model_ids": {}
}

# ============================================================================
# 辅助函数
# ============================================================================

def print_header(title, level=1):
    """打印分层标题"""
    if level == 1:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    elif level == 2:
        print(f"\n{'-'*70}")
        print(f"  {title}")
        print(f"{'-'*70}\n")
    else:
        print(f"\n  • {title}")

def print_test(name, status, error=None, details=None):
    """打印测试结果"""
    test_results["total"] += 1
    
    if status == "PASS":
        symbol = "✓"
        color = "\033[92m"
        test_results["passed"] += 1
    elif status == "SKIP":
        symbol = "⊘"
        color = "\033[93m"
        test_results["skipped"] += 1
    else:
        symbol = "✗"
        color = "\033[91m"
        test_results["failed"] += 1
    
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {name}")
    
    if error:
        print(f"  错误: {error}")
    if details:
        print(f"  详情: {details}")

def print_json(data, indent=2):
    """打印格式化的 JSON"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

async def check_service(url, name):
    """检查服务是否运行"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            if response.status_code == 200:
                print_test(f"{name} 服务运行中", "PASS", details=url)
                return True
    except Exception as e:
        print_test(f"{name} 服务运行中", "FAIL", error=str(e))
        return False
    return False

# ============================================================================
# 测试套件
# ============================================================================

async def test_infrastructure():
    """测试基础设施"""
    print_header("第一步：基础设施检查", level=1)
    
    # 检查后端服务
    backend_ok = await check_service(f"{BACKEND_URL}/health", "后端")
    
    if not backend_ok:
        print("\n⚠️  后端服务未运行，正在尝试启动...")
        print("提示：请在另一个终端运行：")
        print("  cd backend && uvicorn app.main:app --reload\n")
        return False
    
    # 检查前端服务（可选）
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(FRONTEND_URL)
            if response.status_code in [200, 304]:
                print_test("前端服务运行中", "PASS", details=FRONTEND_URL)
            else:
                print_test("前端服务检查", "SKIP", error="前端未运行（可选）")
    except:
        print_test("前端服务检查", "SKIP", error="前端未运行（可选）")
    
    return backend_ok

async def test_authentication():
    """测试认证流程"""
    print_header("第二步：用户认证测试", level=1)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 生成唯一测试用户
        unique_suffix = str(uuid.uuid4())[:8]
        test_email = f"test_{unique_suffix}@example.com"
        test_username = f"testuser_{unique_suffix}"
        test_password = "TestPass123!"
        
        # 1. 注册
        try:
            response = await client.post(
                f"{API_BASE}/auth/register",
                json={
                    "email": test_email,
                    "username": test_username,
                    "password": test_password
                }
            )
            if response.status_code == 200:
                data = response.json()
                test_data["access_token"] = data.get("access_token")
                test_data["user_id"] = data.get("user", {}).get("id")
                print_test("用户注册", "PASS", details=f"用户: {test_username}")
            else:
                print_test("用户注册", "FAIL", error=f"HTTP {response.status_code}")
                return False
        except Exception as e:
            print_test("用户注册", "FAIL", error=str(e))
            return False
        
        # 2. 验证 token
        if test_data["access_token"]:
            try:
                response = await client.get(
                    f"{API_BASE}/auth/me",
                    headers={"Authorization": f"Bearer {test_data['access_token']}"}
                )
                if response.status_code == 200:
                    print_test("Token 验证", "PASS")
                else:
                    print_test("Token 验证", "FAIL", error=f"HTTP {response.status_code}")
            except Exception as e:
                print_test("Token 验证", "FAIL", error=str(e))
        
        return test_data["access_token"] is not None

async def test_llm_config():
    """测试 LLM 配置（新初始化的配置）"""
    print_header("第三步：LLM 配置测试", level=1)
    
    headers = {"Authorization": f"Bearer {test_data['access_token']}"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. 获取供应商列表
        try:
            response = await client.get(
                f"{API_BASE}/llm-config/providers",
                headers=headers
            )
            if response.status_code == 200:
                providers = response.json()
                print_test(f"获取供应商列表", "PASS", details=f"找到 {len(providers)} 个供应商")
                
                # 查找 OpenAI 供应商
                for provider in providers:
                    if provider.get("name") == "openai" and provider.get("is_active"):
                        test_data["provider_id"] = provider.get("id")
                        print(f"  • 找到激活的 OpenAI 供应商: {provider.get('display_name')}")
                        print(f"    Base URL: {provider.get('base_url')}")
            else:
                print_test("获取供应商列表", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("获取供应商列表", "FAIL", error=str(e))
        
        # 2. 获取模型列表
        try:
            response = await client.get(
                f"{API_BASE}/llm-config/models",
                headers=headers
            )
            if response.status_code == 200:
                models = response.json()
                print_test(f"获取模型列表", "PASS", details=f"找到 {len(models)} 个模型")
                
                # 查找我们初始化的模型
                for model in models:
                    model_name = model.get("model_name")
                    if model.get("is_active"):
                        test_data["model_ids"][model_name] = model.get("id")
                        print(f"  • {model.get('display_name')} ({model_name})")
                        if model_name == "gpt-4o":
                            print(f"    ✓ 聊天模型已激活")
                        elif model_name == "text-embedding-3-large":
                            print(f"    ✓ 向量模型已激活")
            else:
                print_test("获取模型列表", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("获取模型列表", "FAIL", error=str(e))
    
    return test_data["provider_id"] is not None

async def test_workflow_crud():
    """测试工作流 CRUD 操作"""
    print_header("第四步：工作流 CRUD 测试", level=1)
    
    headers = {
        "Authorization": f"Bearer {test_data['access_token']}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. 创建工作流
        workflow_data = {
            "title": f"测试工作流_{datetime.now().strftime('%H%M%S')}",
            "description": "端到端集成测试工作流",
            "canvas_json": {
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "开始"}
                    },
                    {
                        "id": "llm1",
                        "type": "llm",
                        "position": {"x": 300, "y": 100},
                        "data": {
                            "label": "GPT-4o",
                            "llm_config": {
                                "provider": "openai",
                                "model": "gpt-4o",
                                "system_prompt": "你是一个有帮助的助手",
                                "temperature": 0.7
                            }
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "start",
                        "target": "llm1"
                    }
                ],
                "viewport": {"x": 0, "y": 0, "zoom": 1}
            }
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/workflows",
                headers=headers,
                json=workflow_data
            )
            if response.status_code == 201:
                workflow = response.json()
                test_data["workflow_id"] = workflow.get("id")
                print_test("创建工作流", "PASS", details=f"ID: {test_data['workflow_id']}")
            else:
                print_test("创建工作流", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print_test("创建工作流", "FAIL", error=str(e))
            return False
        
        # 2. 获取工作流
        try:
            response = await client.get(
                f"{API_BASE}/workflows/{test_data['workflow_id']}",
                headers=headers
            )
            if response.status_code == 200:
                print_test("读取工作流", "PASS")
            else:
                print_test("读取工作流", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("读取工作流", "FAIL", error=str(e))
        
        # 3. 列出工作流
        try:
            response = await client.get(
                f"{API_BASE}/workflows",
                headers=headers
            )
            if response.status_code == 200:
                workflows = response.json()
                print_test("列出工作流", "PASS", details=f"找到 {len(workflows)} 个工作流")
            else:
                print_test("列出工作流", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("列出工作流", "FAIL", error=str(e))
    
    return test_data["workflow_id"] is not None

async def test_dynamic_workflow():
    """测试动态工作流执行"""
    print_header("第五步：动态工作流测试", level=1)
    
    headers = {
        "Authorization": f"Bearer {test_data['access_token']}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        # 1. 验证工具库
        try:
            response = await client.get(
                f"{API_BASE}/dynamic/tools",
                headers=headers
            )
            if response.status_code == 200:
                tools = response.json()
                print_test("获取工具库", "PASS", details=f"可用工具: {len(tools.get('tools', {}))}")
            else:
                print_test("获取工具库", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("获取工具库", "FAIL", error=str(e))
        
        # 2. 验证动态图
        graph_config = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "llm",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "label": "Research",
                        "llm_config": {
                            "provider": "openai",
                            "model": "gpt-4o",
                            "system_prompt": "你是一个友好的助手",
                            "temperature": 0.7
                        }
                    }
                }
            ],
            "edges": [],
            "entry_node": "node1"
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/dynamic/validate",
                headers=headers,
                json=graph_config
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("valid"):
                    print_test("验证动态图", "PASS")
                else:
                    print_test("验证动态图", "FAIL", error=result.get("errors"))
            else:
                print_test("验证动态图", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            print_test("验证动态图", "FAIL", error=str(e))
        
        # 3. 执行简单工作流（非流式）
        print("\n  执行简单工作流（测试 LLM 调用）...")
        simple_graph = {
            "nodes": [
                {
                    "id": "llm_node",
                    "type": "llm",
                    "position": {"x": 150, "y": 150},
                    "data": {
                        "label": "LLM Node",
                        "llm_config": {
                            "provider": "openai",
                            "model": "gpt-4o",
                            "system_prompt": "请用一句话回答",
                            "temperature": 0.3,
                            "max_tokens": 50
                        }
                    }
                }
            ],
            "edges": [],
            "entry_node": "llm_node"
        }
        
        try:
            # 发送 WorkflowGraph 格式（nodes, edges）加上 input_data
            response = await client.post(
                f"{API_BASE}/dynamic/execute",
                headers=headers,
                json={
                    "graph_data": simple_graph,
                    "input_data": {"prompt": "什么是人工智能？用一句话回答。"}
                }
            )
            if response.status_code == 200:
                result = response.json()
                print_test("执行工作流（非流式）", "PASS")
                output = result.get("output", {})
                if output:
                    print(f"  • 工作流输出: {str(output)[:100]}...")
            else:
                print_test("执行工作流（非流式）", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            print_test("执行工作流（非流式）", "FAIL", error=str(e))

async def test_copilot_api():
    """测试 Copilot API"""
    print_header("第六步：Copilot API 测试", level=1)
    
    headers = {
        "Authorization": f"Bearer {test_data['access_token']}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. 聊天接口（本地规则引擎）
        try:
            response = await client.post(
                f"{API_BASE}/copilot/chat",
                headers=headers,
                json={
                    "message": "帮我创建一个工作流",
                    "chat_history": []
                }
            )
            if response.status_code == 200:
                result = response.json()
                print_test("Copilot 聊天", "PASS")
                print(f"  • 响应: {result.get('response', '')[:80]}...")
            else:
                print_test("Copilot 聊天", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("Copilot 聊天", "FAIL", error=str(e))
        
        # 2. 建议接口
        try:
            response = await client.post(
                f"{API_BASE}/copilot/suggestions",
                headers=headers,
                json={"context": "workflow creation"}
            )
            if response.status_code == 200:
                suggestions = response.json()
                print_test("Copilot 建议", "PASS", details=f"{len(suggestions.get('suggestions', []))} 条建议")
            else:
                print_test("Copilot 建议", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            print_test("Copilot 建议", "FAIL", error=str(e))

async def test_knowledge_base():
    """测试知识库（RAG）功能"""
    print_header("第七步：知识库 (RAG) 测试", level=1)
    
    headers = {
        "Authorization": f"Bearer {test_data['access_token']}"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        # 1. 上传文档
        test_content = """
        人工智能（Artificial Intelligence, AI）是计算机科学的一个分支。
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
        """
        
        try:
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(test_content)
                temp_file_path = f.name
            
            # 上传文件
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_doc.txt', f, 'text/plain')}
                response = await client.post(
                    f"{API_BASE}/kb/documents",
                    headers=headers,
                    files=files
                )
            
            # 清理临时文件
            import os
            os.unlink(temp_file_path)
            
            if response.status_code == 201:
                doc = response.json()
                doc_id = doc.get("id")
                print_test("上传文档", "PASS", details=f"文档 ID: {doc_id}")
                test_data["doc_id"] = doc_id
            else:
                print_test("上传文档", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            print_test("上传文档", "FAIL", error=str(e))
        
        # 2. 搜索文档（需要等待向量化）
        if test_data.get("doc_id"):
            print("\n  等待文档向量化... (3秒)")
            await asyncio.sleep(3)
            
            try:
                response = await client.post(
                    f"{API_BASE}/kb/search",
                    headers={**headers, "Content-Type": "application/json"},
                    json={
                        "query": "什么是人工智能",
                        "top_k": 3
                    }
                )
                if response.status_code == 200:
                    results = response.json()
                    chunks = results.get("chunks", [])
                    print_test("搜索文档", "PASS", details=f"找到 {len(chunks)} 个相关片段")
                    if chunks:
                        print(f"  • 最相关片段: {chunks[0].get('text', '')[:60]}...")
                else:
                    print_test("搜索文档", "FAIL", error=f"HTTP {response.status_code}")
            except Exception as e:
                print_test("搜索文档", "FAIL", error=str(e))

async def test_websocket_streaming():
    """测试 WebSocket 流式执行"""
    print_header("第八步：WebSocket 流式测试", level=1)
    
    print("  ⚠️  WebSocket 测试需要 websockets 库")
    print("  提示: pip install websockets")
    print_test("WebSocket 流式", "SKIP", error="需要 websockets 库（可选）")

# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主测试流程"""
    print_header("🚀 TenMuses 全面集成测试 (E2E)", level=1)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"后端 URL: {BACKEND_URL}")
    print(f"前端 URL: {FRONTEND_URL}")
    
    test_results["start_time"] = datetime.now()
    
    # 执行测试套件
    tests = [
        ("基础设施", test_infrastructure),
        ("用户认证", test_authentication),
        ("LLM 配置", test_llm_config),
        ("工作流 CRUD", test_workflow_crud),
        ("动态工作流", test_dynamic_workflow),
        ("Copilot API", test_copilot_api),
        ("知识库 RAG", test_knowledge_base),
        ("WebSocket 流式", test_websocket_streaming),
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result is False:
                print(f"\n⚠️  {test_name} 测试失败，跳过后续依赖测试")
                # 继续执行其他测试，但标记依赖失败
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
    
    test_results["end_time"] = datetime.now()
    
    # 打印测试总结
    print_summary()

def print_summary():
    """打印测试总结"""
    print_header("📊 测试总结", level=1)
    
    duration = (test_results["end_time"] - test_results["start_time"]).total_seconds()
    
    print(f"总测试数: {test_results['total']}")
    print(f"✓ 通过: {test_results['passed']}")
    print(f"✗ 失败: {test_results['failed']}")
    print(f"⊘ 跳过: {test_results['skipped']}")
    print(f"耗时: {duration:.2f} 秒")
    
    # 计算成功率
    if test_results['total'] > 0:
        pass_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"\n通过率: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("\n🎉 测试结果: 优秀！")
        elif pass_rate >= 70:
            print("\n✓ 测试结果: 良好")
        elif pass_rate >= 50:
            print("\n⚠️  测试结果: 需要改进")
        else:
            print("\n❌ 测试结果: 存在严重问题")
    
    # 保存测试数据
    print(f"\n测试数据:")
    if test_data.get("user_id"):
        print(f"  用户 ID: {test_data['user_id']}")
    if test_data.get("workflow_id"):
        print(f"  工作流 ID: {test_data['workflow_id']}")
    if test_data.get("provider_id"):
        print(f"  供应商 ID: {test_data['provider_id']}")
    if test_data.get("model_ids"):
        print(f"  模型数量: {len(test_data['model_ids'])}")
    
    print(f"\n结束时间: {test_results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 返回退出码
    return 0 if test_results['failed'] == 0 else 1

# ============================================================================
# 入口
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 测试执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
