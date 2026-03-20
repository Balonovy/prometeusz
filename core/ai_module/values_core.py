from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    transformed_prompt: str
    reason: str


class ValuesCore:
    """Small placeholder policy layer for future ethics and safety controls."""

    def evaluate(self, prompt: str) -> dict[str, str | bool]:
        sanitized = prompt.strip()
        allowed = bool(sanitized)
        reason = 'accepted' if allowed else 'empty_prompt_rejected'
        return {
            'allowed': allowed,
            'transformed_prompt': sanitized or 'Please provide a prompt.',
            'reason': reason,
        }
