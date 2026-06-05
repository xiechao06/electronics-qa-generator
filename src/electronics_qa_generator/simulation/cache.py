"""Fact cache: disk-backed (topology, seed) → fact_dict storage.

Avoids re-running Xyce for circuits already simulated. Uses JSON files
keyed by topology name and seed for human readability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FactCache:
    """Disk-backed cache of simulation facts keyed by (topology, seed)."""

    def __init__(self, cache_dir: Path | str | None = None):
        if cache_dir is None:
            cache_dir = Path(".cache/eqa")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, topology: str, seed: int) -> Path:
        return self._cache_dir / f"{topology}_{seed & 0xFFFFFFFF:08x}.json"

    def get(self, topology: str, seed: int) -> dict[str, Any] | None:
        """Return cached facts dict, or None if not found."""
        filepath = self._path(topology, seed)
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text())
        except json.JSONDecodeError, OSError:
            return None

    def put(self, topology: str, seed: int, facts: dict[str, Any]) -> None:
        """Store facts dict to the cache."""
        filepath = self._path(topology, seed)
        filepath.write_text(json.dumps(facts, indent=2, default=str))
