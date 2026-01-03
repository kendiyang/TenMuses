from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from app.services.context_service import ContextService

router = APIRouter(prefix="/context", tags=["context"])
_context_service = ContextService()


@router.post("/serialize")
async def serialize_context(payload: Dict[str, Any]):
    nodes = payload.get("nodes", []) if payload else []
    edges = payload.get("edges", []) if payload else []
    items = _context_service.create_context_items({"nodes": nodes, "edges": edges})
    analysis = _context_service.analyze(items)
    return {"nodes": nodes, "edges": edges, "items": items, "analysis": analysis}


@router.post("/suggestions")
async def context_suggestions(payload: Dict[str, Any]):
    nodes: List[Dict[str, Any]] = payload.get("nodes", []) if payload else []
    edges: List[Dict[str, Any]] = payload.get("edges", []) if payload else []
    suggestions: List[Dict[str, Any]] = []

    if nodes:
        suggestions.append({
            "type": "coverage",
            "content": f"Workflow has {len(nodes)} nodes and {len(edges)} edges",
        })
    if any(n.get("type") == "llm" for n in nodes):
        suggestions.append({"type": "llm", "content": "Ensure prompts are concise"})
    if any(n.get("type") == "search" for n in nodes):
        suggestions.append({"type": "retrieval", "content": "Tune topK for search nodes"})

    return suggestions

