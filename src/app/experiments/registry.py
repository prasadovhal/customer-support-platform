from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExperimentRun:
    run_id: str
    name: str
    hypothesis: str
    strategy: str
    metrics: dict[str, Any]
    timestamp: str
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "strategy": self.strategy,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExperimentRun:
        return cls(
            run_id=d["run_id"],
            name=d["name"],
            hypothesis=d["hypothesis"],
            strategy=d["strategy"],
            metrics=d["metrics"],
            timestamp=d["timestamp"],
            tags=d.get("tags", []),
            notes=d.get("notes", ""),
        )


class ExperimentRegistry:
    def __init__(self, store_path: Path) -> None:
        self._store_path = store_path
        self._store_path.mkdir(parents=True, exist_ok=True)

    def _run_path(self, run_id: str) -> Path:
        return self._store_path / f"{run_id}.json"

    def save(self, run: ExperimentRun) -> None:
        self._run_path(run.run_id).write_text(
            json.dumps(run.to_dict(), indent=2), encoding="utf-8"
        )

    def load(self, run_id: str) -> ExperimentRun:
        path = self._run_path(run_id)
        if not path.exists():
            raise FileNotFoundError(f"No experiment run found with id: {run_id!r}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ExperimentRun.from_dict(data)

    def load_all(self) -> list[ExperimentRun]:
        runs = [
            ExperimentRun.from_dict(json.loads(p.read_text(encoding="utf-8")))
            for p in self._store_path.glob("*.json")
        ]
        return sorted(runs, key=lambda r: r.timestamp)

    def compare(
        self,
        metric: str,
        run_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        if run_ids is not None:
            runs = [self.load(rid) for rid in run_ids]
        else:
            runs = self.load_all()
        pairs = [
            (r.run_id, float(r.metrics[metric])) for r in runs if metric in r.metrics
        ]
        return sorted(pairs, key=lambda t: t[1], reverse=True)

    def best(self, metric: str, higher_is_better: bool = True) -> ExperimentRun | None:
        runs = self.load_all()
        candidates = [r for r in runs if metric in r.metrics]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda r: float(r.metrics[metric]) * (1 if higher_is_better else -1),
        )
