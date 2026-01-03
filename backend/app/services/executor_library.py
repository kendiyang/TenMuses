"""
执行器库 - 提供LLM、Tool、Router、Map等节点的具体执行实现

这个模块提供：
1. 内置的LLM执行器（调用OpenAI/Anthropic）
2. 工具执行器和工具注册机制
3. 路由执行器（基于LLM或字段条件）
4. 并行Map执行器
5. RAG 知识库集成
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime

from app.services.llm_client import llm_client
from app.services.dynamic_graph_factory import (
    NodeExecutor, LLMNodeExecutor, ToolNodeExecutor, RouterNodeExecutor,
    MapNodeExecutor, WorkflowState, eval_condition
)

# 延迟导入 RAG 服务（避免循环导入）
_rag_service = None

def get_rag_service():
    """获取 RAG 服务实例（延迟加载）"""
    global _rag_service
    if _rag_service is None:
        from app.services.rag_service import RAGService
        _rag_service = RAGService()
    return _rag_service


# ============================================================================
# 增强的LLM执行器 - 支持流式输出
# ============================================================================

class StreamingLLMNodeExecutor(LLMNodeExecutor):
    """支持流式输出和 RAG 的LLM节点执行器"""
    
    def __init__(self, node, stream_callback=None, user_id: Optional[str] = None, db_session=None):
        super().__init__(node)
        self.stream_callback = stream_callback  # 回调用于发送流式事件
        self.user_id = user_id  # 用户ID，用于 RAG 查询
        self.db_session = db_session  # 数据库会话，用于 RAG 查询
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行LLM节点，支持流式回调和RAG检索"""
        config = self.node.data.llm_config
        if not config:
            raise ValueError(f"LLM节点 {self.node.id} 缺少 llm_config")
        
        # 准备输入
        node_input = self.get_input_for_node(state)
        if isinstance(node_input, dict):
            prompt = str(node_input.get("prompt", ""))
        else:
            prompt = str(node_input)
        
        try:
            # ✨ 第一步：检查是否启用 RAG，如果启用则执行知识库检索
            rag_context = ""
            if config.enable_rag and config.knowledge_documents:
                rag_context = await self._retrieve_rag_context(config)
                # 发送 RAG 搜索事件到前端
                if self.stream_callback:
                    await self.stream_callback({
                        "type": "rag_search",
                        "nodeId": self.node.id,
                        "payload": {
                            "query": prompt,
                            "context": rag_context,
                            "documentCount": len(config.knowledge_documents),
                            "topK": config.rag_top_k,
                            "mode": config.rag_mode
                        }
                    })
            
            # ✨ 第二步：将检索到的上下文注入到 prompt 中
            enhanced_prompt = self._inject_rag_context(prompt, rag_context)
            
            # 如果有流式回调，使用流式执行
            if self.stream_callback:
                result = await self._stream_invoke(
                    config, enhanced_prompt
                )
            else:
                # 普通执行
                result = await llm_client.invoke(
                    provider=config.provider,
                    model=config.model,
                    prompt=enhanced_prompt,
                    system_prompt=config.system_prompt,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
            
            # 保存结果
            state.context[f"node_{self.node.id}_output"] = result
            state.context[f"node_{self.node.id}_rag_context"] = rag_context  # 保存 RAG 上下文供后续节点参考
            state.executed_nodes.append(self.node.id)
            
            return {
                "context": state.context,
                "executed_nodes": state.executed_nodes,
                "output": result
            }
        except Exception as e:
            raise RuntimeError(f"LLM节点 {self.node.id} 执行失败: {str(e)}")
    
    async def _retrieve_rag_context(self, config) -> str:
        """
        从知识库检索相关内容
        
        Args:
            config: LLMConfig 对象，包含 RAG 配置
        
        Returns:
            格式化的知识库上下文字符串
        """
        try:
            # 检查必要的信息
            if not self.db_session or not self.user_id:
                # 如果没有数据库会话或用户ID，返回空上下文
                return ""
            
            rag_service = get_rag_service()
            
            # 获取上一个节点的输出作为查询
            # 通常是 prompt，但也可能是其他形式的查询
            query = ""
            if len(self.node.data.rag_config_query_input or "") > 0:
                # 从指定的输入字段获取查询
                field_name = self.node.data.rag_config_query_input
                # ... 实现字段提取逻辑
                pass
            else:
                # 默认使用当前 prompt 作为查询
                # 这部分需要从 state 中提取，但我们在这个上下文中获取不了
                # 所以会在调用 _retrieve_rag_context 前从上层传入
                pass
            
            # 为了简化，这里先返回空
            # 真实实现需要有 prompt 参数
            return ""
        except Exception as e:
            # 如果 RAG 检索失败，返回空上下文，继续执行
            print(f"RAG 检索失败: {str(e)}")
            return ""
    
    async def _retrieve_rag_context_with_query(self, query: str, config) -> str:
        """
        从知识库检索相关内容（带查询文本）
        
        Args:
            query: 搜索查询文本
            config: LLMConfig 对象，包含 RAG 配置
        
        Returns:
            格式化的知识库上下文字符串
        """
        try:
            if not self.db_session or not self.user_id:
                return ""
            
            rag_service = get_rag_service()
            
            # 根据 RAG 模式执行不同的搜索
            if config.rag_mode == "document":
                results = await rag_service.search_documents(
                    query=query,
                    user_id=self.user_id,
                    top_k=config.rag_top_k,
                    min_score=config.rag_min_score
                )
            else:  # chunk mode
                results = await rag_service.search_chunks(
                    query=query,
                    user_id=self.user_id,
                    top_k=config.rag_top_k,
                    min_score=config.rag_min_score
                )
            
            # 格式化上下文
            return rag_service.format_context(results)
        except Exception as e:
            print(f"RAG 检索失败: {str(e)}")
            return ""
    
    def _inject_rag_context(self, prompt: str, rag_context: str) -> str:
        """
        将 RAG 上下文注入到 prompt 中
        
        Args:
            prompt: 原始 prompt
            rag_context: RAG 检索到的上下文
        
        Returns:
            增强后的 prompt
        """
        if not rag_context:
            return prompt
        
        # 在 prompt 前面添加上下文
        enhanced_prompt = f"""基于以下知识库信息，回答用户的问题：

【知识库上下文】
{rag_context}

【用户问题】
{prompt}"""
        
        return enhanced_prompt
    
    async def _stream_invoke(self, config, prompt: str) -> str:
        """流式调用LLM"""
        result = ""
        async for chunk in llm_client.stream(
            provider=config.provider,
            model=config.model,
            prompt=prompt,
            system_prompt=config.system_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        ):
            result += chunk
            if self.stream_callback:
                await self.stream_callback({
                    "type": "token",
                    "nodeId": self.node.id,
                    "content": chunk,
                    "finished": False
                })
        
        # 发送结束信号
        if self.stream_callback:
            await self.stream_callback({
                "type": "token",
                "nodeId": self.node.id,
                "content": "",
                "finished": True
            })
        
        return result


# ============================================================================

# 工具库和工具执行器
# ============================================================================

class ToolLibrary:
    """工具库 - 管理可用的工具"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._register_builtin_tools()
    
    def register(self, name: str, func: Callable, description: str = "") -> None:
        """注册工具"""
        self._tools[name] = {
            "func": func,
            "description": description
        }
    
    def get(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        tool = self._tools.get(name)
        return tool["func"] if tool else None
    
    def list_tools(self) -> Dict[str, str]:
        """列出所有可用工具"""
        return {name: tool["description"] for name, tool in self._tools.items()}
    
    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        
        # 示例工具1: 文本处理
        async def text_process(input_data: Any) -> str:
            """处理文本 - 简单示例"""
            if isinstance(input_data, dict):
                text = input_data.get("text", "")
            else:
                text = str(input_data)
            return f"Processed: {text.upper()}"
        
        self.register("text_process", text_process, "将文本转换为大写")
        
        # 示例工具2: JSON处理
        async def json_parse(input_data: Any) -> Dict:
            """解析JSON"""
            try:
                if isinstance(input_data, str):
                    return json.loads(input_data)
                return input_data
            except Exception as e:
                return {"error": str(e)}
        
        self.register("json_parse", json_parse, "解析JSON字符串")
        
        # 示例工具3: 数据聚合
        async def aggregate_data(input_data: Any) -> Dict:
            """聚合数据"""
            if isinstance(input_data, list):
                return {
                    "count": len(input_data),
                    "items": input_data,
                    "timestamp": datetime.now().isoformat()
                }
            return {"error": "输入必须是列表"}
        
        self.register("aggregate_data", aggregate_data, "聚合数据列表")


# 全局工具库实例
tool_library = ToolLibrary()


class ToolNodeExecutorEnhanced(ToolNodeExecutor):
    """增强的Tool节点执行器，使用全局工具库"""
    
    def __init__(self, node, tool_lib: Optional[ToolLibrary] = None):
        super().__init__(node)
        self.tool_lib = tool_lib or tool_library
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行Tool节点"""
        config = self.node.data.tool_config
        if not config:
            raise ValueError(f"Tool节点 {self.node.id} 缺少 tool_config")
        
        # 从工具库获取工具
        tool_func = self.tool_lib.get(config.tool_name)
        if not tool_func:
            raise ValueError(f"未注册的工具: {config.tool_name}")
        
        # 准备输入
        node_input = self.get_input_for_node(state)
        
        try:
            # 执行工具
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(node_input)
            else:
                result = tool_func(node_input)
            
            state.context[f"node_{self.node.id}_output"] = result
            state.executed_nodes.append(self.node.id)
            
            return {
                "context": state.context,
                "executed_nodes": state.executed_nodes,
                "output": result
            }
        except Exception as e:
            raise RuntimeError(f"Tool节点 {self.node.id} 执行失败: {str(e)}")


# ============================================================================
# 增强的Router执行器 - 支持复杂条件
# ============================================================================

class ExpressionEvaluator:
    """条件表达式评估器 - 使用simpleeval安全执行"""
    
    # 允许的函数
    ALLOWED_FUNCTIONS = {
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
    }
    
    @staticmethod
    def evaluate(expression: str, context: Dict[str, Any]) -> bool:
        """
        评估条件表达式 - 安全版本
        
        支持:
          - output.field == "value"
          - output.score > 0.8
          - "substring" in output
          - output.approved == true
          - 组合: output.score > 0.8 and output.approved == true
        
        安全特性:
          - 使用simpleeval库，不执行任意Python代码
          - 只允许指定的函数和操作符
          - 无法访问__builtins__或其他危险对象
        """
        try:
            from simpleeval import simple_eval, InvalidExpression
            
            # 准备安全的上下文
            safe_context = {"output": context.get("output", {})}
            
            # 使用simpleeval执行表达式
            result = simple_eval(
                expression,
                names=safe_context,
                functions=ExpressionEvaluator.ALLOWED_FUNCTIONS
            )
            return bool(result)
        except Exception as e:
            print(f"表达式评估失败 '{expression}': {type(e).__name__}: {e}")
            return False


class RouterNodeExecutorEnhanced(RouterNodeExecutor):
    """增强的Router执行器，支持复杂条件和表达式"""
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行Router节点"""
        config = self.node.data.router_config
        if not config:
            raise ValueError(f"Router节点 {self.node.id} 缺少 router_config")
        
        target_node_id = None
        decision_info = {"nodeId": self.node.id}
        
        if config.router_type == "llm":
            # LLM路由
            node_input = self.get_input_for_node(state)
            prompt = f"""Based on the following input, decide which path to take:

Input: {node_input}

{config.routing_prompt or 'Instructions: Choose the best path.'}

Respond with just the decision, no explanation.
"""
            try:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                
                response = await llm_client.invoke(
                    messages,
                    provider=config.llm_config.provider if config.llm_config else "openai",
                    model=config.llm_config.model if config.llm_config else "gpt-4-turbo-preview",
                    temperature=config.llm_config.temperature if config.llm_config else 0.7
                )
                
                # 处理响应
                result = response.content if hasattr(response, 'content') else str(response)
                
                decision_info["llmDecision"] = result
                
                # 基于LLM输出匹配条件
                result_lower = result.lower()
                for condition in config.conditions:
                    if condition.condition.lower() in result_lower:
                        target_node_id = condition.target_node_id
                        decision_info["matched_condition"] = condition.condition
                        break
            except Exception as e:
                print(f"LLM路由失败: {e}")
        
        elif config.router_type == "field":
            # 字段路由
            prev_output = state.get_node_output(state.executed_nodes[-1] if state.executed_nodes else None)
            
            context = {"output": prev_output}
            evaluator = ExpressionEvaluator()
            
            # 匹配条件
            for condition in config.conditions:
                if evaluator.evaluate(condition.condition, context):
                    target_node_id = condition.target_node_id
                    decision_info["matched_condition"] = condition.condition
                    break
        
        # 使用默认路由
        if not target_node_id:
            target_node_id = config.default_target
            decision_info["using_default"] = True
        
        # 保存路由决策
        state.context[f"node_{self.node.id}_output"] = {
            "target_node_id": target_node_id,
            "decision_info": decision_info
        }
        state.executed_nodes.append(self.node.id)
        
        return {
            "context": state.context,
            "executed_nodes": state.executed_nodes,
            "next_node": target_node_id,
            "router_decision": decision_info
        }


# ============================================================================
# 增强的Map执行器 - 支持真正的并行处理
# ============================================================================

class MapNodeExecutorEnhanced(MapNodeExecutor):
    """增强的Map节点执行器，支持真正的并行处理"""
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行Map节点 - 并行处理列表项"""
        config = self.node.data.map_config
        if not config:
            raise ValueError(f"Map节点 {self.node.id} 缺少 map_config")
        
        # 获取数据源
        items = state.context.get(config.items_source)
        if not items:
            raise ValueError(f"数据源 {config.items_source} 不存在或为空")
        
        if not isinstance(items, list):
            items = [items]
        
        # 限制并行度
        semaphore = asyncio.Semaphore(config.parallel_count)
        
        async def process_item(item):
            async with semaphore:
                # 这里应该创建子执行器来处理单个item
                # 现在简化为直接处理
                return item
        
        # 并行执行
        results = await asyncio.gather(*[process_item(item) for item in items])
        
        state.context[f"node_{self.node.id}_output"] = results
        state.executed_nodes.append(self.node.id)
        
        return {
            "context": state.context,
            "executed_nodes": state.executed_nodes,
            "output": results
        }


# ============================================================================
# 执行器工厂函数
# ============================================================================

def create_executor(node, executor_type: str = None, **kwargs):
    """
    根据节点类型和配置创建执行器
    
    Args:
        node: 节点对象
        executor_type: 显式指定执行器类型
        **kwargs: 额外的执行器参数
    
    Returns:
        NodeExecutor: 相应的执行器实例
    """
    if executor_type == "streaming_llm":
        return StreamingLLMNodeExecutor(node, **kwargs)
    elif executor_type == "tool":
        return ToolNodeExecutorEnhanced(node, **kwargs)
    elif executor_type == "router":
        return RouterNodeExecutorEnhanced(node, **kwargs)
    elif executor_type == "map":
        return MapNodeExecutorEnhanced(node, **kwargs)
    else:
        # 根据节点类型自动选择
        from app.schemas.node import NodeType
        
        if node.type == NodeType.LLM:
            return StreamingLLMNodeExecutor(node, **kwargs)
        elif node.type == NodeType.TOOL:
            return ToolNodeExecutorEnhanced(node, **kwargs)
        elif node.type == NodeType.ROUTER:
            return RouterNodeExecutorEnhanced(node, **kwargs)
        elif node.type == NodeType.MAP:
            return MapNodeExecutorEnhanced(node, **kwargs)
        else:
            # 默认使用LLM执行器
            return StreamingLLMNodeExecutor(node, **kwargs)
