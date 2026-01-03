#!/usr/bin/env python3
"""
测试 LLM 配置错误信息

验证当没有正确配置 LLM 时，是否能给出清晰的错误提示
"""

import requests
import json

# 配置
API_URL = "http://localhost:8000/api/v1"

def test_without_auth():
    """测试未登录的聊天请求"""
    print("=" * 60)
    print("🧪 测试 1: 未登录状态")
    print("=" * 60)
    
    payload = {
        "message": "你好",
        "model": "local-smart",
        "context": {},
        "chat_history": []
    }
    
    response = requests.post(
        f"{API_URL}/copilot/chat",
        json=payload
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_with_auth():
    """测试已登录的聊天请求"""
    print("=" * 60)
    print("🧪 测试 2: 已登录状态（需要有效的 LLM 配置）")
    print("=" * 60)
    
    # 先登录
    login_response = requests.post(
        f"{API_URL}/auth/login",
        data={
            "username": "yangqx401@gmail.com",
            "password": "12345678"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ 登录成功")
    
    # 发送聊天请求
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": "什么是 LangGraph？",
        "model": "local-smart",
        "context": {},
        "chat_history": []
    }
    
    print(f"\n📤 发送消息: {payload['message']}")
    
    response = requests.post(
        f"{API_URL}/copilot/chat",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"\n状态码: {response.status_code}")
    result = response.json()
    print(f"\n📝 响应消息:")
    print(result.get('message', ''))
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔧 LLM 配置错误信息测试")
    print("=" * 60)
    print()
    
    # 测试未登录
    test_without_auth()
    
    # 测试已登录
    test_with_auth()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
