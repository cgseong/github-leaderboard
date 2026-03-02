from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScoreSection:
    name: str
    score: float
    max_score: float
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    repo: str
    generated_at: str
    total_score: float
    max_score: float
    grade: str
    pass_fail: str
    sections: list[ScoreSection]
    checklist: dict[str, list[str]]
    raw_metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

