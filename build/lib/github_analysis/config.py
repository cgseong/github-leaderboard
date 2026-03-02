from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_RUBRIC: dict[str, Any] = {
    "pass_score": 70,
    "sections": {
        "code_quality": 40,
        "activity": 25,
        "documentation": 20,
        "collaboration": 15,
    },
}


@dataclass
class Rubric:
    pass_score: float = 70.0
    sections: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_RUBRIC["sections"]))

    @property
    def max_score(self) -> float:
        return float(sum(self.sections.values()))


def load_rubric(path: str | None) -> Rubric:
    if not path:
        return Rubric()

    rubric_path = Path(path)
    with rubric_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    merged = {
        "pass_score": raw.get("pass_score", DEFAULT_RUBRIC["pass_score"]),
        "sections": dict(DEFAULT_RUBRIC["sections"]),
    }
    merged["sections"].update(raw.get("sections", {}))

    return Rubric(
        pass_score=float(merged["pass_score"]),
        sections={k: float(v) for k, v in merged["sections"].items()},
    )

