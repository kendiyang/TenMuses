from __future__ import annotations

import re
from typing import Dict, List, Any


class TemplateService:
    """Minimal template parser and renderer for tests."""

    _var_pattern = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)(:[^|}]+)?(\|upper)?\s*}}")

    def parse(self, template: str) -> Dict[str, Any]:
        variables: List[str] = []
        errors: List[str] = []
        for match in self._var_pattern.finditer(template):
            var = match.group(1)
            variables.append(var)
        # 粗略校验非法变量名
        if "{{" in template and not variables:
            errors.append("invalid variable syntax")
        return {
            "isValid": len(errors) == 0,
            "variables": variables,
            "errors": errors,
        }

    def render(self, template: str, context: Dict[str, Any]) -> Dict[str, Any]:
        warnings: List[str] = []
        parse_result = self.parse(template)

        def _replace(match: re.Match[str]) -> str:
            name = match.group(1)
            default = match.group(2)[1:] if match.group(2) else ""
            filter_upper = bool(match.group(3))
            value = context.get(name, default)
            if value is None:
                value = ""
            if name not in context and not default:
                warnings.append(f"missing variable: {name}")
            value = str(value)
            if filter_upper:
                value = value.upper()
            return value

        is_valid = parse_result["isValid"] and len(warnings) == 0
        content = self._var_pattern.sub(_replace, template)
        result = {"isValid": is_valid, "content": content}
        if warnings:
            result["warnings"] = warnings
        return result

