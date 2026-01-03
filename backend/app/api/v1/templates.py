from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])

_template_store: Dict[str, Dict[str, Any]] = {}
_template_service = TemplateService()


@router.get("")
async def list_templates():
    return list(_template_store.values())


@router.post("", status_code=201)
async def save_template(payload: Dict[str, Any]):
    if not payload or "id" not in payload:
        raise HTTPException(status_code=400, detail="id is required")
    _template_store[payload["id"]] = payload
    return payload


@router.post("/apply")
async def apply_template(payload: Dict[str, Any]):
    if payload is None:
        raise HTTPException(status_code=400, detail="payload required")
    variables = payload.get("variables", {}) if isinstance(payload, dict) else {}

    template_id = payload.get("template_id") if isinstance(payload, dict) else None
    if template_id:
        template = _template_store.get(template_id)
        template_content = template.get("content", "") if template else ""
    else:
        template_content = payload.get("template") or payload.get("content") or ""

    result = _template_service.render(template_content, variables)
    return {"content": result.get("content", ""), "isValid": result.get("isValid", True)}

