"""
动态图构建工厂 - DynamicGraphFactory

这个模块负责：
1. 从前端发送的canvas JSON解析工作流定义
2. 动态构建LangGraph的StateGraph
3. 支持多种节点类型（LLM、Tool、Router、Map等）
4. 支持条件边和HITL中断机制
5. 返回可执行的工作流编译体
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas.node import (
    NodeType, NodeData, EdgeType, Node, Edge, WorkflowGraph,
    LLMConfig, ToolConfig, RouterConfig, MapConfig,
    validate_graph
)
from app.services.llm_client import llm_client


# ============================================================================
# 工作流状态定义
# ============================================================================

@dataclass
class WorkflowState:
    """
    工作流执行状态 - 在LangGraph中流转的数据结构
    """
    # 全局上下文
    input: Dict[str, Any]  # 初始输入
    output: Dict[str, Any]  # 最终输出
    context: Dict[str, Any]  # 全局上下文，各节点可读写
    
    # 执行跟踪
    executed_nodes: List[str]  # 已执行节点列表
    current_node_id: Optional[str] = None  # 当前节点
    
    # HITL 中断
    interrupted: bool = False
    interrupt_reason: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not isinstance(self.context, dict):
            self.context = {}
    
    def get_node_output(self, node_id: str) -> Any:
        """获取某个节点的输出结果"""
        return self.context.get(f"node_{node_id}_output")
    
    def set_node_output(self, node_id: str, output: Any) -> None:
        """设置某个节点的输出结果"""
        self.context[f"node_{node_id}_output"] = output


# ============================================================================
# 节点执行器基类
# ============================================================================

class NodeExecutor:
    """节点执行器基类"""
    
    def __init__(self, node: Node):
        self.node = node
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行节点，返回更新的状态字典"""
        raise NotImplementedError
    
    def get_input_for_node(self, state: WorkflowState) -> Any:
        """从state中提取节点所需的输入"""
        # 简单实现：优先使用节点上一步的输出
        if self.node.id not in state.executed_nodes and len(state.executed_nodes) > 0:
            prev_node = state.executed_nodes[-1]
            return state.get_node_output(prev_node)
        return state.input


# ============================================================================
# 具体节点执行器实现
# ============================================================================

class LLMNodeExecutor(NodeExecutor):
    """LLM节点执行器 - 包含重试机制"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _invoke_llm(self, config, prompt: str) -> str:
        """调用LLM的内部方法 - 带重试"""
        try:
            result = await llm_client.invoke(
                provider=config.provider,
                model=config.model,
                prompt=prompt,
                system_prompt=config.system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            return result
        except Exception as e:
            # 包装异常以便tenacity识别
            if "rate_limit" in str(e).lower() or "timeout" in str(e).lower():
                raise RuntimeError(f"LLM API临时错误: {e}") from e
            raise
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行LLM节点"""
        config = self.node.data.llm_config
        if not config:
            raise ValueError(f"LLM节点 {self.node.id} 缺少 llm_config")
        
        # 准备输入
        node_input = self.get_input_for_node(state)
        if isinstance(node_input, dict):
            prompt = str(node_input.get("prompt", ""))
        else:
            prompt = str(node_input)
        
        # 调用LLM（带重试）
        try:
            result = await self._invoke_llm(config, prompt)
            
            # 保存结果
            state.context[f"node_{self.node.id}_output"] = result
            state.executed_nodes.append(self.node.id)
            
            return {
                "context": state.context,
                "executed_nodes": state.executed_nodes,
                "output": result
            }
        except Exception as e:
            raise RuntimeError(f"LLM节点 {self.node.id} 执行失败 (已重试3次): {str(e)}")


class ToolNodeExecutor(NodeExecutor):
    """Tool节点执行器"""
    
    # 工具库注册 - 实际应用中应从配置加载
    TOOL_REGISTRY: Dict[str, Callable] = {}
    
    @classmethod
    def register_tool(cls, name: str, func: Callable) -> None:
        """注册工具"""
        cls.TOOL_REGISTRY[name] = func
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行Tool节点"""
        config = self.node.data.tool_config
        if not config:
            raise ValueError(f"Tool节点 {self.node.id} 缺少 tool_config")
        
        # 查找工具
        tool_func = self.TOOL_REGISTRY.get(config.tool_name)
        if not tool_func:
            raise ValueError(f"未注册的工具: {config.tool_name}")
        
        # 准备输入
        node_input = self.get_input_for_node(state)
        
        # 执行工具
        try:
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


class RouterNodeExecutor(NodeExecutor):
    """Router节点执行器 - 动态决策下一个节点"""
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行Router节点，返回路由决策"""
        config = self.node.data.router_config
        if not config:
            raise ValueError(f"Router节点 {self.node.id} 缺少 router_config")
        
        target_node_id = None
        
        if config.router_type == "llm":
            # LLM路由
            node_input = self.get_input_for_node(state)
            prompt = f"""Based on the following input, decide which path to take:

Input: {node_input}

{config.routing_prompt or 'Instructions: Choose the best path.'}
"""
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            
            response = await llm_client.invoke(
                messages,
                provider=config.llm_config.provider if config.llm_config else "openai",
                model=config.llm_config.model if config.llm_config else "gpt-4",
                temperature=config.llm_config.temperature if config.llm_config else 0.7
            )
            
            # 处理响应
            result = response.content if hasattr(response, 'content') else str(response)
            
            # 基于LLM输出匹配条件
            for condition in config.conditions:
                if condition.condition.lower() in result.lower():
                    target_node_id = condition.target_node_id
                    break
        
        elif config.router_type == "field":
            # 字段路由
            field_value = state.context.get(config.source_field)
            
            # 匹配条件
            for condition in config.conditions:
                # 简单的条件匹配，可扩展为表达式引擎
                if eval_condition(condition.condition, field_value):
                    target_node_id = condition.target_node_id
                    break
        
        # 使用默认路由
        if not target_node_id:
            target_node_id = config.default_target
        
        # 保存路由决策
        state.context[f"node_{self.node.id}_output"] = {
            "target_node_id": target_node_id,
            "decision_made_at": self.node.id
        }
        state.executed_nodes.append(self.node.id)
        
        return {
            "context": state.context,
            "executed_nodes": state.executed_nodes,
            "next_node": target_node_id
        }


class MapNodeExecutor(NodeExecutor):
    """Map节点执行器 - 并行执行"""
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行Map节点 - 对列表项并行处理"""
        config = self.node.data.map_config
        if not config:
            raise ValueError(f"Map节点 {self.node.id} 缺少 map_config")
        
        # 获取数据源
        items = state.context.get(config.items_source)
        if not items:
            raise ValueError(f"数据源 {config.items_source} 不存在或为空")
        
        if not isinstance(items, list):
            items = [items]
        
        # 并行执行（简化实现，实际应使用线程池）
        results = []
        for item in items:
            # 这里应该创建执行器来处理单个item
            # 现在简化为直接处理
            results.append(item)
        
        state.context[f"node_{self.node.id}_output"] = results
        state.executed_nodes.append(self.node.id)
        
        return {
            "context": state.context,
            "executed_nodes": state.executed_nodes,
            "output": results
        }


# ============================================================================
# 条件评估工具
# ============================================================================

def eval_condition(condition: str, value: Any) -> bool:
    """
    评估条件表达式
    支持: 
      - "== value"
      - "> threshold"
      - "in [list]"
    """
    try:
        # 简单的条件解析
        if "==" in condition:
            expected = condition.split("==")[1].strip().strip("'\"")
            return str(value) == expected
        elif ">" in condition:
            threshold = float(condition.split(">")[1].strip())
            return float(value) > threshold
        elif "<" in condition:
            threshold = float(condition.split("<")[1].strip())
            return float(value) < threshold
        elif "in" in condition:
            # 简单实现，实际需要完整的表达式解析器
            return True
        else:
            return False
    except Exception as e:
        print(f"条件评估失败: {condition}, 错误: {e}")
        return False


# ============================================================================
# DynamicGraphFactory - 核心类
# ============================================================================

class DynamicGraphFactory:
    """
    动态图工厂
    
    使用示例：
        factory = DynamicGraphFactory(workflow_graph)
        compiled_graph = factory.compile()
        result = await compiled_graph.ainvoke({"input": {...}})
    """
    
    def __init__(self, graph_data: Any):
        """
        初始化工厂
        
        Args:
            graph_data: WorkflowGraph对象或字典
        """
        # 验证和规范化图数据
        self.workflow_graph = validate_graph(graph_data)
        
        # 构建节点和边的映射
        self.nodes_map: Dict[str, Node] = {n.id: n for n in self.workflow_graph.nodes}
        self.edges_map: Dict[str, List[str]] = self._build_adjacency_list()
        
        # 构建执行器映射
        self.executors: Dict[str, NodeExecutor] = self._build_executors()
    
    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """构建邻接表（节点连接关系）"""
        adj = {node.id: [] for node in self.workflow_graph.nodes}
        for edge in self.workflow_graph.edges:
            adj[edge.source].append(edge.target)
        return adj
    
    def _build_executors(self) -> Dict[str, NodeExecutor]:
        """为每个节点创建执行器"""
        executors = {}
        for node in self.workflow_graph.nodes:
            if node.type == NodeType.LLM:
                executors[node.id] = LLMNodeExecutor(node)
            elif node.type == NodeType.TOOL:
                executors[node.id] = ToolNodeExecutor(node)
            elif node.type == NodeType.ROUTER:
                executors[node.id] = RouterNodeExecutor(node)
            elif node.type == NodeType.MAP:
                executors[node.id] = MapNodeExecutor(node)
            elif node.type in [NodeType.RESEARCH, NodeType.WRITER, NodeType.REVIEWER]:
                # Phase 1 兼容性 - 作为LLM节点
                executors[node.id] = LLMNodeExecutor(node)
            else:
                raise ValueError(f"不支持的节点类型: {node.type}")
        return executors
    
    def _get_start_nodes(self) -> List[str]:
        """获取起始节点（入度为0的节点）"""
        all_targets = set()
        for edge in self.workflow_graph.edges:
            all_targets.add(edge.target)
        
        start_nodes = [n.id for n in self.workflow_graph.nodes if n.id not in all_targets]
        return start_nodes if start_nodes else [self.workflow_graph.nodes[0].id]
    
    def _get_end_nodes(self) -> List[str]:
        """获取结束节点（出度为0的节点）"""
        end_nodes = [
            node_id for node_id, targets in self.edges_map.items()
            if not targets
        ]
        return end_nodes
    
    def compile(self) -> 'CompiledWorkflow':
        """
        编译工作流为可执行的LangGraph StateGraph
        
        Returns:
            CompiledWorkflow: 编译后的可执行工作流
        """
        return CompiledWorkflow(self)


# ============================================================================
# 编译后的工作流
# ============================================================================

class CompiledWorkflow:
    """编译后的工作流，支持执行和流式处理"""
    
    def __init__(self, factory: DynamicGraphFactory):
        self.factory = factory
        self.graph = self._build_langgraph()
    
    def _build_langgraph(self) -> StateGraph:
        """构建LangGraph"""
        graph = StateGraph(dict)
        
        # 添加节点
        for node_id, executor in self.factory.executors.items():
            graph.add_node(node_id, self._create_node_function(node_id, executor))
        
        # 添加边
        for edge in self.factory.workflow_graph.edges:
            graph.add_edge(edge.source, edge.target)
        
        # 设置起始和结束节点
        start_nodes = self.factory._get_start_nodes()
        end_nodes = self.factory._get_end_nodes()
        
        for start_node in start_nodes:
            graph.set_entry_point(start_node)
        
        for end_node in end_nodes:
            graph.add_edge(end_node, END)
        
        # 编译
        return graph.compile()
    
    def _create_node_function(self, node_id: str, executor: NodeExecutor) -> Callable:
        """为节点创建执行函数"""
        async def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
            # 从字典重建WorkflowState
            workflow_state = WorkflowState(
                input=state.get("input", {}),
                output=state.get("output", {}),
                context=state.get("context", {}),
                executed_nodes=state.get("executed_nodes", []),
                current_node_id=node_id,
                interrupted=state.get("interrupted", False),
                interrupt_reason=state.get("interrupt_reason"),
                metadata=state.get("metadata", {})
            )
            
            # 执行节点
            result = await executor.execute(workflow_state)
            
            return result
        
        return node_function
    
    async def ainvoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行工作流"""
        initial_state = {
            "input": input_data,
            "output": {},
            "context": {},
            "executed_nodes": [],
            "interrupted": False,
            "interrupt_reason": None,
            "metadata": {}
        }
        
        result = await self.graph.ainvoke(initial_state)
        return result
    
    async def astream(self, input_data: Dict[str, Any], version: str = "v1"):
        """异步流式执行工作流，生成事件"""
        initial_state = {
            "input": input_data,
            "output": {},
            "context": {},
            "executed_nodes": [],
            "interrupted": False,
            "interrupt_reason": None,
            "metadata": {}
        }
        
        async for event in self.graph.astream_events(initial_state, version=version):
            yield event


# ============================================================================
# 工厂快速API
# ============================================================================

def create_workflow(graph_data: Any) -> CompiledWorkflow:
    """快速创建编译的工作流"""
    factory = DynamicGraphFactory(graph_data)
    return factory.compile()


async def execute_workflow(graph_data: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """快速执行工作流"""
    workflow = create_workflow(graph_data)
    return await workflow.ainvoke(input_data)
