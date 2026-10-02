"""Registra el consumo de tokens y llamadas para auditoría de costos."""

from typing import Dict, Any


class CostTracker:
    def __init__(self):
        self.total_calls = 0
        self.total_tokens = 0

    def record_usage(self, tokens: int = 150):
        self.total_calls += 1
        self.total_tokens += tokens

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "estimated_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.total_tokens * 0.000002, 5)
        }


cost_tracker = CostTracker()
