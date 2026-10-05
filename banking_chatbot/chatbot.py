from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

_session_counts = {}

def pre_response_pii_filter(response: str) -> str:
    response = re.sub(r"\b\d{13,19}\b", "[REDACTED-CARD]", response)
    response = re.sub(r"\b\d{8,12}\b", "[REDACTED-ACCT]", response)
    return response

def rate_limit_check(session_id: str) -> None:
    _session_counts[session_id] = _session_counts.get(session_id, 0) + 1

    if _session_counts[session_id] > 20:
        raise RuntimeError(
            "Rate limit exceeded: max 20 financial queries per session"
        )

def write_audit_log_entry(event: dict) -> None:
    Path("audit_log").mkdir(exist_ok=True)

    payload = json.dumps(event)

    payload = re.sub(r"\b\d{13,19}\b", "[REDACTED-CARD]", payload)
    payload = re.sub(r"\b\d{8,12}\b", "[REDACTED-ACCT]", payload)

    with open(
        "audit_log/chatbot_tool_calls.jsonl",
        "a",
        encoding="utf-8"
    ) as f:
        f.write(payload + "\n")

def run_with_guardrails(
    user_message: str,
    session_id: str
) -> str:

    rate_limit_check(session_id)

    response = f"Response to: {user_message}"

    response = pre_response_pii_filter(response)

    write_audit_log_entry({
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "event": "chatbot_response"
    })

    return response
