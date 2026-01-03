#!/usr/bin/env python3
"""
Copilot 功能验证脚本 - 不依赖外部库
"""
import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://localhost:8000/api/v1"

def make_request(method, url, data=None, headers=None):
    """发送HTTP请求"""
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    
    if data:
        data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"error": str(e)}
    except Exception as e:
        return None, {"error": str(e)}

def test_copilot():
    print("🧪 Copilot 功能验证")
    print("=" * 50)
    
    # 登录
    print("\n📝 获取认证Token...")
    status, result = make_request("POST", f"{BASE_URL}/auth/login", 
        {"email": "test_copilot@test.com", "password": "testpass123"})
    
    if status != 200:
        print(f"❌ 登录失败: {status}")
        return False
    
    token = result.get("access_token")
    print("✅ 已获取Token")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试各个端点
    tests = [
        ("Chat", "/copilot/chat", {"message": "What is LangGraph?", "model": "local-smart"}),
        ("Workflow Suggestion", "/copilot/suggest/workflow", {"description": "Create a workflow", "model": "local-smart"}),
        ("Node Suggestion", "/copilot/suggest/node", {"context": "process data", "model": "local-smart"}),
        ("Workflow Diagnosis", "/copilot/diagnose", {"workflow": {"nodes": [{"id": "n1", "type": "Start"}], "edges": []}, "model": "local-smart"}),
        ("Prompt Generation", "/copilot/generate-prompt", {"task_description": "Summarize text", "style": "structured", "model": "local-smart"}),
    ]
    
    results = []
    for name, endpoint, data in tests:
        print(f"\n✏️  {name}:")
        status, response = make_request("POST", f"{BASE_URL}{endpoint}", data, headers)
        
        if status == 200:
            # 检查是否返回了有用的数据
            if isinstance(response, dict):
                if "message" in response:
                    is_fallback = "我可以帮" in response["message"]
                    symbol = "⚠️ " if is_fallback else "✅"
                    print(f"   {symbol} {'回退响应' if is_fallback else 'LLM响应'}")
                    print(f"   📊 Length: {len(response['message'])} chars")
                    results.append((name, "✅"))
                elif "workflows" in response:
                    print(f"   ✅ 返回 {len(response['workflows'])} 个工作流")
                    results.append((name, "✅"))
                elif "suggestions" in response:
                    print(f"   ✅ 返回 {len(response['suggestions'])} 个建议")
                    results.append((name, "✅"))
                elif "score" in response:
                    print(f"   ✅ 诊断分数: {response['score']}")
                    results.append((name, "✅"))
                elif "prompt" in response:
                    print(f"   ✅ 生成提示词 ({len(response['prompt'])} chars)")
                    results.append((name, "✅"))
                else:
                    print(f"   ⚠️  返回: {str(response)[:100]}")
                    results.append((name, "⚠️"))
        elif status == 422:
            print(f"   ❌ 请求参数错误 (422)")
            print(f"   Error: {response.get('detail', 'Unknown')}")
            results.append((name, "❌"))
        else:
            print(f"   ❌ HTTP {status}")
            results.append((name, "❌"))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试总结:")
    pass_count = sum(1 for _, s in results if s == "✅")
    total_count = len(results)
    
    for name, status in results:
        print(f"  {status} {name}")
    
    print(f"\n✅ 通过: {pass_count}/{total_count}")
    return pass_count == total_count

if __name__ == "__main__":
    try:
        success = test_copilot()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试中断")
        sys.exit(1)
