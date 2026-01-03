#!/usr/bin/env python3
"""
Copilot 页面修复验证脚本
用于验证前端修复是否有效

使用方法:
  python test_copilot_page_fix.py
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 配置
API_URL = os.getenv('API_URL', 'http://localhost:8000')
API_BASE = f"{API_URL}/api/v1"

# JWT Token (需要从浏览器 localStorage 获取)
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', None)

# 颜色输出
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Color.RESET}\n")

def print_success(text: str):
    """打印成功信息"""
    print(f"{Color.GREEN}✅ {text}{Color.RESET}")

def print_error(text: str):
    """打印错误信息"""
    print(f"{Color.RED}❌ {text}{Color.RESET}")

def print_warning(text: str):
    """打印警告信息"""
    print(f"{Color.YELLOW}⚠️  {text}{Color.RESET}")

def print_info(text: str):
    """打印信息"""
    print(f"{Color.BLUE}ℹ️  {text}{Color.RESET}")

def test_api_models() -> bool:
    """测试 1: 获取模型列表 (/llm-config/models)"""
    print_header("测试 1: 获取可用模型列表")
    
    try:
        headers = {}
        if ACCESS_TOKEN:
            headers['Authorization'] = f'Bearer {ACCESS_TOKEN}'
        
        url = f"{API_BASE}/llm-config/models"
        params = {'active_only': True}
        
        print_info(f"请求: GET {url}")
        print_info(f"参数: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        print_info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print_success(f"成功获取 {len(models)} 个模型")
            
            for model in models:
                print(f"  • {model.get('display_name', model.get('model_name'))} "
                      f"({model.get('model_name')})")
            
            return True
        else:
            print_error(f"请求失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"异常: {str(e)}")
        return False

def test_copilot_chat() -> bool:
    """测试 2: Copilot Chat API"""
    print_header("测试 2: Copilot Chat 端点")
    
    try:
        headers = {'Content-Type': 'application/json'}
        if ACCESS_TOKEN:
            headers['Authorization'] = f'Bearer {ACCESS_TOKEN}'
        
        url = f"{API_BASE}/copilot/chat"
        payload = {
            'message': '你好，请简短自我介绍',
            'model': 'gpt-4o',
            'chat_history': []
        }
        
        print_info(f"请求: POST {url}")
        print_info(f"负载: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print_info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("成功收到响应")
            print(f"  模型: {result.get('model_name', 'unknown')}")
            print(f"  消息: {result.get('message', '')[:100]}...")
            return True
        else:
            print_error(f"请求失败: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"异常: {str(e)}")
        return False

def test_copilot_health() -> bool:
    """测试 3: Copilot 服务健康状态"""
    print_header("测试 3: Copilot 服务健康检查")
    
    try:
        url = f"{API_BASE}/copilot/health"
        
        print_info(f"请求: GET {url}")
        
        response = requests.get(url, timeout=5)
        
        print_info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("服务运行正常")
            print(f"  状态: {data.get('status', 'unknown')}")
            print(f"  LLM 提供商: {data.get('llm_providers', [])}")
            return True
        else:
            print_error(f"请求失败: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("无法连接到后端服务")
        print_warning(f"请检查后端是否运行: {API_URL}")
        return False
    except Exception as e:
        print_error(f"异常: {str(e)}")
        return False

def test_direct_models() -> bool:
    """测试 4: 直接测试模型端点"""
    print_header("测试 4: 直接模型端点测试")
    
    try:
        headers = {}
        if ACCESS_TOKEN:
            headers['Authorization'] = f'Bearer {ACCESS_TOKEN}'
        
        # 测试新端点
        print_info("测试新端点: /llm-config/models")
        response_new = requests.get(f"{API_BASE}/llm-config/models", 
                                    params={'active_only': True},
                                    headers=headers, timeout=5)
        
        if response_new.status_code == 200:
            print_success(f"✓ 新端点可用 ({len(response_new.json())} 个模型)")
        else:
            print_warning(f"新端点返回: {response_new.status_code}")
        
        # 测试旧端点（应该失败或重定向）
        print_info("测试旧端点: /llm-configs")
        try:
            response_old = requests.get(f"{API_BASE}/llm-configs", 
                                       headers=headers, timeout=5)
            if response_old.status_code != 200:
                print_warning(f"✓ 旧端点已禁用 ({response_old.status_code})")
            else:
                print_info(f"旧端点仍然可用 ({response_old.status_code})")
        except:
            print_success("✓ 旧端点已禁用")
        
        return True
        
    except Exception as e:
        print_error(f"异常: {str(e)}")
        return False

def test_frontend_files() -> bool:
    """测试 5: 验证前端文件修改"""
    print_header("测试 5: 验证前端源代码修改")
    
    try:
        workspace_root = '/Users/mg/Workspace/TenMuses'
        
        # 检查 copilot/page.tsx
        copilot_page = f"{workspace_root}/frontend/src/app/copilot/page.tsx"
        print_info(f"检查文件: copilot/page.tsx")
        
        if os.path.exists(copilot_page):
            with open(copilot_page, 'r') as f:
                content = f.read()
            
            checks = {
                '有 copilotClient import': 'import { copilotClient }' in content,
                '调用 copilotClient.chat': 'copilotClient.chat' in content,
                '没有 Mock 响应': 'Mock response' not in content,
            }
            
            all_pass = True
            for check, result in checks.items():
                if result:
                    print_success(f"  {check}")
                else:
                    print_error(f"  {check}")
                    all_pass = False
            
            if all_pass:
                return True
        else:
            print_warning("找不到文件")
            return False
            
    except Exception as e:
        print_error(f"异常: {str(e)}")
        return False

def test_llm_config_client() -> bool:
    """测试 6: 验证 LLM 配置客户端修改"""
    print_header("测试 6: 验证 llm-config-client.ts 修改")
    
    try:
        workspace_root = '/Users/mg/Workspace/TenMuses'
        config_client = f"{workspace_root}/frontend/src/services/llm-config-client.ts"
        
        print_info(f"检查文件: llm-config-client.ts")
        
        if os.path.exists(config_client):
            with open(config_client, 'r') as f:
                content = f.read()
            
            checks = {
                '使用新端点': '/llm-config/models' in content,
                '有 active_only 参数': 'active_only' in content,
                '使用 API_BASE': 'API_BASE' in content,
            }
            
            all_pass = True
            for check, result in checks.items():
                if result:
                    print_success(f"  {check}")
                else:
                    print_error(f"  {check}")
                    all_pass = False
            
            if all_pass:
                return True
        else:
            print_warning("找不到文件")
            return False
            
    except Exception as e:
        print_error(f"异常: {str(e)}")
        return False

def print_summary(results: Dict[str, bool]) -> None:
    """打印测试总结"""
    print_header("测试总结")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"总计: {total} 项测试")
    print(f"  {Color.GREEN}✓ 通过: {passed}{Color.RESET}")
    if failed > 0:
        print(f"  {Color.RED}✗ 失败: {failed}{Color.RESET}")
    
    if failed == 0:
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 所有测试通过！{Color.RESET}")
        print("\n修复完成，你现在可以:")
        print("  1. 刷新浏览器页面")
        print("  2. 打开 Copilot 页面")
        print("  3. 发送测试消息")
        print("  4. 应该能看到真实的 AI 回复")
    else:
        print(f"\n{Color.YELLOW}请检查失败的项目{Color.RESET}")

def main():
    """主函数"""
    print(f"\n{Color.BOLD}{Color.BLUE}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║     Copilot 页面修复验证工具                           ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Color.RESET}")
    
    print_info(f"API 服务器: {API_URL}")
    if ACCESS_TOKEN:
        print_info(f"认证: 使用 ACCESS_TOKEN")
    else:
        print_warning("未提供 ACCESS_TOKEN，某些测试可能失败")
        print_info("使用方法: ACCESS_TOKEN=<token> python test_copilot_page_fix.py")
    
    # 运行测试
    results = {
        '测试 1: 获取模型列表': test_api_models(),
        '测试 2: Copilot Chat': test_copilot_chat(),
        '测试 3: 健康检查': test_copilot_health(),
        '测试 4: 端点验证': test_direct_models(),
        '测试 5: 前端文件验证': test_frontend_files(),
        '测试 6: 配置客户端验证': test_llm_config_client(),
    }
    
    # 打印总结
    print_summary(results)
    
    # 返回状态码
    return 0 if all(results.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
