#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 4 交互功能演示脚本
提供交互式的功能演示和使用示例
"""

import sys
import time
import json
from typing import Dict, Any

# 颜色输出
class UI:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def print_title(text: str):
        print(f"\n{UI.BOLD}{UI.HEADER}╔{'='*78}╗{UI.ENDC}")
        print(f"{UI.BOLD}{UI.HEADER}║ {text.center(76)} ║{UI.ENDC}")
        print(f"{UI.BOLD}{UI.HEADER}╚{'='*78}╝{UI.ENDC}\n")
    
    @staticmethod
    def print_menu(options: list):
        for i, option in enumerate(options, 1):
            print(f"{UI.OKBLUE}{i}.{UI.ENDC} {option}")
        print()
    
    @staticmethod
    def print_demo(title: str):
        print(f"\n{UI.BOLD}{UI.OKCYAN}【{title}】{UI.ENDC}")
        print(f"{UI.OKCYAN}{'─'*70}{UI.ENDC}")
    
    @staticmethod
    def print_success(text: str):
        print(f"{UI.OKGREEN}✓ {text}{UI.ENDC}")
    
    @staticmethod
    def print_input(prompt: str) -> str:
        return input(f"{UI.OKBLUE}→ {prompt}{UI.ENDC} ")
    
    @staticmethod
    def print_output(text: str, label: str = "输出"):
        print(f"{UI.OKCYAN}{label}:{UI.ENDC}")
        for line in text.split('\n'):
            print(f"  {line}")


class Phase4Demo:
    """Phase 4 交互功能演示"""
    
    def __init__(self):
        self.demo_data = {
            "suggestions": [],
            "templates": [],
            "workflows": []
        }
    
    # ========================================================================
    # 功能 1: 流式响应演示
    # ========================================================================
    
    def demo_streaming(self):
        """演示流式响应功能"""
        UI.print_demo("演示 1：实时流式响应")
        
        print("这个功能允许 AI 实时流式传输响应，每个令牌逐个显示。\n")
        
        prompt = UI.print_input("请输入您的问题（或按 Enter 使用示例）")
        if not prompt:
            prompt = "如何优化工作流的性能？"
        
        print(f"\n{UI.OKGREEN}正在流式生成响应...{UI.ENDC}")
        print("─" * 70)
        
        # 模拟流式响应
        response_tokens = [
            "优化工作流", "的", "性能", "可以", "通过", "以下", "几个", "方面",
            "实现", "：\n",
            "1. ", "添加", "缓存", "层", "减少", "重复", "计算\n",
            "2. ", "使用", "异步", "操作", "提高", "并发", "能力\n",
            "3. ", "优化", "数据库", "查询", "减少", "I/O", "操作\n",
            "4. ", "实现", "批处理", "提高", "吞吐", "量"
        ]
        
        full_response = ""
        for token in response_tokens:
            full_response += token
            print(f"{UI.OKGREEN}{token}{UI.ENDC}", end="", flush=True)
            time.sleep(0.05)  # 模拟延迟
        
        print(f"\n{UI.OKGREEN}流式传输完成！{UI.ENDC}")
        print(f"─" * 70)
        
        # 显示统计信息
        token_count = len(response_tokens)
        char_count = len(full_response)
        print(f"\n统计信息:")
        print(f"  令牌数：{token_count}")
        print(f"  字符数：{char_count}")
        print(f"  平均延迟：50ms/令牌")
    
    # ========================================================================
    # 功能 2: 建议历史演示
    # ========================================================================
    
    def demo_suggestions(self):
        """演示建议历史功能"""
        UI.print_demo("演示 2：建议历史与收藏")
        
        print("系统会自动保存所有 AI 生成的建议，支持搜索、收藏和导出。\n")
        
        # 初始化示例建议
        sample_suggestions = [
            {
                "id": "s001",
                "content": "考虑在搜索节点前添加缓存层",
                "type": "优化",
                "timestamp": "2026-01-01 10:30",
                "favorite": False
            },
            {
                "id": "s002", 
                "content": "将 LLM 调用改为异步以提高性能",
                "type": "改进",
                "timestamp": "2026-01-01 10:35",
                "favorite": True
            },
            {
                "id": "s003",
                "content": "添加输入验证防止错误数据",
                "type": "修复",
                "timestamp": "2026-01-01 10:40",
                "favorite": False
            }
        ]
        
        print("当前保存的建议：")
        print("─" * 70)
        for i, sugg in enumerate(sample_suggestions, 1):
            favorite_mark = "⭐" if sugg["favorite"] else "  "
            print(f"{i}. [{sugg['type']}] {favorite_mark} {sugg['content']}")
            print(f"   时间: {sugg['timestamp']}")
        
        print("\n功能菜单：")
        options = [
            "搜索建议",
            "按类型筛选",
            "切换收藏",
            "导出建议",
            "返回主菜单"
        ]
        UI.print_menu(options)
        
        choice = UI.print_input("选择操作 (1-5)")
        
        if choice == "1":
            self._search_suggestions(sample_suggestions)
        elif choice == "2":
            self._filter_suggestions(sample_suggestions)
        elif choice == "3":
            self._toggle_favorite(sample_suggestions)
        elif choice == "4":
            self._export_suggestions(sample_suggestions)
    
    def _search_suggestions(self, suggestions):
        """搜索建议"""
        query = UI.print_input("输入搜索关键词")
        results = [s for s in suggestions if query in s["content"]]
        
        print(f"\n搜索结果（找到 {len(results)} 个）：")
        for sugg in results:
            print(f"  • {sugg['content']}")
    
    def _filter_suggestions(self, suggestions):
        """按类型筛选"""
        types = list(set(s["type"] for s in suggestions))
        print("\n可用类型：")
        for i, t in enumerate(types, 1):
            print(f"{i}. {t}")
        
        choice = input(f"选择类型 (1-{len(types)}): ")
        if choice.isdigit() and 1 <= int(choice) <= len(types):
            selected_type = types[int(choice) - 1]
            results = [s for s in suggestions if s["type"] == selected_type]
            print(f"\n筛选结果（{selected_type}）：")
            for sugg in results:
                print(f"  • {sugg['content']}")
    
    def _toggle_favorite(self, suggestions):
        """切换收藏"""
        idx = input("输入建议编号: ")
        if idx.isdigit() and 1 <= int(idx) <= len(suggestions):
            suggestions[int(idx) - 1]["favorite"] = not suggestions[int(idx) - 1]["favorite"]
            print("✓ 收藏状态已更新")
    
    def _export_suggestions(self, suggestions):
        """导出建议"""
        export_data = json.dumps(suggestions, ensure_ascii=False, indent=2)
        print("\n导出为 JSON 格式：")
        print("─" * 70)
        print(export_data)
        print("─" * 70)
        print("✓ 可以复制这个 JSON 保存到文件")
    
    # ========================================================================
    # 功能 3: 模板编辑器演示
    # ========================================================================
    
    def demo_templates(self):
        """演示模板编辑器功能"""
        UI.print_demo("演示 3：提示词模板编辑器")
        
        print("创建可复用的提示词模板，使用 {{变量}} 语法替换内容。\n")
        
        sample_templates = [
            {
                "name": "RAG 查询",
                "template": "根据以下文档：{{documents}}\n回答这个问题：{{question:请描述这是什么？}}"
            },
            {
                "name": "代码审查",
                "template": "请审查以下 {{language:Python}} 代码：\n{{code}}\n重点关注：{{focus:性能和可读性}}"
            },
            {
                "name": "翻译",
                "template": "将以下文本翻译成 {{target_language:中文}}：\n{{text}}"
            }
        ]
        
        print("预设模板库：")
        print("─" * 70)
        for i, tmpl in enumerate(sample_templates, 1):
            print(f"{i}. {tmpl['name']}")
            print(f"   模板: {tmpl['template'][:50]}...")
        
        print("\n功能菜单：")
        options = [
            "查看完整模板",
            "创建新模板",
            "应用模板",
            "返回主菜单"
        ]
        UI.print_menu(options)
        
        choice = UI.print_input("选择操作 (1-4)")
        
        if choice == "1":
            idx = input("选择模板编号 (1-3): ")
            if idx.isdigit() and 1 <= int(idx) <= len(sample_templates):
                tmpl = sample_templates[int(idx) - 1]
                UI.print_output(tmpl['template'], f"【{tmpl['name']}】")
        elif choice == "2":
            self._create_template()
        elif choice == "3":
            self._apply_template(sample_templates[0])
    
    def _create_template(self):
        """创建新模板"""
        name = input("模板名称: ")
        content = input("模板内容（使用 {{变量}} 语法）: ")
        
        # 提取变量
        import re
        variables = re.findall(r'\{\{(\w+)', content)
        
        print(f"\n✓ 模板已创建")
        print(f"  名称: {name}")
        print(f"  提取的变量: {', '.join(variables)}")
    
    def _apply_template(self, template):
        """应用模板"""
        print(f"\n应用模板: {template['name']}")
        print(f"模板内容: {template['template']}\n")
        
        # 解析变量
        import re
        variables = re.findall(r'\{\{(\w+)', template['template'])
        
        context = {}
        for var in variables:
            value = input(f"请输入 {var} 的值: ")
            context[var] = value
        
        # 渲染
        result = template['template']
        for var, value in context.items():
            result = result.replace(f"{{{{{var}}}}}", value)
        
        print(f"\n渲染结果：")
        UI.print_output(result, "生成的提示词")
    
    # ========================================================================
    # 功能 4: 上下文控制演示
    # ========================================================================
    
    def demo_context(self):
        """演示上下文控制功能"""
        UI.print_demo("演示 4：上下文控制与优化")
        
        print("智能选择工作流组件，在令牌限制内最大化相关信息。\n")
        
        # 示例工作流节点
        nodes = [
            {"id": "1", "type": "llm", "label": "GPT-4 模型", "tokens": 150, "importance": "高"},
            {"id": "2", "type": "search", "label": "RAG 搜索", "tokens": 100, "importance": "中"},
            {"id": "3", "type": "filter", "label": "数据筛选", "tokens": 50, "importance": "低"},
            {"id": "4", "type": "output", "label": "输出格式", "tokens": 30, "importance": "低"}
        ]
        
        print("工作流节点分析：")
        print("─" * 70)
        print(f"{'ID':<5} {'标签':<20} {'类型':<10} {'令牌':<8} {'重要性':<6}")
        print("─" * 70)
        
        total_tokens = 0
        for node in nodes:
            print(f"{node['id']:<5} {node['label']:<20} {node['type']:<10} {node['tokens']:<8} {node['importance']:<6}")
            total_tokens += node['tokens']
        
        print("─" * 70)
        print(f"{'总计':<45} {total_tokens}")
        
        # 优化
        print("\n💡 优化建议：")
        print("  • 节点总令牌数：330")
        print("  • 推荐令牌限制：200")
        print("  • 优化方案：保留高重要性节点，移除低重要性节点")
        
        print("\n执行优化...")
        print("─" * 70)
        
        optimized = [n for n in nodes if n['importance'] != '低']
        optimized_tokens = sum(n['tokens'] for n in optimized)
        
        print("优化后的配置：")
        for node in optimized:
            print(f"  ✓ {node['label']:<20} {node['tokens']:>3} 令牌")
        
        print(f"  {'─'*30}")
        print(f"  总计: {optimized_tokens} 令牌 (在 200 令牌限制内)")
        print("\n✓ 优化完成！上下文已准备就绪。")
    
    # ========================================================================
    # 功能 5: 完整工作流演示
    # ========================================================================
    
    def demo_full_workflow(self):
        """演示完整的 AI 助手工作流"""
        UI.print_demo("演示 5：完整 AI 助手工作流")
        
        print("展示所有 Phase 4 功能如何协同工作。\n")
        
        workflow_steps = [
            {
                "step": 1,
                "name": "用户输入",
                "description": "用户提出问题或请求"
            },
            {
                "step": 2,
                "name": "上下文优化",
                "description": "系统分析工作流，选择相关节点"
            },
            {
                "step": 3,
                "name": "模板应用",
                "description": "使用预设模板填充提示词"
            },
            {
                "step": 4,
                "name": "流式响应",
                "description": "AI 实时流式生成响应"
            },
            {
                "step": 5,
                "name": "历史保存",
                "description": "自动保存建议到历史记录"
            }
        ]
        
        print("工作流步骤：")
        print("─" * 70)
        
        for step in workflow_steps:
            print(f"\n【步骤 {step['step']}】{step['name']}")
            print(f"    {step['description']}")
            
            if step['step'] == 4:
                print("\n    实时响应预览：")
                print("    " + "─" * 62)
                response = "根据分析，我建议采用异步架构来提高系统性能..."
                for char in response:
                    print(char, end="", flush=True)
                    time.sleep(0.02)
                print("\n    " + "─" * 62)
            
            time.sleep(0.5)
            print(f"    ✓ 完成")
        
        print("\n" + "─" * 70)
        print("✓ 完整工作流执行成功！")


def main():
    """主程序"""
    demo = Phase4Demo()
    
    while True:
        UI.print_title("Phase 4 TenMuses Copilot - 交互功能演示")
        
        print("请选择要演示的功能：\n")
        options = [
            "演示 1：流式响应支持",
            "演示 2：建议历史与收藏",
            "演示 3：提示词模板编辑器",
            "演示 4：上下文控制与优化",
            "演示 5：完整 AI 助手工作流",
            "退出程序"
        ]
        
        UI.print_menu(options)
        
        choice = UI.print_input("选择 (1-6)")
        
        try:
            if choice == "1":
                demo.demo_streaming()
            elif choice == "2":
                demo.demo_suggestions()
            elif choice == "3":
                demo.demo_templates()
            elif choice == "4":
                demo.demo_context()
            elif choice == "5":
                demo.demo_full_workflow()
            elif choice == "6":
                print(f"\n{UI.OKGREEN}感谢使用！再见！{UI.ENDC}\n")
                break
            else:
                print(f"{UI.WARNING}无效选择，请重试{UI.ENDC}")
            
            input(f"\n{UI.OKBLUE}按 Enter 继续...{UI.ENDC}")
            print("\n" * 2)
            
        except KeyboardInterrupt:
            print(f"\n\n{UI.WARNING}演示被中断{UI.ENDC}\n")
            break
        except Exception as e:
            print(f"\n{UI.FAIL}错误: {e}{UI.ENDC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        sys.exit(0)
