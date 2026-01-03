#!/usr/bin/env python3
"""
Copilot 全功能测试

测试所有 Copilot API 端点是否能正常从 LLM 返回数据
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "yangqx401@gmail.com",
    "password": "12345678"
}

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

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
        print(f"✅ 登录成功\n")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_chat(token):
    """测试聊天功能"""
    print_section("测试 1: 聊天功能 (POST /copilot/chat)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_cases = [
        {
            "message": "什么是 LangGraph？请简短回答。",
            "description": "基础问答"
        },
        {
            "message": "帮我设计一个简单的数据处理工作流",
            "description": "工作流设计建议"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"📤 测试用例 {i}: {test_case['description']}")
        print(f"   消息: {test_case['message']}")
        
        payload = {
            "message": test_case["message"],
            "model": "local-smart",
            "context": {
                "workflow_id": "test-workflow",
                "nodes": [],
                "edges": []
            },
            "chat_history": []
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_URL}/copilot/chat",
                headers=headers,
                json=payload,
                timeout=60
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                # 检查是否是配置错误
                if '❌ Copilot 当前无法使用' in message or '❌ LLM 配置错误' in message:
                    print(f"   ❌ 配置错误: LLM 未正确配置")
                    print(f"   错误详情: {message[:200]}...")
                    results.append({"test": test_case['description'], "status": "config_error"})
                # 检查是否是回退响应（简单规则响应）
                elif len(message) < 100 or "我可以帮你" in message:
                    print(f"   ⚠️  回退响应（可能是配置问题）")
                    print(f"   响应: {message[:200]}...")
                    results.append({"test": test_case['description'], "status": "fallback"})
                # 正常的 LLM 响应
                else:
                    print(f"   ✅ 成功（{elapsed:.2f}秒）")
                    print(f"   响应长度: {len(message)} 字符")
                    print(f"   响应预览: {message[:150]}...")
                    results.append({"test": test_case['description'], "status": "success"})
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                results.append({"test": test_case['description'], "status": "error"})
        
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append({"test": test_case['description'], "status": "exception"})
        
        print()
        time.sleep(1)  # 避免请求过快
    
    return results

def test_workflow_suggestion(token):
    """测试工作流建议功能"""
    print_section("测试 2: 工作流建议 (POST /copilot/suggest/workflow)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_cases = [
        {
            "description": "处理用户反馈的工作流",
            "complexity": "medium"
        },
        {
            "description": "RAG 文档检索系统",
            "complexity": "advanced"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"📤 测试用例 {i}: {test_case['description']}")
        
        payload = {
            "description": test_case["description"],
            "complexity": test_case["complexity"],
            "model": "local-smart"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_URL}/copilot/suggest/workflow",
                headers=headers,
                json=payload,
                timeout=60
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                workflows = result.get('workflows', [])
                
                if len(workflows) == 0:
                    print(f"   ⚠️  无工作流返回（可能是配置错误）")
                    results.append({"test": test_case['description'], "status": "empty"})
                elif len(workflows) > 0:
                    wf = workflows[0]
                    print(f"   ✅ 成功（{elapsed:.2f}秒）")
                    print(f"   返回工作流数: {len(workflows)}")
                    print(f"   第一个工作流:")
                    print(f"     - 名称: {wf.get('name', 'N/A')}")
                    print(f"     - 描述: {wf.get('description', 'N/A')[:80]}...")
                    print(f"     - 节点数: {len(wf.get('nodes', []))}")
                    print(f"     - 边数: {len(wf.get('edges', []))}")
                    
                    # 检查是否是简单的回退响应
                    if wf.get('name') == '通用工作流' or wf.get('name') == '基础工作流':
                        print(f"   ⚠️  注意: 这可能是回退响应而非 LLM 生成")
                        results.append({"test": test_case['description'], "status": "fallback"})
                    else:
                        results.append({"test": test_case['description'], "status": "success"})
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                results.append({"test": test_case['description'], "status": "error"})
        
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append({"test": test_case['description'], "status": "exception"})
        
        print()
        time.sleep(1)
    
    return results

def test_node_suggestion(token):
    """测试节点建议功能"""
    print_section("测试 3: 节点建议 (POST /copilot/suggest/node)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "context": "需要一个处理 JSON 数据的节点",
        "previous_node_type": "Input",
        "model": "local-smart"
    }
    
    try:
        print(f"📤 测试: 节点建议")
        print(f"   上下文: {payload['context']}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/copilot/suggest/node",
            headers=headers,
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            nodes = result.get('nodes', [])
            
            print(f"   ✅ 成功（{elapsed:.2f}秒）")
            print(f"   返回节点数: {len(nodes)}")
            
            if len(nodes) > 0:
                for i, node in enumerate(nodes[:3], 1):
                    print(f"   节点 {i}:")
                    print(f"     - 类型: {node.get('type', 'N/A')}")
                    print(f"     - 标签: {node.get('label', 'N/A')}")
                    print(f"     - 说明: {node.get('explanation', 'N/A')[:80]}...")
                return [{"test": "节点建议", "status": "success"}]
            else:
                print(f"   ⚠️  无节点返回")
                return [{"test": "节点建议", "status": "empty"}]
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   错误: {response.text[:200]}")
            return [{"test": "节点建议", "status": "error"}]
    
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return [{"test": "节点建议", "status": "exception"}]
    
    finally:
        print()

def test_workflow_diagnosis(token):
    """测试工作流诊断功能"""
    print_section("测试 4: 工作流诊断 (POST /copilot/diagnose)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 构造一个有问题的工作流
    payload = {
        "nodes": [
            {"id": "node1", "type": "Start", "label": "开始"},
            {"id": "node2", "type": "Tool", "label": "处理"},
            {"id": "node3", "type": "End", "label": "结束"},
            {"id": "node4", "type": "Tool", "label": "孤立节点"}  # 孤立节点
        ],
        "edges": [
            {"from": "node1", "to": "node2"},
            {"from": "node2", "to": "node3"}
            # node4 没有连接
        ],
        "model": "local-smart"
    }
    
    try:
        print(f"📤 测试: 工作流诊断（包含孤立节点）")
        
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/copilot/diagnose",
            headers=headers,
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            diagnostics = result.get('diagnostics', [])
            score = result.get('score', 0)
            summary = result.get('summary', '')
            
            print(f"   ✅ 成功（{elapsed:.2f}秒）")
            print(f"   健康评分: {score}/100")
            print(f"   问题数: {len(diagnostics)}")
            print(f"   总结: {summary[:100]}...")
            
            if len(diagnostics) > 0:
                print(f"\n   发现的问题:")
                for i, diag in enumerate(diagnostics[:3], 1):
                    print(f"   {i}. [{diag.get('level', 'N/A')}] {diag.get('description', 'N/A')}")
                    print(f"      建议: {diag.get('suggestion', 'N/A')[:80]}...")
            
            return [{"test": "工作流诊断", "status": "success"}]
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   错误: {response.text[:200]}")
            return [{"test": "工作流诊断", "status": "error"}]
    
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return [{"test": "工作流诊断", "status": "exception"}]
    
    finally:
        print()

def test_prompt_generation(token):
    """测试提示词生成功能"""
    print_section("测试 5: 提示词生成 (POST /copilot/generate-prompt)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "description": "生成一个总结长文本的提示词",
        "style": "structured",
        "model": "local-smart"
    }
    
    try:
        print(f"📤 测试: 提示词生成")
        print(f"   描述: {payload['description']}")
        print(f"   风格: {payload['style']}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/copilot/generate-prompt",
            headers=headers,
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            prompt = result.get('prompt', '')
            estimated_tokens = result.get('estimated_tokens', 0)
            
            print(f"   ✅ 成功（{elapsed:.2f}秒）")
            print(f"   生成的提示词长度: {len(prompt)} 字符")
            print(f"   预估 tokens: {estimated_tokens}")
            print(f"   提示词预览: {prompt[:150]}...")
            
            return [{"test": "提示词生成", "status": "success"}]
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   错误: {response.text[:200]}")
            return [{"test": "提示词生成", "status": "error"}]
    
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return [{"test": "提示词生成", "status": "exception"}]
    
    finally:
        print()

def print_summary(all_results):
    """打印测试总结"""
    print_section("测试总结")
    
    total = 0
    success = 0
    fallback = 0
    config_error = 0
    error = 0
    
    for results in all_results:
        for result in results:
            total += 1
            status = result['status']
            if status == 'success':
                success += 1
            elif status == 'fallback':
                fallback += 1
            elif status == 'config_error':
                config_error += 1
            else:
                error += 1
    
    print(f"总测试数: {total}")
    print(f"✅ 成功（LLM 正常响应）: {success}")
    print(f"⚠️  回退响应（规则模式）: {fallback}")
    print(f"❌ 配置错误: {config_error}")
    print(f"❌ 其他错误: {error}")
    
    print("\n" + "-" * 70)
    
    if config_error > 0:
        print("\n⚠️  检测到配置错误！")
        print("\n请确保:")
        print("  1. 数据库中已配置 llm_providers（包含有效的 API key）")
        print("  2. 数据库中已配置 llm_models")
        print("  3. provider 和 model 都是 is_active = true")
        print("\n检查配置:")
        print("  curl http://localhost:8000/api/v1/llm-provider-model/providers")
        print("  curl http://localhost:8000/api/v1/llm-provider-model/models")
    elif fallback > 0:
        print("\n⚠️  部分响应使用了回退模式（规则响应）")
        print("这可能意味着 LLM 调用失败，请检查:")
        print("  - API key 是否有效")
        print("  - 网络连接是否正常")
        print("  - 后端日志中是否有错误")
    elif success == total:
        print("\n🎉 所有测试通过！Copilot 功能正常，模型返回数据正常！")
    else:
        print("\n⚠️  部分测试失败，请检查错误详情")
    
    print()

def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("  🧪 Copilot 全功能测试")
    print("  测试所有 API 端点是否能正常从 LLM 返回数据")
    print("=" * 70)
    
    # 登录
    token = login()
    if not token:
        print("\n❌ 无法登录，测试终止")
        return
    
    # 运行所有测试
    all_results = []
    
    all_results.append(test_chat(token))
    all_results.append(test_workflow_suggestion(token))
    all_results.append(test_node_suggestion(token))
    all_results.append(test_workflow_diagnosis(token))
    all_results.append(test_prompt_generation(token))
    
    # 打印总结
    print_summary(all_results)

if __name__ == "__main__":
    main()
