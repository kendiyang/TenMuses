#!/usr/bin/env python
"""
综合端到端功能测试脚本 - 验证TenMuses后端所有关键功能
"""

import asyncio
import aiohttp
import json
import sys
from uuid import uuid4
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_USER_EMAIL = f"test_{uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_WORKFLOW_TITLE = f"Test Workflow {uuid4().hex[:8]}"

# 测试结果追踪
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(name, status, message=""):
    """记录测试结果"""
    result = {
        "name": name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    results["tests"].append(result)
    
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} {name}: {message}")
    
    if status == "PASS":
        results["passed"] += 1
    else:
        results["failed"] += 1

async def test_health():
    """测试服务器健康状态"""
    try:
        async with aiohttp.ClientSession() as session:
            # 尝试访问需要认证的端点，验证服务器响应
            async with session.get(f"{BASE_URL}/workflows") as resp:
                if resp.status in [200, 401, 403]:  # 200 OK, 401/403 Unauthorized/Forbidden (expected without token)
                    log_test("服务器健康检查", "PASS", f"HTTP {resp.status} (服务器运行正常)")
                    return True
                else:
                    log_test("服务器健康检查", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("服务器健康检查", "FAIL", str(e))
        return False

async def test_user_registration():
    """测试用户注册"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "email": TEST_USER_EMAIL,
                "username": f"testuser_{uuid4().hex[:6]}",
                "password": TEST_USER_PASSWORD
            }
            async with session.post(f"{BASE_URL}/auth/register", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "access_token" in data:
                        log_test("用户注册", "PASS", f"用户创建成功: {payload['email']}")
                        return data.get("access_token")
                    else:
                        log_test("用户注册", "FAIL", "返回数据中没有 access_token")
                        return None
                else:
                    error = await resp.text()
                    log_test("用户注册", "FAIL", f"HTTP {resp.status}: {error[:100]}")
                    return None
    except Exception as e:
        log_test("用户注册", "FAIL", str(e))
        return None

async def test_user_login(email, password):
    """测试用户登录"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"email": email, "password": password}
            async with session.post(f"{BASE_URL}/auth/login", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "access_token" in data:
                        log_test("用户登录", "PASS", f"登录成功")
                        return data.get("access_token")
                    else:
                        log_test("用户登录", "FAIL", "返回数据中没有 access_token")
                        return None
                else:
                    log_test("用户登录", "FAIL", f"HTTP {resp.status}")
                    return None
    except Exception as e:
        log_test("用户登录", "FAIL", str(e))
        return None

async def test_get_current_user(token):
    """测试获取当前用户信息"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BASE_URL}/auth/me", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    log_test("获取当前用户", "PASS", f"用户ID: {data.get('id', 'N/A')[:8]}")
                    return True
                else:
                    log_test("获取当前用户", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("获取当前用户", "FAIL", str(e))
        return False

async def test_create_workflow(token):
    """测试创建工作流"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "title": TEST_WORKFLOW_TITLE,
                "description": "Test workflow for E2E testing",
                "is_public": False,
                "canvas_json": {
                    "nodes": [
                        {"id": "node1", "type": "start", "position": [0, 0]},
                        {"id": "node2", "type": "end", "position": [100, 100]}
                    ],
                    "edges": [
                        {"id": "edge1", "source": "node1", "target": "node2"}
                    ]
                }
            }
            async with session.post(f"{BASE_URL}/workflows", json=payload, headers=headers) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    workflow_id = data.get("id")
                    log_test("创建工作流", "PASS", f"工作流ID: {workflow_id[:8] if workflow_id else 'N/A'}")
                    return workflow_id
                else:
                    error = await resp.text()
                    log_test("创建工作流", "FAIL", f"HTTP {resp.status}: {error[:100]}")
                    return None
    except Exception as e:
        log_test("创建工作流", "FAIL", str(e))
        return None

async def test_get_workflows(token):
    """测试获取工作流列表"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BASE_URL}/workflows", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # 处理两种响应格式：列表或包含workflows的字典
                    if isinstance(data, list):
                        count = len(data)
                    else:
                        count = len(data.get("workflows", []))
                    log_test("获取工作流列表", "PASS", f"获取 {count} 个工作流")
                    return True
                else:
                    log_test("获取工作流列表", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("获取工作流列表", "FAIL", str(e))
        return False

async def test_get_workflow_detail(token, workflow_id):
    """测试获取工作流详情"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BASE_URL}/workflows/{workflow_id}", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    log_test("获取工作流详情", "PASS", f"工作流: {data.get('title', 'N/A')[:30]}")
                    return True
                else:
                    log_test("获取工作流详情", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("获取工作流详情", "FAIL", str(e))
        return False

async def test_update_workflow(token, workflow_id):
    """测试更新工作流"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "title": f"Updated {TEST_WORKFLOW_TITLE}",
                "description": "Updated description"
            }
            async with session.put(f"{BASE_URL}/workflows/{workflow_id}", json=payload, headers=headers) as resp:
                if resp.status == 200:
                    log_test("更新工作流", "PASS", "工作流更新成功")
                    return True
                else:
                    log_test("更新工作流", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("更新工作流", "FAIL", str(e))
        return False

async def test_workspace_overview(token):
    """测试工作空间概览"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BASE_URL}/workspace", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    workflows_count = len(data.get("recent_workflows", []))
                    stats = data.get("statistics", {})
                    log_test("工作空间概览", "PASS", 
                            f"工作流数: {stats.get('total_workflows', 0)}, 最近查看: {workflows_count}")
                    return True
                else:
                    error = await resp.text()
                    log_test("工作空间概览", "FAIL", f"HTTP {resp.status}: {error[:100]}")
                    return False
    except Exception as e:
        log_test("工作空间概览", "FAIL", str(e))
        return False

async def test_delete_workflow(token, workflow_id):
    """测试删除工作流"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.delete(f"{BASE_URL}/workflows/{workflow_id}", headers=headers) as resp:
                if resp.status in [200, 204]:
                    log_test("删除工作流", "PASS", f"工作流已删除")
                    return True
                else:
                    log_test("删除工作流", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("删除工作流", "FAIL", str(e))
        return False

async def test_invalid_token():
    """测试无效令牌"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": "Bearer invalid_token"}
            async with session.get(f"{BASE_URL}/workflows", headers=headers) as resp:
                if resp.status == 401:
                    log_test("无效令牌拒绝", "PASS", "无效令牌被正确拒绝")
                    return True
                else:
                    log_test("无效令牌拒绝", "FAIL", f"预期401，收到HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("无效令牌拒绝", "FAIL", str(e))
        return False

async def test_api_documentation():
    """测试API文档可用性"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/docs") as resp:
                if resp.status == 200:
                    log_test("API文档可用性", "PASS", "Swagger UI 可访问")
                    return True
                else:
                    log_test("API文档可用性", "FAIL", f"HTTP {resp.status}")
                    return False
    except Exception as e:
        log_test("API文档可用性", "FAIL", str(e))
        return False

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("  TenMuses 后端 - 综合端到端功能测试")
    print("="*70 + "\n")
    
    # 健康检查
    await test_health()
    
    # API文档
    await test_api_documentation()
    
    # 无效令牌测试
    await test_invalid_token()
    
    # 用户认证测试
    token = await test_user_registration()
    if not token:
        log_test("后续测试", "FAIL", "注册失败，无法继续")
        return
    
    # 再次测试登录
    login_token = await test_user_login(TEST_USER_EMAIL, TEST_USER_PASSWORD)
    if login_token:
        token = login_token
    
    # 用户信息测试
    await test_get_current_user(token)
    
    # 工作流测试
    workflow_id = await test_create_workflow(token)
    
    if workflow_id:
        await test_get_workflow_detail(token, workflow_id)
        await test_update_workflow(token, workflow_id)
    
    await test_get_workflows(token)
    
    # 工作空间概览测试
    await test_workspace_overview(token)
    
    # 清理 - 删除工作流
    if workflow_id:
        await test_delete_workflow(token, workflow_id)
    
    # 打印总结
    print("\n" + "="*70)
    print("  测试总结")
    print("="*70)
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")
    print(f"📊 总计: {results['passed'] + results['failed']}")
    print(f"✨ 成功率: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")
    print("="*70 + "\n")
    
    # 返回状态码
    return 0 if results['failed'] == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
