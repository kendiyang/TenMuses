from __future__ import annotations

from typing import Any, Dict, List


class ContextService:
    """Lightweight context analysis and selection helpers for tests."""

    def create_context_items(self, workflow_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []
        for node in workflow_data.get("nodes", []):
            label = node.get("label") or node.get("id", "")
            tokens = max(1, len(str(label)) // 4 or 1)
            items.append({
                "id": node.get("id"),
                "label": label,
                "type": node.get("type", "default"),
                "tokens": tokens,
                "importance": 1.0,
            })
        return items

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def analyze(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "totalItems": len(items),
            "totalTokens": sum(i.get("tokens", 0) for i in items),
            "suggestions": ["reduce less important items"] if items else [],
        }

    def optimize_for_token_limit(self, items: List[Dict[str, Any]], token_limit: int) -> List[Dict[str, Any]]:
        selected = []
        total = 0
        for item in items:
            if total + item.get("tokens", 0) <= token_limit:
                item["selected"] = True
                selected.append(item)
                total += item.get("tokens", 0)
            else:
                item["selected"] = False
                selected.append(item)
        return selected

