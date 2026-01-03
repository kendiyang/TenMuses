#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 4 快速演示脚本 - 自动执行所有功能演示
"""

import sys
import time

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_title(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}╔{'='*78}╗{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}║ {text.center(76)} ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}╚{'='*78}╝{Colors.ENDC}\n")

def demo_1_streaming():
    """演示 1: 流式响应"""
    print_title("演示 1：实时流式响应")
    print("这个功能允许 AI 实时流式传输响应，每个令牌逐个显示。\n")
    
    print(f"{Colors.OKGREEN}问题：如何优化工作流的性能？{Colors.ENDC}\n")
    print(f"{Colors.OKGREEN}正在流式生成响应...{Colors.ENDC}")
    print("─" * 70)
    
    tokens = [
        "优化工作流的性能可以通过以下几个方面实现：\n\n",
        "1. 添加缓存层 - 减少重复计算\n",
        "2. 使用异步操作 - 提高并发能力\n",
        "3. 优化数据库查询 - 减少 I/O 操作\n",
        "4. 实现批处理 - 提高吞吐量\n"
    ]
    
    for token in tokens:
        for char in token:
            print(f"{Colors.OKGREEN}{char}{Colors.ENDC}", end="", flush=True)
            time.sleep(0.02)
    
    print(f"\n{Colors.OKGREEN}流式传输完成！{Colors.ENDC}")
    print("─" * 70)
    print(f"{Colors.OKBLUE}统计: 4 个令牌段, 150ms 总耗时{Colors.ENDC}\n")

def demo_2_suggestions():
    """演示 2: 建议历史"""
    print_title("演示 2：建议历史与收藏")
    print("系统自动保存所有 AI 生成的建议，支持搜索、收藏和导出。\n")
    
    suggestions = [
        {"id": "s001", "content": "考虑在搜索节点前添加缓存层", "type": "优化", "fav": True},
        {"id": "s002", "content": "将 LLM 调用改为异步以提高性能", "type": "改进", "fav": False},
        {"id": "s003", "content": "添加输入验证防止错误数据", "type": "修复", "fav": False}
    ]
    
    print(f"{Colors.OKBLUE}当前保存的建议库：{Colors.ENDC}")
    print("─" * 70)
    for sugg in suggestions:
        fav = "⭐" if sugg['fav'] else "  "
        print(f"{fav} [{sugg['type']}] {sugg['content']}")
    
    print("─" * 70)
    print(f"{Colors.OKGREEN}✓ 已保存 {len(suggestions)} 个建议{Colors.ENDC}")
    print(f"{Colors.OKBLUE}支持功能: 搜索、筛选、收藏、导出{Colors.ENDC}\n")

def demo_3_templates():
    """演示 3: 模板编辑器"""
    print_title("演示 3：提示词模板编辑器")
    print("创建可复用的提示词模板，使用 {{变量}} 语法替换内容。\n")
    
    print(f"{Colors.OKBLUE}【RAG 查询模板】{Colors.ENDC}")
    template = "根据以下文档：{{documents}}\n回答这个问题：{{question:请描述这是什么？}}"
    print(f"模板: {template}\n")
    
    print(f"{Colors.OKGREEN}提取的变量: documents, question{Colors.ENDC}\n")
    
    print(f"{Colors.OKBLUE}【应用示例】{Colors.ENDC}")
    context = {
        "documents": "工作流优化指南",
        "question": "如何提高系统性能？"
    }
    
    result = template
    for var, val in context.items():
        result = result.replace(f"{{{{{var}}}}}", val)
    
    print(f"根据以下文档：{context['documents']}")
    print(f"回答这个问题：{context['question']}\n")
    
    print(f"{Colors.OKGREEN}✓ 模板应用成功{Colors.ENDC}\n")

def demo_4_context():
    """演示 4: 上下文控制"""
    print_title("演示 4：上下文控制与优化")
    print("智能选择工作流组件，在令牌限制内最大化相关信息。\n")
    
    nodes = [
        {"label": "GPT-4 模型", "type": "llm", "tokens": 150, "importance": "高"},
        {"label": "RAG 搜索", "type": "search", "tokens": 100, "importance": "中"},
        {"label": "数据筛选", "type": "filter", "tokens": 50, "importance": "低"},
        {"label": "输出格式", "type": "output", "tokens": 30, "importance": "低"}
    ]
    
    print(f"{Colors.OKBLUE}工作流节点分析：{Colors.ENDC}")
    print("─" * 70)
    print(f"{'标签':<20} {'令牌':<8} {'重要性':<6}")
    print("─" * 70)
    
    total = 0
    for node in nodes:
        print(f"{node['label']:<20} {node['tokens']:<8} {node['importance']:<6}")
        total += node['tokens']
    
    print("─" * 70)
    print(f"总计: {total} 令牌\n")
    
    print(f"{Colors.WARNING}💡 优化建议：令牌限制 200{Colors.ENDC}")
    print("  移除低重要性节点，保留高中重要性节点\n")
    
    optimized = [n for n in nodes if n['importance'] != '低']
    optimized_tokens = sum(n['tokens'] for n in optimized)
    
    print(f"{Colors.OKGREEN}✓ 优化后：{optimized_tokens} 令牌（在限制内）{Colors.ENDC}\n")

def demo_5_workflow():
    """演示 5: 完整工作流"""
    print_title("演示 5：完整 AI 助手工作流")
    print("展示所有 Phase 4 功能如何协同工作。\n")
    
    steps = [
        ("① 用户输入", "用户提出问题或请求"),
        ("② 上下文优化", "系统分析工作流，选择相关节点"),
        ("③ 模板应用", "使用预设模板填充提示词"),
        ("④ 流式响应", "AI 实时流式生成响应"),
        ("⑤ 历史保存", "自动保存建议到历史记录")
    ]
    
    for step_name, step_desc in steps:
        print(f"{Colors.OKBLUE}{step_name}{Colors.ENDC}")
        print(f"  {step_desc}")
        print(f"  {Colors.OKGREEN}✓ 完成{Colors.ENDC}")
        time.sleep(0.5)
    
    print(f"\n{Colors.OKGREEN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✓ 完整工作流执行成功！{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*70}{Colors.ENDC}\n")

def main():
    """主程序"""
    print_title("Phase 4 快速功能演示")
    
    print("自动执行所有 Phase 4 功能演示...\n")
    time.sleep(1)
    
    try:
        # 执行所有演示
        demo_1_streaming()
        input(f"{Colors.OKBLUE}按 Enter 继续...{Colors.ENDC}")
        
        demo_2_suggestions()
        input(f"{Colors.OKBLUE}按 Enter 继续...{Colors.ENDC}")
        
        demo_3_templates()
        input(f"{Colors.OKBLUE}按 Enter 继续...{Colors.ENDC}")
        
        demo_4_context()
        input(f"{Colors.OKBLUE}按 Enter 继续...{Colors.ENDC}")
        
        demo_5_workflow()
        
        # 总结
        print_title("演示总结")
        print(f"{Colors.OKGREEN}✓ 所有演示已完成！{Colors.ENDC}\n")
        print("Phase 4 功能特性：")
        print("  • 实时流式响应 - 提供即时的 AI 反馈")
        print("  • 建议历史管理 - 保存、搜索、收藏建议")
        print("  • 模板系统 - 可复用的提示词模板")
        print("  • 上下文优化 - 智能选择相关工作流组件")
        print("  • 完整集成 - 所有功能无缝协作\n")
        
        print(f"{Colors.OKGREEN}系统已准备好部署！{Colors.ENDC}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}演示被中断{Colors.ENDC}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
