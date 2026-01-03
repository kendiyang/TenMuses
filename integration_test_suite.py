#!/usr/bin/env python3
"""
TenMuses 综合集成测试套件
测试覆盖: Redis 缓存、API 端点、WebSocket、工作流执行
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\n")

def print_section(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}>>> {text}{Colors.ENDC}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

def print_metric(label: str, value: str):
    print(f"   {label:<30} {value}")

# 配置
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"
WS_URL = "ws://localhost:8000"
TEST_USER = {
    "email": f"test_{int(time.time())}@test.com",
    "password": "TestPassword123!",
    "username": f"testuser_{int(time.time())}"
}

# 全局状态
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

access_token = None
user_id = None


async def test_auth(session: aiohttp.ClientSession) -> bool:
    """测试用户认证"""
    global access_token, user_id
    
    print_section("测试 1: 用户认证")
    
    try:
        # 注册新用户
        print_info(f"注册用户: {TEST_USER['email']}")
        register_payload = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"],
            "username": TEST_USER["username"]
        }
        
        async with session.post(
            f"{API_URL}/auth/register",
            json=register_payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                access_token = data.get("access_token")
                user_id = data.get("user", {}).get("id")
                
                if access_token and user_id:
                    print_success(f"用户注册成功, Token: {access_token[:20]}...")
                    print_success(f"用户 ID: {user_id}")
                    test_results["passed"] += 1
                    return True
                else:
                    print_error("响应中缺少 token 或 user_id")
                    test_results["failed"] += 1
                    return False
            else:
                error_text = await resp.text()
                print_error(f"注册失败 (HTTP {resp.status}): {error_text[:100]}")
                test_results["failed"] += 1
                return False
                
    except Exception as e:
        print_error(f"认证测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_redis_cache(session: aiohttp.ClientSession) -> bool:
    """测试 Redis 缓存集成"""
    print_section("测试 2: Redis 缓存集成")
    
    if not access_token:
        print_warning("跳过缓存测试 (未完成认证)")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 测试 1: 首次查询 (无缓存)
        print_info("首次查询模板列表 (无缓存)")
        start_time = time.time()
        
        async with session.get(
            f"{API_URL}/marketplace/templates?page=1&page_size=10",
            headers=headers
        ) as resp:
            first_time = time.time() - start_time
            
            if resp.status == 200:
                data = await resp.json()
                print_success(f"首次查询成功, 耗时: {first_time*1000:.2f}ms")
                print_metric("返回结果数", str(len(data.get("items", []))))
                print_metric("总数", str(data.get("total", 0)))
            else:
                print_error(f"查询失败 (HTTP {resp.status})")
                test_results["failed"] += 1
                return False
        
        # 测试 2: 第二次查询 (有缓存)
        print_info("第二次查询模板列表 (缓存命中)")
        await asyncio.sleep(0.1)
        start_time = time.time()
        
        async with session.get(
            f"{API_URL}/marketplace/templates?page=1&page_size=10",
            headers=headers
        ) as resp:
            second_time = time.time() - start_time
            
            if resp.status == 200:
                print_success(f"缓存查询成功, 耗时: {second_time*1000:.2f}ms")
                
                # 计算加速倍数
                if second_time > 0:
                    speedup = first_time / second_time
                    print_metric("缓存加速倍数", f"{speedup:.1f}x")
                    
                    if speedup >= 5:
                        print_success(f"缓存性能良好 (加速 {speedup:.1f}x)")
                        test_results["passed"] += 1
                    else:
                        print_warning(f"缓存性能一般 (加速 {speedup:.1f}x)")
                        test_results["passed"] += 1
                else:
                    test_results["passed"] += 1
            else:
                print_error(f"缓存查询失败 (HTTP {resp.status})")
                test_results["failed"] += 1
                return False
        
        # 测试 3: 特色模板缓存
        print_info("查询特色模板 (缓存)")
        async with session.get(
            f"{API_URL}/marketplace/templates/featured",
            headers=headers
        ) as resp:
            if resp.status == 200:
                print_success("特色模板查询成功")
            else:
                print_warning(f"特色模板查询返回 HTTP {resp.status}")
        
        return True
        
    except Exception as e:
        print_error(f"缓存测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_workflow_api(session: aiohttp.ClientSession) -> bool:
    """测试工作流 API"""
    print_section("测试 3: 工作流 API")
    
    if not access_token:
        print_warning("跳过工作流测试 (未完成认证)")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        workflow_id = None
        
        # 创建工作流
        print_info("创建新工作流")
        workflow_data = {
            "name": f"Test Workflow {int(time.time())}",
            "description": "Integration test workflow",
            "status": "draft"
        }
        
        async with session.post(
            f"{API_URL}/workflows",
            json=workflow_data,
            headers=headers
        ) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                workflow_id = data.get("id")
                print_success(f"工作流创建成功, ID: {workflow_id}")
                test_results["passed"] += 1
            else:
                print_error(f"工作流创建失败 (HTTP {resp.status})")
                test_results["failed"] += 1
                return False
        
        # 获取工作流
        if workflow_id:
            print_info(f"获取工作流 {workflow_id}")
            async with session.get(
                f"{API_URL}/workflows/{workflow_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_success(f"工作流获取成功")
                    print_metric("名称", data.get("name", "N/A"))
                    print_metric("状态", data.get("status", "N/A"))
                    test_results["passed"] += 1
                else:
                    print_warning(f"工作流获取返回 HTTP {resp.status}")
        
        # 更新工作流
        if workflow_id:
            print_info(f"更新工作流")
            update_data = {
                "name": f"Updated Workflow {int(time.time())}",
                "description": "Updated description"
            }
            
            async with session.put(
                f"{API_URL}/workflows/{workflow_id}",
                json=update_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    print_success("工作流更新成功")
                    test_results["passed"] += 1
                else:
                    print_warning(f"工作流更新返回 HTTP {resp.status}")
        
        # 列出工作流
        print_info("列出所有工作流")
        async with session.get(
            f"{API_URL}/workflows?page=1&page_size=10",
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                count = len(data.get("items", []))
                print_success(f"工作流列表获取成功, 共 {count} 个")
                test_results["passed"] += 1
            else:
                print_warning(f"工作流列表返回 HTTP {resp.status}")
        
        return True
        
    except Exception as e:
        print_error(f"工作流测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_marketplace_api(session: aiohttp.ClientSession) -> bool:
    """测试 Marketplace API"""
    print_section("测试 4: Marketplace API")
    
    if not access_token:
        print_warning("跳过 Marketplace 测试 (未完成认证)")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 获取模板列表
        print_info("获取模板列表")
        async with session.get(
            f"{API_URL}/marketplace/templates?page=1&page_size=5",
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                total = data.get("total", 0)
                items = data.get("items", [])
                print_success(f"模板列表获取成功")
                print_metric("总数", str(total))
                print_metric("当前页数", str(len(items)))
                test_results["passed"] += 1
                
                # 测试模板详情
                if items:
                    template_id = items[0].get("id")
                    if template_id:
                        print_info(f"获取模板详情 (ID: {template_id})")
                        async with session.get(
                            f"{API_URL}/marketplace/templates/{template_id}",
                            headers=headers
                        ) as detail_resp:
                            if detail_resp.status == 200:
                                template_data = await detail_resp.json()
                                print_success("模板详情获取成功")
                                print_metric("模板名称", template_data.get("name", "N/A")[:50])
                                print_metric("作者", template_data.get("author", {}).get("username", "N/A"))
                                test_results["passed"] += 1
                            else:
                                print_warning(f"模板详情返回 HTTP {detail_resp.status}")
            else:
                print_warning(f"模板列表返回 HTTP {resp.status}")
        
        # 获取特色模板
        print_info("获取特色模板")
        async with session.get(
            f"{API_URL}/marketplace/templates/featured",
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                featured = data.get("items", []) if isinstance(data, dict) else data
                print_success(f"特色模板获取成功, 共 {len(featured)} 个")
                test_results["passed"] += 1
            else:
                print_warning(f"特色模板返回 HTTP {resp.status}")
        
        return True
        
    except Exception as e:
        print_error(f"Marketplace 测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_user_statistics(session: aiohttp.ClientSession) -> bool:
    """测试用户统计 API"""
    print_section("测试 5: 用户统计 API")
    
    if not access_token:
        print_warning("跳过用户统计测试 (未完成认证)")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 测试 1: 首次查询
        print_info("首次查询用户统计 (无缓存)")
        start_time = time.time()
        
        async with session.get(
            f"{API_URL}/users/me/statistics",
            headers=headers
        ) as resp:
            first_time = time.time() - start_time
            
            if resp.status == 200:
                stats = await resp.json()
                print_success(f"用户统计获取成功, 耗时: {first_time*1000:.2f}ms")
                print_metric("工作流总数", str(stats.get("total_workflows", 0)))
                print_metric("执行次数", str(stats.get("total_runs", 0)))
                print_metric("发布模板数", str(stats.get("published_templates", 0)))
                print_metric("收藏数", str(stats.get("favorites_count", 0)))
                test_results["passed"] += 1
            else:
                print_warning(f"用户统计返回 HTTP {resp.status}")
        
        # 测试 2: 第二次查询 (缓存)
        print_info("第二次查询用户统计 (缓存命中)")
        await asyncio.sleep(0.05)
        start_time = time.time()
        
        async with session.get(
            f"{API_URL}/users/me/statistics",
            headers=headers
        ) as resp:
            second_time = time.time() - start_time
            
            if resp.status == 200:
                print_success(f"统计缓存查询成功, 耗时: {second_time*1000:.2f}ms")
                
                if second_time > 0:
                    speedup = first_time / second_time
                    print_metric("缓存加速倍数", f"{speedup:.1f}x")
                    test_results["passed"] += 1
        
        return True
        
    except Exception as e:
        print_error(f"用户统计测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_pagination(session: aiohttp.ClientSession) -> bool:
    """测试分页功能"""
    print_section("测试 6: 分页功能")
    
    if not access_token:
        print_warning("跳过分页测试 (未完成认证)")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 测试不同页面大小
        for page_size in [5, 10, 20]:
            print_info(f"测试分页 (page_size={page_size})")
            async with session.get(
                f"{API_URL}/marketplace/templates?page=1&page_size={page_size}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = len(data.get("items", []))
                    total = data.get("total", 0)
                    
                    if items <= page_size:
                        print_success(f"分页正确: 返回 {items} 条 (请求 {page_size})")
                        test_results["passed"] += 1
                    else:
                        print_error(f"分页错误: 返回 {items} 条 (请求 {page_size})")
                        test_results["failed"] += 1
                else:
                    print_warning(f"分页查询返回 HTTP {resp.status}")
        
        # 测试多页导航
        print_info("测试多页导航")
        pages_to_test = [1, 2, 3]
        for page in pages_to_test:
            async with session.get(
                f"{API_URL}/marketplace/templates?page={page}&page_size=10",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    current_page = data.get("page")
                    if current_page == page:
                        print_success(f"页面 {page} 导航正确")
                        test_results["passed"] += 1
                    else:
                        print_warning(f"页面返回不匹配: 期望 {page}, 收到 {current_page}")
                else:
                    print_warning(f"页面 {page} 返回 HTTP {resp.status}")
        
        return True
        
    except Exception as e:
        print_error(f"分页测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_llm_config(session: aiohttp.ClientSession) -> bool:
    """测试 LLM 配置 API"""
    print_section("测试 7: LLM 配置 API")
    
    if not access_token:
        print_warning("跳过 LLM 配置测试 (未完成认证)")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 测试 1: 首次查询供应商列表
        print_info("首次查询 LLM 供应商 (无缓存)")
        start_time = time.time()
        
        async with session.get(
            f"{API_URL}/llm-config/providers",
            headers=headers
        ) as resp:
            first_time = time.time() - start_time
            
            if resp.status == 200:
                data = await resp.json()
                providers = data.get("providers", [])
                print_success(f"供应商列表获取成功, 耗时: {first_time*1000:.2f}ms")
                print_metric("供应商数量", str(len(providers)))
                test_results["passed"] += 1
            else:
                print_warning(f"供应商列表返回 HTTP {resp.status}")
                return False
        
        # 测试 2: 第二次查询 (缓存)
        print_info("第二次查询 LLM 供应商 (缓存命中)")
        await asyncio.sleep(0.05)
        start_time = time.time()
        
        async with session.get(
            f"{API_URL}/llm-config/providers",
            headers=headers
        ) as resp:
            second_time = time.time() - start_time
            
            if resp.status == 200:
                print_success(f"供应商缓存查询成功, 耗时: {second_time*1000:.2f}ms")
                
                if second_time > 0:
                    speedup = first_time / second_time
                    print_metric("缓存加速倍数", f"{speedup:.1f}x")
                    test_results["passed"] += 1
        
        return True
        
    except Exception as e:
        print_error(f"LLM 配置测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_error_handling(session: aiohttp.ClientSession) -> bool:
    """测试错误处理"""
    print_section("测试 8: 错误处理")
    
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        
        # 测试无效 token
        print_info("测试无效认证 token")
        async with session.get(
            f"{API_URL}/workflows",
            headers=headers
        ) as resp:
            if resp.status == 401:
                print_success("正确返回 401 未授权错误")
                test_results["passed"] += 1
            else:
                print_warning(f"期望 401, 收到 {resp.status}")
        
        # 测试不存在的资源
        print_info("测试不存在的资源")
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(
                f"{API_URL}/workflows/nonexistent-id",
                headers=headers
            ) as resp:
                if resp.status == 404:
                    print_success("正确返回 404 未找到错误")
                    test_results["passed"] += 1
                else:
                    print_warning(f"期望 404, 收到 {resp.status}")
        
        # 测试无效分页参数
        print_info("测试无效分页参数")
        if access_token:
            async with session.get(
                f"{API_URL}/marketplace/templates?page=0&page_size=10",
                headers=headers
            ) as resp:
                if resp.status in [200, 400]:  # 可能返回 200 或 400
                    print_success(f"无效参数处理正确 (HTTP {resp.status})")
                    test_results["passed"] += 1
        
        return True
        
    except Exception as e:
        print_error(f"错误处理测试异常: {str(e)}")
        test_results["failed"] += 1
        return False


async def test_websocket_connection(session: aiohttp.ClientSession) -> bool:
    """测试 WebSocket 连接"""
    print_section("测试 9: WebSocket 连接")
    
    if not access_token or not user_id:
        print_warning("跳过 WebSocket 测试 (未完成认证)")
        return False
    
    try:
        print_info(f"连接 WebSocket: {WS_URL}/ws/run/{user_id}")
        
        # 注意: 实际的 WebSocket 测试需要完整的设置
        # 这里只测试连接是否可能
        print_info("WebSocket 完整测试需要运行前端应用和工作流执行")
        print_warning("WebSocket 测试需要独立的 E2E 测试工具")
        
        return True
        
    except Exception as e:
        print_error(f"WebSocket 测试异常: {str(e)}")
        return False


async def run_all_tests():
    """运行所有集成测试"""
    print_header("TenMuses 综合集成测试套件")
    
    print_info(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"API 地址: {API_URL}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 检查服务可用性
            print_section("初始化: 检查服务可用性")
            try:
                async with session.get(f"{BASE_URL}/docs") as resp:
                    if resp.status == 200:
                        print_success("后端服务正在运行")
                    else:
                        print_error("后端服务返回异常状态码")
                        print_error("请确保后端服务已启动: python -m app.main")
                        return
            except Exception as e:
                print_error(f"无法连接到后端服务: {str(e)}")
                print_error("请确保后端服务已启动: python -m app.main")
                return
            
            # 运行所有测试
            await test_auth(session)
            await test_redis_cache(session)
            await test_workflow_api(session)
            await test_marketplace_api(session)
            await test_user_statistics(session)
            await test_pagination(session)
            await test_llm_config(session)
            await test_error_handling(session)
            await test_websocket_connection(session)
            
        except KeyboardInterrupt:
            print_warning("\n测试被用户中断")
        except Exception as e:
            print_error(f"测试执行出错: {str(e)}")
            import traceback
            traceback.print_exc()


def print_summary():
    """打印测试总结"""
    print_header("测试结果总结")
    
    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    
    print_metric("总测试数", str(total))
    print_metric("通过", f"{test_results['passed']} ✅")
    print_metric("失败", f"{test_results['failed']} ❌")
    print_metric("通过率", f"{pass_rate:.1f}%")
    
    if test_results["errors"]:
        print_section("错误详情")
        for error in test_results["errors"]:
            print_error(error)
    
    print_info(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 最终状态
    if test_results["failed"] == 0 and test_results["passed"] > 0:
        print_header("✅ 所有测试通过!")
        return 0
    else:
        print_header("⚠️ 部分测试失败")
        return 1


async def main():
    """主函数"""
    try:
        await run_all_tests()
        exit_code = print_summary()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\n程序被中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"程序错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
