#!/usr/bin/env python3
"""
Phase 2 独立测试脚本 - 不依赖pytest

直接运行Python脚本来测试核心功能
"""

import os
import sys
import asyncio
from datetime import datetime

# 设置测试环境变量
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['ANTHROPIC_API_KEY'] = 'test-anthropic-key'
os.environ['CORS_ORIGINS_STR'] = 'http://localhost:3000'

# 导入核心模块
from app.schemas.node import (
    WorkflowGraph, Node, Edge, NodeType, NodeData, NodePosition,
    LLMConfig, ToolConfig, RouterConfig, MapConfig, RouterCondition,
    validate_graph
)
from app.services.dynamic_graph_factory import (
    DynamicGraphFactory, create_workflow, WorkflowState
)
from app.services.executor_library import (
    tool_library, ExpressionEvaluator, create_executor
)


# ============================================================================
# 测试辅助函数
# ============================================================================

def create_test_llm_node(node_id: str, label: str = "测试节点") -> Node:
    """创建测试用LLM节点"""
    return Node(
        id=node_id,
        type=NodeType.LLM,
        position=NodePosition(x=100, y=100),
        data=NodeData(
            label=label,
            llm_config=LLMConfig(
                provider="openai",
                model="gpt-4-turbo-preview",
                temperature=0.7,
                system_prompt="你是一个助手"
            )
        )
    )


def print_test_header(test_name: str):
    """打印测试头部"""
    print("\n" + "="*60)
    print(f"  测试: {test_name}")
    print("="*60)


def print_result(passed: bool, message: str):
    """打印测试结果"""
    icon = "✅" if passed else "❌"
    print(f"{icon} {message}")


# ============================================================================
# 测试函数
# ============================================================================

def test_node_creation():
    """测试1: 节点创建"""
    print_test_header("节点创建")
    
    try:
        # 创建LLM节点
        node = create_test_llm_node("node-1", "测试LLM节点")
        assert node.id == "node-1"
        assert node.type == NodeType.LLM
        assert node.data.llm_config is not None
        print_result(True, "LLM节点创建成功")
        
        # 创建Tool节点
        tool_node = Node(
            id="tool-1",
            type=NodeType.TOOL,
            position=NodePosition(x=200, y=100),
            data=NodeData(
                label="工具节点",
                tool_config=ToolConfig(
                    tool_name="text_process",
                    tool_input_schema={"input": {"type": "string"}},
                    required_inputs=["input"]
                )
            )
        )
        assert tool_node.type == NodeType.TOOL
        print_result(True, "Tool节点创建成功")
        
        return True
    except Exception as e:
        print_result(False, f"节点创建失败: {e}")
        return False


def test_graph_validation():
    """测试2: 图验证"""
    print_test_header("图验证")
    
    try:
        # 创建简单工作流
        nodes = [
            create_test_llm_node("node-1", "节点1"),
            create_test_llm_node("node-2", "节点2"),
            create_test_llm_node("node-3", "节点3")
        ]
        
        edges = [
            Edge(id="edge-1", source="node-1", target="node-2", type="normal"),
            Edge(id="edge-2", source="node-2", target="node-3", type="normal")
        ]
        
        graph = WorkflowGraph(nodes=nodes, edges=edges)
        validated = validate_graph(graph)
        
        assert len(validated.nodes) == 3
        assert len(validated.edges) == 2
        print_result(True, f"图验证成功: {len(validated.nodes)}个节点, {len(validated.edges)}条边")
        
        return True
    except Exception as e:
        print_result(False, f"图验证失败: {e}")
        return False


def test_duplicate_node_detection():
    """测试3: 重复节点检测"""
    print_test_header("重复节点检测")
    
    try:
        nodes = [
            create_test_llm_node("node-1", "节点1"),
            create_test_llm_node("node-1", "节点2")  # 重复ID
        ]
        edges = []
        
        graph = WorkflowGraph(nodes=nodes, edges=edges)
        
        try:
            validate_graph(graph)
            print_result(False, "应该检测到重复节点ID但没有")
            return False
        except ValueError as ve:
            if "唯一" in str(ve):
                print_result(True, f"正确检测到重复节点: {ve}")
                return True
            else:
                print_result(False, f"错误信息不符合预期: {ve}")
                return False
                
    except Exception as e:
        print_result(False, f"测试失败: {e}")
        return False


def test_invalid_edge_detection():
    """测试4: 无效边检测"""
    print_test_header("无效边检测")
    
    try:
        nodes = [create_test_llm_node("node-1", "节点1")]
        edges = [Edge(
            id="edge-1",
            source="node-1",
            target="nonexistent",  # 不存在的节点
            type="normal"
        )]
        
        graph = WorkflowGraph(nodes=nodes, edges=edges)
        
        try:
            validate_graph(graph)
            print_result(False, "应该检测到无效边但没有")
            return False
        except ValueError as ve:
            if "不存在" in str(ve):
                print_result(True, f"正确检测到无效边: {ve}")
                return True
            else:
                print_result(False, f"错误信息不符合预期: {ve}")
                return False
                
    except Exception as e:
        print_result(False, f"测试失败: {e}")
        return False


def test_factory_creation():
    """测试5: 工厂创建"""
    print_test_header("工厂创建")
    
    try:
        nodes = [
            create_test_llm_node("node-1", "节点1"),
            create_test_llm_node("node-2", "节点2")
        ]
        edges = [Edge(id="edge-1", source="node-1", target="node-2", type="normal")]
        
        graph = WorkflowGraph(nodes=nodes, edges=edges)
        factory = DynamicGraphFactory(graph)
        
        assert len(factory.nodes_map) == 2
        assert len(factory.executors) == 2
        assert "node-1" in factory.executors
        assert "node-2" in factory.executors
        
        print_result(True, f"工厂创建成功: {len(factory.executors)}个执行器")
        
        # 验证起始/结束节点
        start_nodes = factory._get_start_nodes()
        end_nodes = factory._get_end_nodes()
        
        assert "node-1" in start_nodes
        assert "node-2" in end_nodes
        
        print_result(True, f"起始节点: {start_nodes}, 结束节点: {end_nodes}")
        
        return True
    except Exception as e:
        print_result(False, f"工厂创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_library():
    """测试6: 工具库"""
    print_test_header("工具库")
    
    try:
        tools = tool_library.list_tools()
        assert len(tools) > 0
        print_result(True, f"工具库包含 {len(tools)} 个内置工具")
        
        for tool_name, description in tools.items():
            print(f"   - {tool_name}: {description}")
        
        # 测试获取工具
        text_process = tool_library.get("text_process")
        assert text_process is not None
        print_result(True, "成功获取text_process工具")
        
        # 测试工具执行
        result = asyncio.run(text_process({"text": "hello"}))
        assert "HELLO" in str(result).upper()
        print_result(True, f"工具执行成功: {result}")
        
        return True
    except Exception as e:
        print_result(False, f"工具库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_expression_evaluator():
    """测试7: 表达式评估器"""
    print_test_header("表达式评估器")
    
    try:
        evaluator = ExpressionEvaluator()
        
        # 测试相等
        context = {"output": {"status": "approved"}}
        result = evaluator.evaluate('output.status == "approved"', context)
        assert result is True
        print_result(True, '表达式评估: output.status == "approved" → True')
        
        result = evaluator.evaluate('output.status == "rejected"', context)
        assert result is False
        print_result(True, '表达式评估: output.status == "rejected" → False')
        
        # 测试数值比较
        context = {"output": {"score": 0.85}}
        result = evaluator.evaluate("output.score > 0.8", context)
        assert result is True
        print_result(True, "表达式评估: output.score > 0.8 → True")
        
        result = evaluator.evaluate("output.score < 0.5", context)
        assert result is False
        print_result(True, "表达式评估: output.score < 0.5 → False")
        
        return True
    except Exception as e:
        print_result(False, f"表达式评估测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_large_workflow():
    """测试8: 大型工作流 (100节点)"""
    print_test_header("大型工作流性能")
    
    try:
        import time
        
        # 创建100个节点的线性链
        nodes = [create_test_llm_node(f"node-{i}", f"节点{i}") for i in range(100)]
        edges = [
            Edge(id=f"edge-{i}", source=f"node-{i}", target=f"node-{i+1}", type="normal")
            for i in range(99)
        ]
        
        graph = WorkflowGraph(nodes=nodes, edges=edges)
        
        # 测量编译时间
        start = time.time()
        validated = validate_graph(graph)
        factory = DynamicGraphFactory(validated)
        compile_time = time.time() - start
        
        assert len(factory.nodes_map) == 100
        assert len(factory.executors) == 100
        
        print_result(True, f"100节点工作流编译成功")
        print(f"   编译时间: {compile_time:.4f}秒")
        
        if compile_time < 1.0:
            print_result(True, "编译性能良好 (< 1秒)")
            return True
        else:
            print_result(False, f"编译时间过长: {compile_time:.2f}秒")
            return False
            
    except Exception as e:
        print_result(False, f"大型工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 主测试运行器
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🎯 "*20)
    print("        TenMuses Phase 2 独立测试套件")
    print("🎯 "*20 + "\n")
    
    tests = [
        ("节点创建", test_node_creation),
        ("图验证", test_graph_validation),
        ("重复节点检测", test_duplicate_node_detection),
        ("无效边检测", test_invalid_edge_detection),
        ("工厂创建", test_factory_creation),
        ("工具库", test_tool_library),
        ("表达式评估器", test_expression_evaluator),
        ("大型工作流", test_large_workflow),
    ]
    
    results = []
    start_time = datetime.now()
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ 测试 {name} 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("                    测试总结")
    print("="*60 + "\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}")
    
    print("\n" + "-"*60)
    print(f"通过: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print(f"耗时: {elapsed:.2f}秒")
    print("-"*60 + "\n")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！")
        return 0
    else:
        print(f"⚠️  有 {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
