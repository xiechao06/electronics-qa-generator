"""Tests for simulation/cache.py — FactCache put/get."""

from __future__ import annotations

from electronics_qa_generator.simulation.cache import FactCache


class TestFactCache:
    def test_put_and_get(self, tmp_path):
        cache = FactCache(cache_dir=tmp_path / "cache")
        cache.put("rc_lowpass", 42, {"cutoff_hz": 1590.0, "behavior": "low-pass"})

        result = cache.get("rc_lowpass", 42)
        assert result == {"cutoff_hz": 1590.0, "behavior": "low-pass"}

    def test_miss_returns_none(self, tmp_path):
        cache = FactCache(cache_dir=tmp_path / "cache")
        assert cache.get("nonexistent", 0) is None

    def test_overwrite_updates_value(self, tmp_path):
        cache = FactCache(cache_dir=tmp_path / "cache")
        cache.put("rc_lowpass", 42, {"cutoff_hz": 1000.0})
        cache.put("rc_lowpass", 42, {"cutoff_hz": 2000.0})
        assert cache.get("rc_lowpass", 42) == {"cutoff_hz": 2000.0}

    def test_different_seeds_different_files(self, tmp_path):
        cache = FactCache(cache_dir=tmp_path / "cache")
        cache.put("rc_lowpass", 1, {"cutoff_hz": 100.0})
        cache.put("rc_lowpass", 2, {"cutoff_hz": 200.0})
        assert cache.get("rc_lowpass", 1) == {"cutoff_hz": 100.0}
        assert cache.get("rc_lowpass", 2) == {"cutoff_hz": 200.0}

    def test_auto_create_cache_dir(self, tmp_path):
        cache_dir = tmp_path / "nonexistent" / "subdir"
        assert not cache_dir.exists()
        cache = FactCache(cache_dir=cache_dir)
        cache.put("test", 0, {"value": 1})
        assert cache_dir.exists()

    def test_cache_file_is_valid_json(self, tmp_path):
        cache = FactCache(cache_dir=tmp_path / "cache")
        cache.put("voltage_divider", 42, {"Vout_dc": 6.28})
        import json

        filepath = cache._path("voltage_divider", 42)
        data = json.loads(filepath.read_text())
        assert data == {"Vout_dc": 6.28}

    def test_different_topologies_isolated(self, tmp_path):
        cache = FactCache(cache_dir=tmp_path / "cache")
        cache.put("voltage_divider", 0, {"Vout_dc": 5.0})
        cache.put("rc_lowpass", 0, {"cutoff_hz": 1590.0})
        assert cache.get("voltage_divider", 0) == {"Vout_dc": 5.0}
        assert cache.get("rc_lowpass", 0) == {"cutoff_hz": 1590.0}
