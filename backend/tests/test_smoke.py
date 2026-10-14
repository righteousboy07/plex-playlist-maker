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
    assert "/api/v1/automation" in paths
    assert "/api/v1/automation/{job_name}/install" in paths
    assert "/api/v1/automation/{job_name}/uninstall" in paths
    assert "/api/v1/automation/{job_name}/run-now" in paths
    assert "/api/v1/artwork/{rating_key}" in paths
    assert "/api/v1/playlist" in paths
    assert "/api/v1/movies/preview" in paths
    assert "/api/v1/movies/playlist" in paths
    assert "/api/v1/wishlist/kids-scary" in paths
    assert "/api/v1/schedules" in paths
    assert "/api/v1/schedules/{schedule_id}" in paths
    assert "/api/v1/schedules/{schedule_id}/preview" in paths
    assert "/api/v1/schedules/{schedule_id}/build" in paths


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


def test_api_server_automation_cannot_uninstall_itself():
    try:
        api.automation_uninstall("api-server", True)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
    else:
        raise AssertionError("Expected self-uninstall to be blocked")


def test_automation_install_uses_launchd_manager(monkeypatch):
    monkeypatch.setattr(
        api,
        "launchd_jobs_payload",
        lambda: {
            "jobs": [
                {
                    "name": "stations-nightly",
                    "label": "com.ry.plexcurator.stationsnightly",
                    "description": "Nightly",
                }
            ]
        },
    )

    calls = []

    def fake_run(*args):
        calls.append(args)
        if args[0] == "status-json":
            return """{"name":"stations-nightly","loaded":true,"plist_exists":true}"""
        return ""

    monkeypatch.setattr(api, "run_launchd_manager", fake_run)
    response = api.automation_install("stations-nightly", True)

    assert response["ok"] is True
    assert response["job"]["loaded"] is True
    assert ("install", "stations-nightly") in calls


def test_launchd_wishlist_uses_packaged_example():
    import importlib.util
    from pathlib import Path

    manager_path = Path(__file__).resolve().parents[1] / "launchd-manager.py"
    spec = importlib.util.spec_from_file_location("plex_curator_launchd", manager_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    args = module.JOBS["kids-scary-wishlist"]["args"]
    assert "examples" in args[1]
    assert args[1].endswith("kids-scary-missing-wishlist.txt")


def test_artwork_rejects_non_numeric_rating_key():
    try:
        api.artwork("not-a-number", 240, 360)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Expected invalid artwork rating key to be rejected")


def test_serialize_item_exposes_artwork_metadata():
    item = SimpleNamespace(
        ratingKey="123",
        type="movie",
        title="Example",
        year=1999,
        contentRating="PG",
        viewCount=0,
        duration=7200000,
        summary="Example summary",
        thumb="/library/metadata/123/thumb/1",
    )

    payload = api.serialize_item(item, 1)

    assert payload["rating_key"] == "123"
    assert payload["thumb_available"] is True
    assert payload["artwork_url"] == "/api/v1/artwork/123"
    assert payload["duration_minutes"] == 120
    assert payload["summary"] == "Example summary"


def test_movie_filters_reject_conflicting_watch_state():
    request = api.MovieFilterRequest(watched=True, unwatched=True)
    try:
        api.movie_request_options(request)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Expected conflicting watch filters to be rejected")


def test_movie_filters_reject_invalid_year_range():
    request = api.MovieFilterRequest(year_min=2000, year_max=1990)
    try:
        api.movie_request_options(request)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Expected invalid year range to be rejected")


def test_resolve_title_with_aliases(monkeypatch):
    calls = []

    def fake_resolve(section, title, year=None):
        calls.append((title, year))
        if title == "Ghostbusters Remastered":
            return SimpleNamespace(title=title, year=1984)
        return None

    monkeypatch.setattr(core, "resolve_title", fake_resolve)
    monkeypatch.setattr(
        api,
        "load_title_aliases",
        lambda: {"Ghostbusters": ["Ghostbusters Remastered"]},
    )

    item = api.resolve_title_with_aliases(object(), "Ghostbusters", 1984)

    assert item.title == "Ghostbusters Remastered"
    assert calls == [
        ("Ghostbusters", 1984),
        ("Ghostbusters Remastered", 1984),
    ]


def test_schedule_summary_totals_blocks():
    cfg = {
        "description": "Example schedule",
        "playlist": "Example Playlist",
        "blocks": [
            {"name": "Cartoons", "type": "cartoons", "preset": "80s-cartoons", "minutes": 60},
            {"name": "Movie", "type": "movie", "preset": "kids-scary", "minutes": 120},
        ],
    }

    payload = api.schedule_summary("example", cfg)

    assert payload["id"] == "example"
    assert payload["playlist"] == "Example Playlist"
    assert payload["total_minutes"] == 180
    assert len(payload["blocks"]) == 2
    assert payload["blocks"][0]["name"] == "Cartoons"


def test_schedule_options_reject_invalid_seasonal():
    request = api.ScheduleOptionsRequest(seasonal="spring")
    try:
        api.schedule_options(request)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("Expected invalid seasonal setting to be rejected")


def test_schedule_options_match_cli_defaults():
    request = api.ScheduleOptionsRequest()
    options = api.schedule_options(request)

    assert options["avoid_recent"] == 150
    assert options["min_show_gap"] == 2
    assert options["seasonal"] == "auto"
    assert options["special_every"] == 8
    assert options["unwatched"] is False
    assert options["sync_watch_progress"] is True
