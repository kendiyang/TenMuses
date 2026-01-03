#!/usr/bin/env python3
"""
测试 Copilot LLM 集成

验证 Copilot 聊天功能是否正确调用真实的 LLM
"""

import requests
import json
import sys

# 配置
API_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "test@example.com",
    "password": "testpass123"
}

def login():
    """登录获取 token"""
    print("🔐 登录中...")
    response = requests.post(
        f"{API_URL}/auth/login",
        data={
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ 登录成功")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_chat(token):
    """测试聊天功能"""
    print("\n💬 测试 Copilot 聊天...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试消息
    test_message = "请简单介绍一下什么是 LangGraph 工作流？"
    
    payload = {
        "message": test_message,
        "model": "local-smart",
        "context": {},
        "chat_history": []
    }
    
    print(f"📤 发送消息: {test_message}")
    
    try:
        response = requests.post(
            f"{API_URL}/copilot/chat",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 收到回复:")
            print(f"📝 {result['message'][:200]}...")
            
            # 检查回复是否像是 LLM 生成的（而不是简单的规则回复）
            reply = result['message']
            if len(reply) > 100 and any(word in reply for word in ['LangGraph', '工作流', '节点', '图']):
                print("✨ 回复看起来是由真实 LLM 生成的！")
                return True
            else:
                print("⚠️  回复可能是回退响应，而非 LLM 生成")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_workflow_suggestion(token):
    """测试工作流建议"""
    print("\n🔧 测试工作流建议...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "description": "我需要一个处理用户反馈的工作流",
        "complexity": "medium",
        "model": "local-smart"
    }
    
    print(f"📤 请求工作流建议: {payload['description']}")
    
    try:
        response = requests.post(
            f"{API_URL}/copilot/suggest/workflow",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            workflows = result.get('workflows', [])
            print(f"✅ 收到 {len(workflows)} 个工作流建议")
            
            if workflows:
                wf = workflows[0]
                print(f"📋 第一个建议: {wf['name']}")
                print(f"   描述: {wf['description']}")
                print(f"   节点数: {len(wf.get('nodes', []))}")
                return True
            else:
                print("⚠️  没有收到工作流建议")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试流程"""
    print("=" * 60)
    print("🧪 Copilot LLM 集成测试")
    print("=" * 60)
    
    # 登录
    token = login()
    if not token:
        print("\n❌ 无法登录，测试终止")
        sys.exit(1)
    
    # 测试聊天
    chat_ok = test_chat(token)
    
    # 测试工作流建议
    suggestion_ok = test_workflow_suggestion(token)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结:")
    print(f"   聊天功能: {'✅ 通过' if chat_ok else '❌ 失败'}")
    print(f"   工作流建议: {'✅ 通过' if suggestion_ok else '❌ 失败'}")
    print("=" * 60)
    
    if chat_ok and suggestion_ok:
        print("\n🎉 所有测试通过！Copilot 已正确集成 LLM")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查日志")
        sys.exit(1)

if __name__ == "__main__":
    main()
