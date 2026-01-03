from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

# In-memory store for suggestion history used by tests
_suggestion_store: Dict[str, Dict[str, Any]] = {}


def _normalize_suggestion(payload: Dict[str, Any]) -> Dict[str, Any]:
    suggestion = {
        "id": payload.get("id"),
        "type": payload.get("type", "general"),
        "content": payload.get("content", ""),
        "timestamp": payload.get("timestamp"),
        "favorite": bool(payload.get("favorite", False)),
    }
    # Preserve any additional fields
    for key, value in payload.items():
        if key not in suggestion:
            suggestion[key] = value
    return suggestion


@router.post("", status_code=201)
async def save_suggestion(payload: Dict[str, Any]):
    if not payload or "id" not in payload:
        raise HTTPException(status_code=400, detail="id is required")
    suggestion = _normalize_suggestion(payload)
    _suggestion_store[suggestion["id"]] = suggestion
    return suggestion


@router.get("")
async def list_suggestions(type: str | None = Query(None)):  # type: ignore[valid-type]
    suggestions = list(_suggestion_store.values())
    if type:
        suggestions = [s for s in suggestions if s.get("type") == type]
    return suggestions


@router.get("/search")
async def search_suggestions(query: str = Query("")):
    term = query.lower()
    return [
        s for s in _suggestion_store.values()
        if term in str(s.get("content", "")).lower()
    ]


@router.post("/{suggestion_id}/favorite")
async def toggle_favorite(suggestion_id: str):
    if suggestion_id not in _suggestion_store:
        raise HTTPException(status_code=404, detail="suggestion not found")
    suggestion = _suggestion_store[suggestion_id]
    suggestion["favorite"] = not bool(suggestion.get("favorite", False))
    _suggestion_store[suggestion_id] = suggestion
    return suggestion


@router.get("/export")
async def export_suggestions(format: str = Query("json")):
    # Only JSON supported for tests
    return list(_suggestion_store.values())


@router.post("/import", status_code=201)
async def import_suggestions(payload: Dict[str, Any]):
    suggestions: List[Dict[str, Any]] = payload.get("suggestions", []) if payload else []
    if not isinstance(suggestions, list):
        raise HTTPException(status_code=400, detail="suggestions must be a list")
    for item in suggestions:
        if "id" not in item:
            raise HTTPException(status_code=400, detail="suggestion id missing")
        suggestion = _normalize_suggestion(item)
        _suggestion_store[suggestion["id"]] = suggestion
    return {"imported": len(suggestions)}

