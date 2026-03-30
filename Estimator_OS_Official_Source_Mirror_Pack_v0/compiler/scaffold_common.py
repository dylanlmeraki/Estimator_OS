"""Shared helpers for first-pass scaffold modules."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


PACK_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = PACK_ROOT / "schemas"
SEEDPACKS_DIR = PACK_ROOT / "seedpacks"


def canonicalize(value: Any) -> Any:
    """Return deterministically sorted JSON-compatible data."""
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key in sorted(value.keys()):
            item = canonicalize(value[key])
            normalized[key] = item
        return normalized
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def stable_json_dumps(value: Any) -> str:
    return json.dumps(canonicalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(value: Any) -> str:
    payload = value if isinstance(value, str) else stable_json_dumps(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
