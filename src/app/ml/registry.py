from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib

REGISTRY_PATH = Path("models/registry.json")


class ModelRegistry:
    """File-based model registry storing metadata and paths for all trained models."""

    def __init__(self, registry_path: Path = REGISTRY_PATH) -> None:
        self.registry_path = registry_path
        self._data: dict[str, list[dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def _save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def register(
        self,
        task: str,
        model_type: str,
        model_path: str,
        metadata: dict[str, Any],
    ) -> None:
        entry = {
            "task": task,
            "model_type": model_type,
            "model_path": model_path,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            **metadata,
        }
        if task not in self._data:
            self._data[task] = []
        # Replace existing entry for same model_type
        self._data[task] = [
            e for e in self._data[task] if e["model_type"] != model_type
        ]
        self._data[task].append(entry)
        self._save()

    def get_best(self, task: str) -> Optional[str]:
        """Return model_path for the entry with highest macro_f1 on val split."""
        entries = self._data.get(task, [])
        if not entries:
            return None
        best = max(
            entries,
            key=lambda e: e.get("val_metrics", {}).get("macro_f1", 0.0),
        )
        return best["model_path"]  # type: ignore[no-any-return]

    def list_versions(self, task: str) -> list[dict[str, Any]]:
        return list(self._data.get(task, []))

    def all_tasks(self) -> list[str]:
        return list(self._data.keys())

    def load_model(self, task: str, model_type: Optional[str] = None) -> Any:
        entries = self._data.get(task, [])
        if not entries:
            raise FileNotFoundError(f"No registered models for task '{task}'")

        if model_type:
            matches = [e for e in entries if e["model_type"] == model_type]
            if not matches:
                raise FileNotFoundError(
                    f"No model of type '{model_type}' for task '{task}'"
                )
            entry = matches[-1]
        else:
            # Load best by val macro_f1
            entry = max(
                entries,
                key=lambda e: e.get("val_metrics", {}).get("macro_f1", 0.0),
            )

        path = Path(entry["model_path"])
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        return joblib.load(path)

    def summary(self) -> dict[str, Any]:
        result = {}
        for task, entries in self._data.items():
            result[task] = [
                {
                    "model_type": e["model_type"],
                    "val_macro_f1": e.get("val_metrics", {}).get("macro_f1"),
                    "registered_at": e.get("registered_at"),
                    "model_path": e.get("model_path"),
                }
                for e in entries
            ]
        return result
