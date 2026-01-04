#!/usr/bin/env python3
"""
快速登录脚本 - 获取测试用户的访问令牌
"""
import requests
import json

API_URL = "http://localhost:8000"

def register_or_login():
    """注册或登录测试用户"""
    
    # 测试用户信息
    test_user = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    print("🔐 尝试登录...")
    
    # 先尝试登录
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            user = data["user"]
            print(f"✅ 登录成功!")
            print(f"👤 用户: {user['username']} ({user['email']})")
            print(f"🔑 Token: {token}")
            print(f"\n📋 在浏览器控制台执行以下命令:")
            print(f"localStorage.setItem('accessToken', '{token}')")
            return token
    except Exception as e:
        print(f"⚠️  登录失败，尝试注册...")
    
    # 如果登录失败，尝试注册
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json=test_user
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            token = data["access_token"]
            user = data["user"]
            print(f"✅ 注册成功!")
            print(f"👤 用户: {user['username']} ({user['email']})")
            print(f"🔑 Token: {token}")
            print(f"\n📋 在浏览器控制台执行以下命令:")
            print(f"localStorage.setItem('accessToken', '{token}')")
            return token
        else:
            print(f"❌ 注册失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

if __name__ == "__main__":
    register_or_login()
