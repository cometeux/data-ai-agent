"""JSON extraction for model responses; independent of UI and provider SDKs."""
from __future__ import annotations

import json
from typing import Any


def parse_analysis_json(text: str | None) -> dict[str, Any] | None:
    """Read the first JSON object, allowing prose/fences and braces in strings."""
    if not isinstance(text, str):
        return None
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None
