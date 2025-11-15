from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import ServiceConfig
from ..schemas import ForecastRun


class ForecastStore:
    def __init__(self, data_dir: Path, config: ServiceConfig):
        self.file_path = data_dir / "forecast_history.json"
        self.config = config
        self._runs: list[ForecastRun] = []
        self._load()

    def _load(self) -> None:
        if not self.file_path.exists():
            self._runs = []
            return

        try:
            payload: list[dict[str, Any]] = json.loads(self.file_path.read_text())
        except json.JSONDecodeError:
            self._runs = []
            return

        self._runs = [ForecastRun(**item) for item in payload][-self.config.max_runs :]

    def _persist(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        serializable = [json.loads(run.model_dump_json()) for run in self._runs]
        self.file_path.write_text(json.dumps(serializable, indent=2))

    def add_run(self, run: ForecastRun) -> None:
        self._runs.append(run)
        self._runs = self._runs[-self.config.max_runs :]
        self._persist()

    def latest(self) -> ForecastRun | None:
        return self._runs[-1] if self._runs else None

    def all_runs(self) -> list[ForecastRun]:
        return list(self._runs)
