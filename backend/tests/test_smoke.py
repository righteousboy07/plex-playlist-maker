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
    assert "/api/v1/stations/{station_id}/refresh" in paths
