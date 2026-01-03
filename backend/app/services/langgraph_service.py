from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from app.services.llm_client import llm_client

# Define the state for our workflow
class WorkflowState(TypedDict):
    """State for the workflow execution."""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    research_results: str
    draft_content: str
    final_content: str
    current_step: str

class LangGraphService:
    """Service for creating and executing LangGraph workflows."""
    
    def __init__(self):
        self.graph = None
    
    def create_static_workflow(self):
        """Create a static workflow: Research → Writer → Reviewer."""
        
        # Define node functions
        async def research_node(state: WorkflowState) -> WorkflowState:
            """Research node: Gather information on the topic."""
            messages = state.get("messages", [])
            
            # Get the user's query
            user_query = messages[-1].content if messages else "AI trends"
            
            # Create research prompt
            research_prompt = f"""You are a research assistant. Research the following topic and provide key findings:
            
Topic: {user_query}

Provide 3-5 key points with brief explanations."""
            
            # Call LLM
            response = await llm_client.invoke(
                [HumanMessage(content=research_prompt)],
                provider="openai",
                model="gpt-4o",
                temperature=0.7
            )
            
            research_results = response.content
            
            return {
                **state,
                "research_results": research_results,
                "current_step": "research_completed",
                "messages": messages + [AIMessage(content=f"Research completed: {research_results[:100]}...")]
            }
        
        async def writer_node(state: WorkflowState) -> WorkflowState:
            """Writer node: Generate content based on research."""
            research_results = state.get("research_results", "")
            messages = state.get("messages", [])
            
            # Create writing prompt
            writing_prompt = f"""You are a content writer. Based on the following research, write a comprehensive article:

Research Results:
{research_results}

Write a well-structured article with an introduction, main points, and conclusion."""
            
            # Call LLM
            response = await llm_client.invoke(
                [HumanMessage(content=writing_prompt)],
                provider="openai",
                model="gpt-4o",
                temperature=0.8
            )
            
            draft_content = response.content
            
            return {
                **state,
                "draft_content": draft_content,
                "current_step": "writing_completed",
                "messages": messages + [AIMessage(content=f"Draft completed: {draft_content[:100]}...")]
            }
        
        async def reviewer_node(state: WorkflowState) -> WorkflowState:
            """Reviewer node: Review and refine the content."""
            draft_content = state.get("draft_content", "")
            messages = state.get("messages", [])
            
            # Create review prompt
            review_prompt = f"""You are an editor. Review the following article and provide an improved version:

Draft Article:
{draft_content}

Improve clarity, fix any errors, and enhance the overall quality."""
            
            # Call LLM
            response = await llm_client.invoke(
                [HumanMessage(content=review_prompt)],
                provider="openai",
                model="gpt-4o",
                temperature=0.5
            )
            
            final_content = response.content
            
            return {
                **state,
                "final_content": final_content,
                "current_step": "review_completed",
                "messages": messages + [AIMessage(content=f"Review completed. Final article ready.")]
            }
        
        # Build the graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("research", research_node)
        workflow.add_node("writer", writer_node)
        workflow.add_node("reviewer", reviewer_node)
        
        # Add edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "writer")
        workflow.add_edge("writer", "reviewer")
        workflow.add_edge("reviewer", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        
        return self.graph
    
    async def execute_workflow(self, input_text: str):
        """Execute the workflow with the given input."""
        if not self.graph:
            self.create_static_workflow()
        
        # Initialize state
        initial_state: WorkflowState = {
            "messages": [HumanMessage(content=input_text)],
            "research_results": "",
            "draft_content": "",
            "final_content": "",
            "current_step": "started"
        }
        
        # Execute the workflow
        result = await self.graph.ainvoke(initial_state)
        
        return result
    
    async def stream_workflow(self, input_text: str):
        """Stream the workflow execution."""
        if not self.graph:
            self.create_static_workflow()
        
        # Initialize state
        initial_state: WorkflowState = {
            "messages": [HumanMessage(content=input_text)],
            "research_results": "",
            "draft_content": "",
            "final_content": "",
            "current_step": "started"
        }
        
        # Stream events
        async for event in self.graph.astream_events(initial_state, version="v1"):
            yield event

# Global instance
langgraph_service = LangGraphService()
