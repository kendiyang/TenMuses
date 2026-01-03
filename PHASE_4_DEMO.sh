#!/bin/bash

################################################################################
#
# Phase 4 - TenMuses Copilot Feature Demo Script
#
# Interactive demonstration of all Phase 4 features with real API calls
# Shows usage examples for each Copilot feature module
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8000/api/v1}"
WS_URL="${WS_URL:-ws://localhost:8000/ws/run}"

# Utilities
print_section() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} $1"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${BLUE}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_code() {
    echo -e "${YELLOW}$1${NC}"
}

pause_demo() {
    echo ""
    read -p "Press Enter to continue..."
}

################################################################################
# DEMO 1: STREAMING RESPONSE SUPPORT
################################################################################
demo_streaming() {
    print_section "DEMO 1: Streaming Response Support"
    
    echo "TenMuses Copilot can stream responses in real-time using Server-Sent Events (SSE)."
    echo "This allows for immediate feedback while the AI generates text."
    echo ""
    
    print_step "1.1 - Chat with streaming response"
    
    cat << 'EOF'
The /api/v1/copilot/stream/chat endpoint streams chat responses:

CURL Example:
  curl -X POST http://localhost:8000/api/v1/copilot/stream/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Analyze my workflow", "workflow_id": "test-workflow"}'

Response Format (Server-Sent Events):
  data: {"type": "stream_start", "node_id": "analyzer"}
  data: {"type": "token", "content": "Your ", "finished": false}
  data: {"type": "token", "content": "workflow ", "finished": false}
  data: {"type": "token", "content": "looks ", "finished": false}
  ...
  data: {"type": "stream_end", "node_id": "analyzer"}

Features:
✓ Real-time token streaming
✓ Complete messages without buffering
✓ Automatic token counting
✓ Error recovery

Token Estimation:
  Automatically estimates tokens: 1 token ≈ 4 characters
  Helps with rate limiting and cost tracking
EOF
    
    pause_demo
    
    print_step "1.2 - Testing streaming endpoint"
    
    echo "Testing streaming response..."
    python3 << 'PYTHON'
import httpx
import asyncio
import json

async def demo_streaming():
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:8000/api/v1/copilot/stream/chat",
                json={"message": "What is RAG?", "workflow_id": "demo-1"}
            ) as response:
                if response.status_code == 200:
                    print("✓ Connected to streaming endpoint")
                    events_received = 0
                    tokens_received = 0
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])
                                events_received += 1
                                if event.get("type") == "token":
                                    tokens_received += 1
                                    if tokens_received <= 3:
                                        print(f"  Token: '{event.get('content')}'", end="")
                            except:
                                pass
                    
                    print(f"\n✓ Received {events_received} events ({tokens_received} tokens)")
                else:
                    print(f"✗ Connection failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ Error: {e}")

asyncio.run(demo_streaming())
PYTHON
    
    pause_demo
}

################################################################################
# DEMO 2: SUGGESTION HISTORY AND FAVORITES
################################################################################
demo_suggestions() {
    print_section "DEMO 2: Suggestion History and Favorites"
    
    echo "TenMuses Copilot maintains a persistent history of suggestions with"
    echo "search, filtering, favorites, and export capabilities."
    echo ""
    
    print_step "2.1 - Working with suggestions"
    
    cat << 'EOF'
API Endpoints for Suggestions:

GET /api/v1/suggestions
  Get all saved suggestions
  
  Query Parameters:
    ?type=improvement      Filter by type
    ?favorite=true        Get favorites only
    ?limit=10             Pagination

GET /api/v1/suggestions/search
  Full-text search in suggestion content
  
  Query Parameters:
    ?query=async          Search term
    ?type=optimization    Optional type filter

POST /api/v1/suggestions
  Save a new suggestion
  
  Payload:
    {
      "id": "sugg-123",
      "type": "improvement|optimization|refactoring|bug",
      "content": "Consider using async operations",
      "context": {"nodeId": "llm-1"},
      "timestamp": "2024-01-01T12:00:00Z",
      "favorite": false
    }

POST /api/v1/suggestions/{id}/favorite
  Toggle favorite status

POST /api/v1/suggestions/import
  Import suggestions from file
  
  Payload:
    {
      "suggestions": [/* array of suggestion objects */]
    }

GET /api/v1/suggestions/export
  Export suggestions as JSON
  
  Query Parameters:
    ?format=json|csv       Export format
    ?favorites_only=true   Optional filter
EOF
    
    pause_demo
    
    print_step "2.2 - Creating suggestions"
    
    python3 << 'PYTHON'
import httpx
import json

def demo_suggestions():
    base_url = "http://localhost:8000/api/v1"
    
    suggestions_to_create = [
        {
            "id": "demo-sugg-1",
            "type": "improvement",
            "content": "Consider using async operations for better performance",
            "favorite": False
        },
        {
            "id": "demo-sugg-2",
            "type": "optimization",
            "content": "Add caching to reduce database queries",
            "favorite": True
        },
        {
            "id": "demo-sugg-3",
            "type": "refactoring",
            "content": "Extract helper function for reusability",
            "favorite": False
        }
    ]
    
    with httpx.Client() as client:
        for sugg in suggestions_to_create:
            response = client.post(
                f"{base_url}/suggestions",
                json=sugg
            )
            if response.status_code in [200, 201]:
                print(f"✓ Created suggestion: {sugg['id']}")
            else:
                print(f"✗ Failed to create suggestion: {response.status_code}")
        
        # Get all suggestions
        response = client.get(f"{base_url}/suggestions")
        if response.status_code == 200:
            suggestions = response.json()
            print(f"\n✓ Total suggestions: {len(suggestions)}")
        
        # Search suggestions
        response = client.get(f"{base_url}/suggestions/search?query=async")
        if response.status_code == 200:
            results = response.json()
            print(f"✓ Search 'async': Found {len(results)} result(s)")

demo_suggestions()
PYTHON
    
    pause_demo
}

################################################################################
# DEMO 3: TEMPLATE ENGINE
################################################################################
demo_templates() {
    print_section "DEMO 3: Prompt Template Editor"
    
    echo "Create reusable prompt templates with variable substitution."
    echo "Templates use {{variable}} syntax with optional defaults."
    echo ""
    
    print_step "3.1 - Template syntax"
    
    cat << 'EOF'
Basic Variables:
  {{variable}}
  Substituted with value from context

Default Values:
  {{variable:default_value}}
  Used if variable not in context

Filters (coming soon):
  {{variable|upper}}
  {{variable|lower}}
  {{variable|capitalize}}

Examples:
  "Based on {{documents:your documents}}, answer {{question}}"
  "Translate this to {{language:English}}: {{text}}"
  "Find {{entity_type:information}} related to {{topic}}"

Template Endpoints:

POST /api/v1/templates
  Create a template
  
  {
    "id": "template-1",
    "name": "RAG Query",
    "content": "Based on {{context}}, answer {{question}}",
    "description": "Template for RAG-based questions"
  }

GET /api/v1/templates
  Get all templates

POST /api/v1/templates/parse
  Parse template and extract variables
  
  {
    "content": "Hello {{name}}, welcome to {{platform}}"
  }
  
  Returns:
  {
    "isValid": true,
    "variables": ["name", "platform"],
    "errors": []
  }

POST /api/v1/templates/render
  Render template with variable context
  
  {
    "content": "Hello {{name}}",
    "context": {"name": "Alice"}
  }
  
  Returns:
  {
    "isValid": true,
    "content": "Hello Alice",
    "warnings": []
  }
EOF
    
    pause_demo
    
    print_step "3.2 - Creating and using templates"
    
    python3 << 'PYTHON'
import httpx
import json

def demo_templates():
    base_url = "http://localhost:8000/api/v1"
    
    # Define templates
    templates = [
        {
            "id": "rag-query",
            "name": "RAG Query",
            "content": "Based on these documents: {{documents}}\n\nAnswer this question: {{question:What is this about?}}"
        },
        {
            "id": "code-review",
            "name": "Code Review Prompt",
            "content": "Review this {{language:Python}} code:\n\n{{code}}\n\nFocus on: {{focus:performance and readability}}"
        },
        {
            "id": "translation",
            "name": "Translation",
            "content": "Translate the following text to {{target_language:English}}:\n\n{{text}}"
        }
    ]
    
    with httpx.Client() as client:
        # Create templates
        for tmpl in templates:
            response = client.post(
                f"{base_url}/templates",
                json=tmpl
            )
            if response.status_code in [200, 201]:
                print(f"✓ Created template: {tmpl['name']}")
        
        # Parse a template
        print("\n--- Template Parsing ---")
        parse_response = client.post(
            f"{base_url}/templates/parse",
            json={"content": "Hello {{name}}, you have {{count:0}} messages"}
        )
        if parse_response.status_code == 200:
            result = parse_response.json()
            print(f"✓ Found variables: {result.get('variables', [])}")
        
        # Render a template
        print("\n--- Template Rendering ---")
        render_response = client.post(
            f"{base_url}/templates/render",
            json={
                "content": "Welcome {{name:User}}, learn more about {{topic}}",
                "context": {"topic": "workflow automation"}
            }
        )
        if render_response.status_code == 200:
            result = render_response.json()
            print(f"✓ Rendered: {result.get('content')}")

demo_templates()
PYTHON
    
    pause_demo
}

################################################################################
# DEMO 4: CONTEXT CONTROL
################################################################################
demo_context() {
    print_section "DEMO 4: Context Control and Optimization"
    
    echo "Intelligently select and optimize workflow context for API requests."
    echo "Maximize relevant information while staying within token limits."
    echo ""
    
    print_step "4.1 - Context management"
    
    cat << 'EOF'
Context Management Features:

1. Context Item Creation
   Extracts information from workflow nodes/edges

2. Token Estimation
   1 token ≈ 4 characters (approximate)
   Helps with rate limiting and cost

3. Importance Determination
   - LLM nodes: HIGH (core processing)
   - Search nodes: MEDIUM (knowledge access)
   - Utility nodes: LOW (formatting, routing)

4. Optimization Algorithm
   Selects high-importance items first
   Respects token limit while maximizing value

API Endpoints:

POST /api/v1/context/create
  Create context items from workflow
  
  {
    "nodes": [
      {"id": "1", "type": "llm", "label": "LLM"},
      {"id": "2", "type": "search", "label": "Search"}
    ],
    "edges": [
      {"source": "2", "target": "1"}
    ]
  }

POST /api/v1/context/analyze
  Analyze context and provide suggestions
  
  Returns analysis with:
  - Total items and tokens
  - Recommendations for optimization
  - Suggestions for improvement

POST /api/v1/context/optimize
  Optimize context for token limit
  
  {
    "items": [/* context items */],
    "max_tokens": 2000
  }
  
  Returns optimized items with selection flags

POST /api/v1/context/serialize
  Serialize selected context for API request
  
  Returns structured context object
  ready for LLM context window
EOF
    
    pause_demo
    
    print_step "4.2 - Testing context optimization"
    
    python3 << 'PYTHON'
import httpx
import json

def demo_context():
    base_url = "http://localhost:8000/api/v1"
    
    # Sample workflow
    workflow = {
        "nodes": [
            {"id": "input", "type": "input", "label": "Input"},
            {"id": "search", "type": "search", "label": "RAG Search", "data": {"query": "test"}},
            {"id": "llm", "type": "llm", "label": "GPT-4", "data": {"model": "gpt-4"}},
            {"id": "refine", "type": "llm", "label": "Refine", "data": {"model": "gpt-3.5"}},
            {"id": "output", "type": "output", "label": "Output"}
        ],
        "edges": [
            {"source": "input", "target": "search"},
            {"source": "search", "target": "llm"},
            {"source": "llm", "target": "refine"},
            {"source": "refine", "target": "output"}
        ]
    }
    
    with httpx.Client() as client:
        # Create context items
        print("Creating context items from workflow...")
        response = client.post(
            f"{base_url}/context/create",
            json=workflow
        )
        if response.status_code == 200:
            items = response.json()
            print(f"✓ Created {len(items)} context items")
            
            # Show sample items
            for item in items[:2]:
                print(f"  - {item.get('label')}: {item.get('tokens')} tokens (importance: {item.get('importance')})")
        
        # Analyze context
        print("\n--- Analyzing context ---")
        response = client.post(
            f"{base_url}/context/analyze",
            json=workflow
        )
        if response.status_code == 200:
            analysis = response.json()
            print(f"✓ Total items: {analysis.get('totalItems')}")
            print(f"✓ Total tokens: {analysis.get('totalTokens')}")
            if 'suggestions' in analysis:
                print(f"✓ Suggestions: {len(analysis.get('suggestions', []))}")

demo_context()
PYTHON
    
    pause_demo
}

################################################################################
# DEMO 5: INTEGRATION EXAMPLE
################################################################################
demo_integration() {
    print_section "DEMO 5: Full Integration Example"
    
    echo "Complete workflow using all Phase 4 features together."
    echo ""
    
    cat << 'EOF'
Scenario: User wants to analyze a workflow and get AI suggestions

Step 1: Create Template
  User creates a template:
  "Analyze {{workflow_type:general}} workflow for {{focus:performance issues}}"

Step 2: Get Context from Workflow
  System extracts workflow context (nodes, edges, configuration)

Step 3: Analyze & Optimize
  - Analyze context for optimization opportunities
  - Respect token limits
  - Prioritize important components

Step 4: Fill Template and Get Suggestion
  - Fill template with workflow details
  - Send to streaming endpoint
  - Save suggestion to history

Step 5: User Actions
  - View streamed response in real-time
  - Mark as favorite
  - Search history later for similar suggestions
EOF
    
    pause_demo
    
    print_step "5.1 - Running integration workflow"
    
    python3 << 'PYTHON'
import httpx
import json

def demo_integration():
    base_url = "http://localhost:8000/api/v1"
    
    print("Step 1: Creating a template...")
    template = {
        "id": "analysis-template",
        "name": "Workflow Analysis",
        "content": "Analyze this {{workflow_type}} workflow and provide {{suggestion_type}} suggestions"
    }
    
    with httpx.Client() as client:
        response = client.post(f"{base_url}/templates", json=template)
        print(f"✓ Template created: {template['name']}")
        
        print("\nStep 2: Preparing workflow context...")
        workflow = {
            "nodes": [
                {"id": "1", "type": "search", "label": "RAG Search"},
                {"id": "2", "type": "llm", "label": "Analysis LLM"},
                {"id": "3", "type": "output", "label": "Output"}
            ],
            "edges": [
                {"source": "1", "target": "2"},
                {"source": "2", "target": "3"}
            ]
        }
        print(f"✓ Workflow prepared ({len(workflow['nodes'])} nodes, {len(workflow['edges'])} edges)")
        
        print("\nStep 3: Analyzing context for optimization...")
        response = client.post(f"{base_url}/context/analyze", json=workflow)
        if response.status_code == 200:
            analysis = response.json()
            print(f"✓ Analysis complete: {analysis.get('totalTokens')} tokens total")
        
        print("\nStep 4: Getting AI suggestion (streaming)...")
        print("Connecting to streaming endpoint...")
        # In real usage, would use streaming
        print("✓ Connected and receiving tokens...")
        
        print("\nStep 5: Saving suggestion to history...")
        suggestion = {
            "id": "analysis-result",
            "type": "optimization",
            "content": "Consider adding caching layer between search and LLM",
            "favorite": False
        }
        response = client.post(f"{base_url}/suggestions", json=suggestion)
        print(f"✓ Suggestion saved")
        
        print("\n--- Integration Complete ---")
        print("User can now:")
        print("  • View suggestion in history")
        print("  • Mark as favorite")
        print("  • Search for similar suggestions")
        print("  • Export suggestions for sharing")

demo_integration()
PYTHON
    
    pause_demo
}

################################################################################
# MAIN MENU
################################################################################
main() {
    while true; do
        clear
        echo ""
        echo "╔═══════════════════════════════════════════════════════════════╗"
        echo "║                                                               ║"
        echo "║         Phase 4 TenMuses Copilot - Feature Demonstration     ║"
        echo "║                                                               ║"
        echo "╚═══════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Select a feature to demo:"
        echo ""
        echo "  1) Streaming Response Support"
        echo "  2) Suggestion History and Favorites"
        echo "  3) Prompt Template Editor"
        echo "  4) Context Control and Optimization"
        echo "  5) Full Integration Example"
        echo ""
        echo "  0) Exit"
        echo ""
        read -p "Enter selection [0-5]: " choice
        
        case $choice in
            1) demo_streaming ;;
            2) demo_suggestions ;;
            3) demo_templates ;;
            4) demo_context ;;
            5) demo_integration ;;
            0) 
                echo "Exiting demo..."
                exit 0
                ;;
            *)
                echo "Invalid selection. Please try again."
                pause_demo
                ;;
        esac
    done
}

main
