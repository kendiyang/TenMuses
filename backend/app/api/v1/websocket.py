from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json
import asyncio

from app.core.database import get_db
from app.models.workflow import WorkflowRun, RunStatus
from app.services.langgraph_service import langgraph_service

router = APIRouter()

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, thread_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[thread_id] = websocket
    
    def disconnect(self, thread_id: str):
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]
    
    async def send_message(self, thread_id: str, message: dict):
        if thread_id in self.active_connections:
            await self.active_connections[thread_id].send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/run/{thread_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    thread_id: UUID,
):
    """WebSocket endpoint for workflow execution streaming."""
    thread_id_str = str(thread_id)
    
    await manager.connect(thread_id_str, websocket)
    
    try:
        # Send initial connection message
        await manager.send_message(thread_id_str, {
            "type": "connected",
            "threadId": thread_id_str,
            "payload": {"message": "Connected to execution stream"}
        })
        
        # Wait for start command
        data = await websocket.receive_json()
        
        if data.get("action") == "start":
            input_text = data.get("input", "Generate an article about AI trends")
            
            # Send run started event
            await manager.send_message(thread_id_str, {
                "type": "run_started",
                "threadId": thread_id_str,
                "payload": {
                    "inputSummary": input_text[:200]
                }
            })
            
            # Execute workflow and stream events
            try:
                current_node = None
                
                # Stream events from langgraph workflow
                async for event in langgraph_service.stream_workflow(input_text):
                    event_type = event.get("event")
                    
                    # Handle different event types
                    if event_type == "on_chain_start":
                        node_name = event.get("name", "")
                        if node_name in ["research", "writer", "reviewer"]:
                            current_node = node_name
                            await manager.send_message(thread_id_str, {
                                "type": "node_started",
                                "threadId": thread_id_str,
                                "nodeId": node_name,
                                "payload": {
                                    "label": node_name.capitalize()
                                }
                            })
                            
                            await manager.send_message(thread_id_str, {
                                "type": "node_status",
                                "threadId": thread_id_str,
                                "nodeId": node_name,
                                "payload": {
                                    "status": "executing"
                                }
                            })
                    
                    elif event_type == "on_chain_end":
                        node_name = event.get("name", "")
                        if node_name in ["research", "writer", "reviewer"]:
                            await manager.send_message(thread_id_str, {
                                "type": "node_status",
                                "threadId": thread_id_str,
                                "nodeId": node_name,
                                "payload": {
                                    "status": "completed"
                                }
                            })
                    
                    elif event_type == "on_chat_model_stream":
                        # Stream tokens
                        data = event.get("data", {})
                        chunk = data.get("chunk")
                        
                        # chunk 可能是 AIMessageChunk 对象或字典
                        if chunk:
                            # 尝试从对象获取 content 属性
                            content = ""
                            if hasattr(chunk, "content"):
                                content = chunk.content
                            elif isinstance(chunk, dict):
                                content = chunk.get("content", "")
                            
                            if content and current_node:
                                await manager.send_message(thread_id_str, {
                                    "type": "token",
                                    "threadId": thread_id_str,
                                    "nodeId": current_node,
                                    "payload": {
                                        "content": content,
                                        "finished": False
                                    }
                                })
                
                # Send completion event
                await manager.send_message(thread_id_str, {
                    "type": "run_completed",
                    "threadId": thread_id_str,
                    "payload": {
                        "status": "completed",
                        "durationMs": 0
                    }
                })
                
            except Exception as e:
                # Send error event
                await manager.send_message(thread_id_str, {
                    "type": "error",
                    "threadId": thread_id_str,
                    "payload": {
                        "message": str(e),
                        "code": "EXECUTION_ERROR",
                        "fatal": True
                    }
                })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(thread_id_str)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(thread_id_str)
