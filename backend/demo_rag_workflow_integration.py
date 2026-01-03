#!/usr/bin/env python
"""
RAG Workflow Integration Demonstration (No DB Required)

This script demonstrates:
1. RAG Configuration in LLM Nodes
2. How RAG context is retrieved and injected
3. WebSocket event format for RAG search
4. End-to-end workflow with RAG
"""

import json
from typing import Dict, Any, List
from dataclasses import asdict


def create_sample_workflow_with_rag() -> Dict[str, Any]:
    """Create a sample workflow with RAG-enabled LLM node"""
    
    workflow = {
        "id": "wf-001-rag-research",
        "title": "AI Trends Research with RAG",
        "description": "Research AI trends using knowledge base",
        "nodes": [
            {
                "id": "input",
                "type": "input",
                "data": {
                    "label": "User Query",
                    "description": "Initial research topic"
                },
                "position": {"x": 0, "y": 100}
            },
            {
                "id": "research-with-rag",
                "type": "llm",
                "data": {
                    "label": "Research with Knowledge Base",
                    "llm_config": {
                        # Basic LLM config
                        "provider": "openai",
                        "model": "gpt-4-turbo-preview",
                        "temperature": 0.7,
                        "max_tokens": 2000,
                        "system_prompt": "You are an AI research expert. Answer questions using provided knowledge base context.",
                        
                        # ✨ RAG Configuration - NEW!
                        "enable_rag": True,
                        "knowledge_documents": [
                            "doc-ai-trends-2024",
                            "doc-rag-guide",
                            "doc-workflow-design"
                        ],
                        "rag_mode": "chunk",  # or "document"
                        "rag_top_k": 5,  # Number of results
                        "rag_min_score": 0.5  # Relevance threshold
                    }
                },
                "position": {"x": 400, "y": 100}
            },
            {
                "id": "output",
                "type": "output",
                "data": {
                    "label": "Research Result",
                    "description": "Generated research report"
                },
                "position": {"x": 800, "y": 100}
            }
        ],
        "edges": [
            {
                "id": "e1",
                "source": "input",
                "target": "research-with-rag",
                "type": "normal"
            },
            {
                "id": "e2",
                "source": "research-with-rag",
                "target": "output",
                "type": "normal"
            }
        ]
    }
    
    return workflow


def simulate_rag_retrieval(query: str) -> Dict[str, Any]:
    """Simulate RAG retrieval from knowledge base"""
    
    retrieval_results = {
        "query": query,
        "mode": "chunk",
        "top_k": 5,
        "results": [
            {
                "document_id": "doc-rag-guide",
                "chunk_id": "chunk-001",
                "score": 0.94,
                "content": """检索增强生成（RAG）实现指南
- RAG 核心概念：从外部知识库检索相关文档
- 将文档内容注入到 LLM prompt 中
- 提升 LLM 回答的准确性和可信度
- 系统架构包括：文档加载、分片、向量化、存储、检索、格式化"""
            },
            {
                "document_id": "doc-ai-trends-2024",
                "chunk_id": "chunk-042",
                "score": 0.87,
                "content": """2024 年 AI 趋势报告
- 知识库检索增强（RAG）已成为关键技术
- 在多模态模型和自主智能体中广泛应用
- 企业采用率大幅增长（60%+）
- 与向量数据库集成成为标配"""
            },
            {
                "document_id": "doc-workflow-design",
                "chunk_id": "chunk-078",
                "score": 0.72,
                "content": """工作流设计最佳实践
- 节点类型：LLM、Tool、Router、Map
- 节点间通过边连接，实现数据流转
- 支持 RAG 配置：enable_rag、knowledge_documents、rag_mode
- RAG 参数：top_k、min_score、search_mode"""
            }
        ]
    }
    
    return retrieval_results


def format_rag_context(retrieval_results: Dict[str, Any]) -> str:
    """Format retrieved context for LLM injection"""
    
    context_lines = ["【知识库检索结果】\n"]
    
    for idx, result in enumerate(retrieval_results["results"], 1):
        score_pct = int(result["score"] * 100)
        doc_id = result["document_id"]
        content = result["content"][:100] + "..."
        
        context_lines.append(
            f"[文档 {idx}] {doc_id} (相关度: {score_pct}%)\n"
            f"{content}\n"
        )
    
    return "\n".join(context_lines)


def create_websocket_events() -> List[Dict[str, Any]]:
    """Create example WebSocket events for RAG workflow execution"""
    
    events = [
        {
            "type": "connected",
            "threadId": "thread-001",
            "payload": {"message": "Connected to RAG workflow executor"}
        },
        {
            "type": "run_started",
            "threadId": "thread-001",
            "payload": {
                "workflowId": "wf-001-rag-research",
                "inputSummary": "Please analyze the latest AI trends"
            }
        },
        {
            "type": "node_started",
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {"label": "Research with Knowledge Base"}
        },
        {
            "type": "node_status",
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {"status": "executing"}
        },
        {
            "type": "rag_search",  # 🆕 NEW RAG EVENT!
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {
                "query": "Please analyze the latest AI trends",
                "documentCount": 3,
                "topK": 5,
                "mode": "chunk",
                "resultsCount": 3,
                "context": """【知识库检索结果】

[文档 1] doc-rag-guide (相关度: 94%)
检索增强生成（RAG）实现指南
- RAG 核心概念...

[文档 2] doc-ai-trends-2024 (相关度: 87%)
2024 年 AI 趋势报告
- 知识库检索增强（RAG）已成为关键技术...

[文档 3] doc-workflow-design (相关度: 72%)
工作流设计最佳实践
- RAG 配置：enable_rag、knowledge_documents..."""
            }
        },
        {
            "type": "token",
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {
                "content": "基于知识库检索结果，AI ",
                "finished": False,
                "sequence": 1
            }
        },
        {
            "type": "token",
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {
                "content": "行业在2024年展现出以下主要趋势：\n\n",
                "finished": False,
                "sequence": 2
            }
        },
        {
            "type": "token",
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {
                "content": "1. RAG技术成熟度上升...",
                "finished": False,
                "sequence": 3
            }
        },
        {
            "type": "node_status",
            "threadId": "thread-001",
            "nodeId": "research-with-rag",
            "payload": {"status": "completed"}
        },
        {
            "type": "run_completed",
            "threadId": "thread-001",
            "payload": {
                "status": "completed",
                "durationMs": 3450
            }
        }
    ]
    
    return events


def demonstrate_rag_injection():
    """Demonstrate how RAG context is injected into LLM prompt"""
    
    original_prompt = "请分析2024年的AI趋势"
    
    # Simulate RAG retrieval
    retrieval_results = simulate_rag_retrieval(original_prompt)
    rag_context = format_rag_context(retrieval_results)
    
    # Inject RAG context
    injected_prompt = f"""{rag_context}

【用户问题】
{original_prompt}

请基于上述知识库信息回答问题。"""
    
    return {
        "original_prompt": original_prompt,
        "rag_context": rag_context,
        "injected_prompt": injected_prompt,
        "retrieval_results": retrieval_results
    }


def main():
    """Main demonstration"""
    
    print("\n" + "="*80)
    print("🚀 RAG 工作流集成演示 (Day 4-5)")
    print("="*80)
    
    # 1. Show workflow structure
    print("\n" + "="*80)
    print("1️⃣ 工作流结构 - 启用 RAG 的 LLM 节点")
    print("="*80)
    
    workflow = create_sample_workflow_with_rag()
    
    print(f"""
工作流 ID: {workflow['id']}
标题: {workflow['title']}

节点配置：
""")
    
    for node in workflow["nodes"]:
        print(f"  📦 {node['id']} ({node['type']})")
        if node["type"] == "llm":
            llm_config = node["data"]["llm_config"]
            print(f"     模型: {llm_config['model']}")
            print(f"     ✨ RAG 启用: {llm_config['enable_rag']}")
            print(f"     📚 知识库文档: {len(llm_config['knowledge_documents'])} 个")
            print(f"     🔍 检索模式: {llm_config['rag_mode']}")
            print(f"     📊 Top K: {llm_config['rag_top_k']}")
            print(f"     ⭐ 最小得分: {llm_config['rag_min_score']}")
    
    # 2. Show RAG retrieval simulation
    print("\n" + "="*80)
    print("2️⃣ RAG 检索过程 - 从知识库获取相关内容")
    print("="*80)
    
    rag_demo = demonstrate_rag_injection()
    
    print(f"""
原始 Prompt:
  "{rag_demo['original_prompt']}"

检索到 {len(rag_demo['retrieval_results']['results'])} 个相关文档：
""")
    
    for result in rag_demo['retrieval_results']['results']:
        score_pct = int(result['score'] * 100)
        print(f"""
  📄 {result['document_id']} (相关度: {score_pct}%)
     {result['content'][:80]}...""")
    
    # 3. Show context injection
    print("\n" + "="*80)
    print("3️⃣ 上下文注入 - 增强后的 Prompt")
    print("="*80)
    
    print(f"""
{rag_demo['injected_prompt'][:300]}...
    """)
    
    # 4. Show WebSocket events
    print("\n" + "="*80)
    print("4️⃣ WebSocket 事件流 - 执行时的实时通信")
    print("="*80)
    
    events = create_websocket_events()
    
    print(f"\n总计 {len(events)} 个事件，关键事件：\n")
    
    for event in events:
        event_type = event["type"]
        if event_type in ["rag_search", "run_started", "run_completed", "node_started"]:
            print(f"  📡 {event_type}")
            if event_type == "rag_search":
                print(f"     - 查询: {event['payload']['query'][:50]}...")
                print(f"     - 检索到: {event['payload']['resultsCount']} 个文档")
                print(f"     - 模式: {event['payload']['mode']}")
    
    # 5. Show execution flow
    print("\n" + "="*80)
    print("5️⃣ 执行流程 - 工作流执行时序")
    print("="*80)
    
    print("""
执行步骤：

1. 客户端发起工作流执行
   └─ POST /api/v1/workflows/{workflow_id}/run
   └─ 返回 threadId 和 WebSocket URL

2. WebSocket 连接建立
   └─ ws://api/ws/run/{thread_id}
   └─ 发送 "run_started" 事件

3. 执行 "research-with-rag" 节点
   ├─ 发送 "node_started" 事件
   ├─ 检查 llm_config.enable_rag = true ✨
   ├─ 执行 RAG 检索
   │  ├─ 从知识库搜索相关文档
   │  ├─ 格式化上下文
   │  └─ 发送 "rag_search" 事件 🆕
   ├─ 将 RAG 上下文注入 LLM prompt
   ├─ 调用 LLM 生成响应
   ├─ 流式返回 Token
   │  └─ 发送多个 "token" 事件
   └─ 发送 "node_status" = "completed" 事件

4. 工作流完成
   └─ 发送 "run_completed" 事件

5. WebSocket 连接关闭
    """)
    
    # 6. Show data structure
    print("\n" + "="*80)
    print("6️⃣ 数据结构 - RAG 配置的数据模型")
    print("="*80)
    
    print("""
LLMConfig 扩展了 RAG 字段：

class LLMConfig(BaseModel):
    # 基础 LLM 配置
    provider: str                              # "openai" 或 "anthropic"
    model: str                                 # 模型名称
    temperature: float                         # 温度参数
    system_prompt: Optional[str]               # 系统提示词
    
    # ✨ RAG 配置 - 新增字段
    enable_rag: bool = False                   # 是否启用 RAG
    knowledge_documents: List[str] = []        # 知识库文档 ID 列表
    rag_mode: Literal["document", "chunk"]     # 检索粒度
    rag_top_k: int = 5                         # 检索结果数量
    rag_min_score: float = 0.5                 # 最小相关性分数

WebSocket RAG 搜索事件格式：

{
    "type": "rag_search",
    "nodeId": "research-with-rag",
    "threadId": "thread-001",
    "payload": {
        "query": "用户的原始问题",
        "context": "检索到的知识库内容",
        "documentCount": 3,
        "topK": 5,
        "mode": "chunk",
        "resultsCount": 3
    }
}
    """)
    
    # 7. Show API integration
    print("\n" + "="*80)
    print("7️⃣ API 集成 - 与现有系统的集成点")
    print("="*80)
    
    print("""
现有 API：
  POST /api/v1/kb/documents              - 上传知识库文档
  GET  /api/v1/kb/documents              - 列表文档
  POST /api/v1/kb/search                 - 搜索文档（已存在）

工作流执行 API：
  POST /api/v1/workflows/{id}/run        - 执行工作流
  WS   /ws/run/{thread_id}               - WebSocket 执行流

集成点：
  ✓ StreamingLLMNodeExecutor._retrieve_rag_context()
    └─ 调用 RAGService.search_chunks()
    └─ 调用 RAGService.format_context()
  
  ✓ StreamingLLMNodeExecutor._inject_rag_context()
    └─ 在 prompt 前添加知识库上下文
  
  ✓ WebSocket 事件处理
    └─ 推送 "rag_search" 事件到前端
    └─ 前端显示检索进度和结果
    """)
    
    # 8. Show next steps
    print("\n" + "="*80)
    print("✅ 演示完成")
    print("="*80)
    
    print("""
✨ 关键改进点：

1. LLMConfig 扩展
   ├─ enable_rag: 启用/禁用 RAG
   ├─ knowledge_documents: 指定知识库
   ├─ rag_mode: 检索粒度选择
   └─ rag_top_k, rag_min_score: 调优参数

2. StreamingLLMNodeExecutor 增强
   ├─ _retrieve_rag_context(): 执行检索
   ├─ _inject_rag_context(): 注入上下文
   └─ stream_callback: 推送 RAG 事件

3. WebSocket 事件扩展
   └─ rag_search: 新增事件，显示检索进度

4. 前端集成
   ├─ 工作流编辑器显示 RAG 配置选项
   ├─ 执行面板显示检索结果
   └─ 实时展示 RAG 搜索进度

📅 实施时间表（Day 4-5）：
  - Day 4 上午：完成后端 RAG 集成（✓ 完成）
  - Day 4 下午：前端工作流编辑器集成
  - Day 5 上午：执行面板展示 RAG 结果
  - Day 5 下午：端到端测试与优化

🎯 后续优化（Week 3+）：
  - 异步后台任务队列 (Celery)
  - Redis 缓存层
  - 向量数据库索引优化
  - HITL 中断机制集成
    """)


if __name__ == "__main__":
    main()
