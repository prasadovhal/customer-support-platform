from __future__ import annotations

import pytest

from app.experiments.registry import ExperimentRegistry, ExperimentRun


def _run(run_id: str, timestamp: str, metric_val: float, **kwargs) -> ExperimentRun:
    return ExperimentRun(
        run_id=run_id,
        name=f"run-{run_id}",
        hypothesis="test hypothesis",
        strategy="bm25",
        metrics={"recall_at_5": metric_val},
        timestamp=timestamp,
        **kwargs,
    )


def test_save_and_load_roundtrip(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    run = _run("run-001", "2026-01-01T00:00:00Z", 0.85, tags=["v1"], notes="initial")
    registry.save(run)
    loaded = registry.load("run-001")
    assert loaded.run_id == run.run_id
    assert loaded.name == run.name
    assert loaded.hypothesis == run.hypothesis
    assert loaded.strategy == run.strategy
    assert loaded.metrics == run.metrics
    assert loaded.timestamp == run.timestamp
    assert loaded.tags == run.tags
    assert loaded.notes == run.notes


def test_load_nonexistent_raises(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    with pytest.raises(FileNotFoundError):
        registry.load("does-not-exist")


def test_load_all_sorted_by_timestamp(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    r3 = _run("r3", "2026-03-01T00:00:00Z", 0.7)
    r1 = _run("r1", "2026-01-01T00:00:00Z", 0.9)
    r2 = _run("r2", "2026-02-01T00:00:00Z", 0.8)
    for r in (r3, r1, r2):
        registry.save(r)

    all_runs = registry.load_all()
    assert [r.run_id for r in all_runs] == ["r1", "r2", "r3"]


def test_load_all_empty_dir(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    assert registry.load_all() == []


def test_compare_sorted_descending(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    registry.save(_run("r1", "2026-01-01T00:00:00Z", 0.6))
    registry.save(_run("r2", "2026-02-01T00:00:00Z", 0.9))
    registry.save(_run("r3", "2026-03-01T00:00:00Z", 0.75))

    result = registry.compare("recall_at_5")
    assert result[0] == ("r2", pytest.approx(0.9))
    assert result[1] == ("r3", pytest.approx(0.75))
    assert result[2] == ("r1", pytest.approx(0.6))


def test_best_returns_highest_metric(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    registry.save(_run("r1", "2026-01-01T00:00:00Z", 0.6))
    registry.save(_run("r2", "2026-02-01T00:00:00Z", 0.9))
    registry.save(_run("r3", "2026-03-01T00:00:00Z", 0.75))

    best = registry.best("recall_at_5")
    assert best is not None
    assert best.run_id == "r2"


def test_best_lower_is_better(tmp_path):
    registry = ExperimentRegistry(tmp_path)
    registry.save(_run("r1", "2026-01-01T00:00:00Z", 0.6))
    registry.save(_run("r2", "2026-02-01T00:00:00Z", 0.9))
    registry.save(_run("r3", "2026-03-01T00:00:00Z", 0.1))

    best = registry.best("recall_at_5", higher_is_better=False)
    assert best is not None
    assert best.run_id == "r3"


def test_experiment_run_to_dict_from_dict_roundtrip():
    run = ExperimentRun(
        run_id="r42",
        name="dense-retrieval",
        hypothesis="dense beats sparse",
        strategy="dense",
        metrics={"recall_at_5": 0.88, "mrr": 0.77},
        timestamp="2026-06-15T12:00:00Z",
        tags=["dense", "production"],
        notes="first dense run",
    )
    d = run.to_dict()
    restored = ExperimentRun.from_dict(d)
    assert restored.run_id == run.run_id
    assert restored.metrics == run.metrics
    assert restored.tags == run.tags
    assert restored.notes == run.notes
