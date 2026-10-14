from types import SimpleNamespace

import plex_curator as core
import plex_curator_api as api


def command_names():
    parser = core.build_parser()
    subparsers = next(
        action for action in parser._actions
        if getattr(action, "choices", None)
    )
    return set(subparsers.choices)


def test_expected_reliability_commands_exist():
    commands = command_names()
    expected = {
        "doctor",
        "station-list",
        "station-diff",
        "station-refresh",
        "backup",
        "backup-list",
        "logs",
    }
    assert expected <= commands


def test_default_station_profiles_validate():
    assert core.DEFAULT_STATIONS
    for station_id, raw in core.DEFAULT_STATIONS.items():
        cfg = core.normalize_station(station_id, raw)
        assert cfg["total"] > 0
        assert cfg["per_show"] > 0
        assert cfg["seasonal"] in {"auto", "none", "halloween", "christmas"}


def test_playlist_diff_counts_items():
    current = [SimpleNamespace(ratingKey="1", title="A"), SimpleNamespace(ratingKey="2", title="B")]
    proposed = [SimpleNamespace(ratingKey="2", title="B"), SimpleNamespace(ratingKey="3", title="C")]
    diff = core.calculate_playlist_diff(current, proposed)
    assert diff["keep_count"] == 1
    assert diff["add_count"] == 1
    assert diff["remove_count"] == 1


def test_api_routes_are_registered():
    paths = {route.path for route in api.app.routes}
    assert "/api/v1/ping" in paths
    assert "/api/v1/status" in paths
    assert "/api/v1/stations" in paths
    assert "/api/v1/stations/{station_id}" in paths
    assert "/api/v1/stations/{station_id}/refresh" in paths


def test_station_update_config_persists_normalized_profile(tmp_path, monkeypatch):
    stations_file = tmp_path / "stations.json"
    stations_file.write_text(
        """{
  "retro-kids": {
    "name": "Retro Kids",
    "enabled": true,
    "playlist": "Retro Kids Channel",
    "preset": "all-cartoons",
    "per_show": 6,
    "total": 60
  }
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(core, "STATIONS_FILE", stations_file)

    updated = api.update_station_config(
        "retro-kids",
        {
            "enabled": False,
            "total": 72,
            "seasonal": "halloween",
            "include_shows": ["DuckTales", "Darkwing Duck"],
        },
    )

    assert updated["enabled"] is False
    assert updated["total"] == 72
    assert updated["seasonal"] == "halloween"
    assert updated["include_shows"] == ["DuckTales", "Darkwing Duck"]

    saved = core.load_stations()["retro-kids"]
    assert saved["enabled"] is False
    assert saved["total"] == 72


def test_station_update_rejects_invalid_year_range(tmp_path, monkeypatch):
    stations_file = tmp_path / "stations.json"
    stations_file.write_text(
        """{
  "retro-kids": {
    "name": "Retro Kids",
    "enabled": true,
    "playlist": "Retro Kids Channel",
    "preset": "all-cartoons",
    "year_min": 1980,
    "year_max": 1999,
    "per_show": 6,
    "total": 60
  }
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(core, "STATIONS_FILE", stations_file)

    try:
        api.update_station_config("retro-kids", {"year_min": 2000, "year_max": 1990})
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Expected invalid year range to be rejected")
