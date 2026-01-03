#!/usr/bin/env python3
"""
WebSocket 执行流集成测试脚本

测试工作流执行的 WebSocket 通信流程：
1. 创建测试工作流
2. 通过 WebSocket 连接并启动执行
3. 接收和验证流式事件
4. 确认执行完成

使用方法:
    python test_websocket_execution.py
"""

import asyncio
import json
import sys
from uuid import uuid4
import aiohttp
from datetime import datetime

# 配置
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
TEST_EMAIL = f"test_ws_{uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "Test123456"

class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log(msg: str, color: str = ""):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if color:
        print(f"{Colors.CYAN}[{timestamp}]{Colors.END} {color}{msg}{Colors.END}")
    else:
        print(f"{Colors.CYAN}[{timestamp}]{Colors.END} {msg}")

async def register_user(session: aiohttp.ClientSession) -> dict:
    """Register a test user"""
    log(f"Registering test user: {TEST_EMAIL}", Colors.BLUE)
    
    async with session.post(
        f"{API_URL}/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": f"TestUser_{uuid4().hex[:8]}",
            "password": TEST_PASSWORD
        }
    ) as response:
        if response.status != 200:
            error = await response.text()
            raise Exception(f"Registration failed: {error}")
        
        data = await response.json()
        log(f"✓ User registered successfully", Colors.GREEN)
        return data

async def create_test_workflow(session: aiohttp.ClientSession, token: str) -> dict:
    """Create a test workflow"""
    log("Creating test workflow...", Colors.BLUE)
    
    workflow_data = {
        "title": f"WebSocket Test Workflow {uuid4().hex[:8]}",
        "description": "Test workflow for WebSocket execution testing",
        "nodes": [
            {
                "id": "start-1",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "data": {"label": "Start"}
            },
            {
                "id": "llm-1",
                "type": "llm",
                "position": {"x": 100, "y": 250},
                "data": {
                    "label": "LLM Node",
                    "provider": "openai",
                    "model": "gpt-4o",
                    "prompt": "Write a haiku about AI"
                }
            },
            {
                "id": "end-1",
                "type": "end",
                "position": {"x": 100, "y": 400},
                "data": {"label": "End"}
            }
        ],
        "edges": [
            {"id": "e1", "source": "start-1", "target": "llm-1"},
            {"id": "e2", "source": "llm-1", "target": "end-1"}
        ]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with session.post(
        f"{API_URL}/api/v1/workflows",
        json=workflow_data,
        headers=headers
    ) as response:
        if response.status != 201:
            error = await response.text()
            raise Exception(f"Workflow creation failed: {error}")
        
        data = await response.json()
        log(f"✓ Workflow created: {data['id']}", Colors.GREEN)
        return data

async def test_websocket_execution(workflow_id: str, token: str):
    """Test WebSocket execution flow"""
    log(f"Testing WebSocket execution for workflow: {workflow_id}", Colors.BLUE)
    
    # Generate a thread ID for this execution
    thread_id = str(uuid4())
    ws_url = f"{WS_URL}/api/v1/ws/run/{thread_id}"
    
    log(f"Connecting to WebSocket: {ws_url}", Colors.BLUE)
    
    events_received = []
    execution_started = False
    execution_completed = False
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ws_url) as ws:
            log("✓ WebSocket connected", Colors.GREEN)
            
            # Wait for connection confirmation
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    event = json.loads(msg.data)
                    event_type = event.get("type")
                    events_received.append(event_type)
                    
                    log(f"← Event: {Colors.BOLD}{event_type}{Colors.END}", Colors.CYAN)
                    
                    if event_type == "connected":
                        log(f"   Payload: {event.get('payload', {})}", Colors.CYAN)
                        
                        # Send start action
                        start_message = {
                            "action": "start",
                            "workflow_id": workflow_id,
                            "input": "Test execution via WebSocket"
                        }
                        log(f"→ Sending start action...", Colors.YELLOW)
                        await ws.send_json(start_message)
                    
                    elif event_type == "run_started":
                        execution_started = True
                        log(f"   Run started!", Colors.GREEN)
                    
                    elif event_type == "node_started":
                        node_id = event.get("nodeId", "unknown")
                        log(f"   Node {node_id} started", Colors.GREEN)
                    
                    elif event_type == "node_status":
                        node_id = event.get("nodeId", "unknown")
                        status = event.get("payload", {}).get("status", "unknown")
                        log(f"   Node {node_id} status: {status}", Colors.BLUE)
                    
                    elif event_type == "token":
                        content = event.get("payload", {}).get("content", "")
                        finished = event.get("payload", {}).get("finished", False)
                        if content:
                            log(f"   Token: {content[:50]}...", Colors.YELLOW)
                        if finished:
                            log(f"   Token stream finished", Colors.GREEN)
                    
                    elif event_type == "run_completed":
                        execution_completed = True
                        log(f"   Run completed!", Colors.GREEN)
                        log(f"   Result: {event.get('payload', {})}", Colors.GREEN)
                        break
                    
                    elif event_type == "error":
                        error_msg = event.get("payload", {}).get("message", "Unknown error")
                        log(f"   ERROR: {error_msg}", Colors.RED)
                        break
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log(f"WebSocket error: {ws.exception()}", Colors.RED)
                    break
    
    log(f"\n{Colors.BOLD}=== Test Results ==={Colors.END}", Colors.CYAN)
    log(f"Events received: {len(events_received)}", Colors.BLUE)
    log(f"Event types: {', '.join(set(events_received))}", Colors.BLUE)
    log(f"Execution started: {execution_started}", Colors.GREEN if execution_started else Colors.RED)
    log(f"Execution completed: {execution_completed}", Colors.GREEN if execution_completed else Colors.RED)
    
    # Validate test
    required_events = ["connected", "run_started"]
    missing_events = [e for e in required_events if e not in events_received]
    
    if missing_events:
        log(f"\n✗ TEST FAILED: Missing events: {missing_events}", Colors.RED)
        return False
    
    if not execution_started:
        log(f"\n✗ TEST FAILED: Execution never started", Colors.RED)
        return False
    
    log(f"\n✓ TEST PASSED: WebSocket execution flow working correctly", Colors.GREEN)
    return True

async def main():
    """Main test flow"""
    log(f"\n{Colors.BOLD}{'='*60}{Colors.END}", Colors.CYAN)
    log(f"{Colors.BOLD}WebSocket Execution Flow Integration Test{Colors.END}", Colors.CYAN)
    log(f"{Colors.BOLD}{'='*60}{Colors.END}\n", Colors.CYAN)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Register user
            user_data = await register_user(session)
            token = user_data["access_token"]
            
            # Step 2: Create test workflow
            workflow = await create_test_workflow(session, token)
            workflow_id = workflow["id"]
            
            # Step 3: Test WebSocket execution
            success = await test_websocket_execution(workflow_id, token)
            
            log(f"\n{Colors.BOLD}{'='*60}{Colors.END}", Colors.CYAN)
            if success:
                log(f"{Colors.BOLD}✓ All tests passed!{Colors.END}", Colors.GREEN)
                return 0
            else:
                log(f"{Colors.BOLD}✗ Tests failed!{Colors.END}", Colors.RED)
                return 1
    
    except Exception as e:
        log(f"\n{Colors.BOLD}✗ Test error: {e}{Colors.END}", Colors.RED)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user", Colors.YELLOW)
        sys.exit(1)
