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


def test_repair_trailing_json_junk_removes_legacy_literal_newline(tmp_path):
    stations_file = tmp_path / "stations.json"
    stations_file.write_text('{"retro-kids":{"enabled":true}}\\n', encoding="utf-8")

    repaired, detail = core.repair_trailing_json_junk(stations_file)

    assert repaired is True
    assert "removed legacy trailing data" in detail
    assert core.json_file_check(stations_file)[0] == "PASS"
    assert (tmp_path / "stations.json.pre-repair").exists()


def test_repair_trailing_json_junk_refuses_second_document(tmp_path):
    stations_file = tmp_path / "stations.json"
    stations_file.write_text('{"a":1}{"b":2}', encoding="utf-8")

    repaired, detail = core.repair_trailing_json_junk(stations_file)

    assert repaired is False
    assert "refusing to discard unexpected trailing data" in detail
    assert stations_file.read_text(encoding="utf-8") == '{"a":1}{"b":2}'


def test_api_wrapper_uses_sys_prefix_for_venv_detection():
    from pathlib import Path

    wrapper = (Path(__file__).resolve().parents[1] / "plex-curator-api").read_text(encoding="utf-8")
    assert "current_prefix = Path(sys.prefix).resolve()" in wrapper
    assert "current = Path(sys.executable).resolve()" not in wrapper


def test_channel_scoped_cursors_are_independent(tmp_path, monkeypatch):
    state_db = tmp_path / "state.sqlite3"
    config_dir = tmp_path / "config"
    monkeypatch.setattr(core, "STATE_DB", state_db)
    monkeypatch.setattr(core, "CONFIG_DIR", config_dir)

    core.init_db()
    show = SimpleNamespace(ratingKey="show-1", title="Example Show")

    core.set_cursor("station:80s", show, 4)
    core.set_cursor("station:90s", show, 9)

    assert core.get_cursor("station:80s", show)[0] == 4
    assert core.get_cursor("station:90s", show)[0] == 9


def test_cursor_updates_only_include_final_consumed_items():
    show = SimpleNamespace(ratingKey="show-1", title="Example Show")
    ep1 = SimpleNamespace(ratingKey="ep-1", title="One")
    ep2 = SimpleNamespace(ratingKey="ep-2", title="Two")
    special = SimpleNamespace(ratingKey="special-1", title="Special")

    cursor_steps = {
        "ep-1": (show, 3),
        "ep-2": (show, 7),
    }

    updates = core.cursor_updates_for_items(
        "station:retro-kids",
        [ep1, special],
        cursor_steps,
    )

    assert updates["show-1"][0] == "station:retro-kids"
    assert updates["show-1"][2] == 3


def test_interleave_tracks_next_index_per_consumed_episode():
    show = SimpleNamespace(ratingKey="show-1", title="Example Show")
    ep1 = SimpleNamespace(ratingKey="ep-1", title="One")
    ep2 = SimpleNamespace(ratingKey="ep-2", title="Two")

    items, cursor_steps = core.interleave_show_queues(
        [(show, core.deque([(ep1, 2), (ep2, 5)]), "curator")],
        total=1,
        min_show_gap=0,
    )

    assert items == [ep1]
    assert cursor_steps == {"ep-1": (show, 2)}


def test_partial_watch_progress_resumes_same_episode():
    older = core.datetime(2026, 10, 14, 10, 0, tzinfo=core.timezone.utc)
    newer = core.datetime(2026, 10, 14, 11, 0, tzinfo=core.timezone.utc)

    episodes = [
        SimpleNamespace(viewCount=1, viewOffset=0, lastViewedAt=older),
        SimpleNamespace(viewCount=0, viewOffset=300000, lastViewedAt=newer),
        SimpleNamespace(viewCount=0, viewOffset=0, lastViewedAt=None),
    ]

    idx, updated = core.plex_watch_next_index(episodes)

    assert idx == 1
    assert updated == newer


def test_completed_watch_advances_to_next_episode():
    viewed = core.datetime(2026, 10, 14, 11, 0, tzinfo=core.timezone.utc)
    episodes = [
        SimpleNamespace(viewCount=0, viewOffset=0, lastViewedAt=None),
        SimpleNamespace(viewCount=1, viewOffset=0, lastViewedAt=viewed),
        SimpleNamespace(viewCount=0, viewOffset=0, lastViewedAt=None),
    ]

    idx, updated = core.plex_watch_next_index(episodes)

    assert idx == 2
    assert updated == viewed


def test_partial_progress_without_timestamp_is_still_used():
    episodes = [
        SimpleNamespace(viewCount=0, viewOffset=0, lastViewedAt=None),
        SimpleNamespace(viewCount=0, viewOffset=120000, lastViewedAt=None),
        SimpleNamespace(viewCount=0, viewOffset=0, lastViewedAt=None),
    ]

    idx, updated = core.plex_watch_next_index(episodes)

    assert idx == 1
    assert updated is None


def test_station_interstitial_defaults_and_normalization():
    cfg = core.normalize_station("demo", {
        "preset": "all-cartoons",
        "interstitial_playlists": [" Retro Kids Bumpers ", "", "Vintage Commercials"],
        "interstitial_every": 3,
        "interstitial_count": 2,
    })

    assert cfg["interstitial_playlists"] == ["Retro Kids Bumpers", "Vintage Commercials"]
    assert cfg["interstitial_every"] == 3
    assert cfg["interstitial_count"] == 2


def test_inject_interstitials_keeps_program_order():
    programs = [
        SimpleNamespace(ratingKey=f"ep-{i}", title=f"Episode {i}")
        for i in range(1, 6)
    ]
    clips = [
        SimpleNamespace(ratingKey="ad-1", title="Ad 1"),
        SimpleNamespace(ratingKey="ad-2", title="Ad 2"),
    ]

    result = core.inject_interstitials(programs, clips, every=2, count=1)

    assert [item.ratingKey for item in result] == [
        "ep-1", "ep-2", "ad-1", "ep-3", "ep-4", "ad-2", "ep-5"
    ]


def test_collect_interstitial_items_filters_recent_and_duplicates():
    ad1 = SimpleNamespace(ratingKey="ad-1", title="Ad 1", type="movie")
    ad2 = SimpleNamespace(ratingKey="ad-2", title="Ad 2", type="movie")
    playlist_a = SimpleNamespace(title="Ads", items=lambda: [ad1, ad2])
    playlist_b = SimpleNamespace(title="Bumpers", items=lambda: [ad2])
    plex = SimpleNamespace(playlists=lambda: [playlist_a, playlist_b])

    result = core.collect_interstitial_items(
        plex,
        ["Ads", "Bumpers"],
        recent_keys={"ad-1"},
    )

    assert [item.ratingKey for item in result] == ["ad-2"]


def test_station_update_request_accepts_interstitial_settings():
    request = api.StationUpdateRequest(
        interstitial_playlists=["Retro Kids Bumpers", "Vintage Commercials"],
        interstitial_every=3,
        interstitial_count=2,
    )

    assert request.interstitial_every == 3
    assert request.interstitial_count == 2
    assert request.interstitial_playlists == ["Retro Kids Bumpers", "Vintage Commercials"]


def test_legacy_interstitial_playlists_migrate_to_general_pools():
    cfg = core.normalize_station("legacy", {
        "preset": "all-cartoons",
        "interstitial_playlists": ["Bumpers", "Commercials"],
    })

    assert cfg["interstitial_pools"] == [
        {"playlist": "Bumpers", "type": "general", "weight": 1},
        {"playlist": "Commercials", "type": "general", "weight": 1},
    ]


def test_weighted_interstitial_pool_normalization():
    cfg = core.normalize_station("weighted", {
        "preset": "all-cartoons",
        "interstitial_pools": [
            {"playlist": "Station IDs", "type": "station-id", "weight": 20},
            {"playlist": "Bumpers", "type": "bumper", "weight": 35},
            {"playlist": "Commercials", "type": "commercial", "weight": 45},
        ],
    })

    assert cfg["interstitial_playlists"] == ["Station IDs", "Bumpers", "Commercials"]
    assert [pool["weight"] for pool in cfg["interstitial_pools"]] == [20, 35, 45]


def test_choose_weighted_interstitial_uses_pool_weights(monkeypatch):
    id_clip = SimpleNamespace(ratingKey="id-1")
    commercial = SimpleNamespace(ratingKey="ad-1")
    states = [
        {"playlist": "IDs", "type": "station-id", "weight": 20, "items": core.deque([id_clip])},
        {"playlist": "Ads", "type": "commercial", "weight": 80, "items": core.deque([commercial])},
    ]

    def choose_last(population, weights, k):
        assert weights == [20, 80]
        return [population[-1]]

    monkeypatch.setattr(core.random, "choices", choose_last)
    assert core.choose_weighted_interstitial(states) is commercial


def test_weighted_pool_api_model_accepts_type_and_weight():
    request = api.StationUpdateRequest(
        interstitial_pools=[
            api.InterstitialPoolRequest(
                playlist="Vintage Commercials",
                type="commercial",
                weight=45,
            )
        ]
    )

    assert request.interstitial_pools[0].type == "commercial"
    assert request.interstitial_pools[0].weight == 45


def test_parse_interstitial_pool_spec():
    pool = core.parse_interstitial_pool_spec("Station IDs|station-id|20")
    assert pool == {"playlist": "Station IDs", "type": "station-id", "weight": 20}


def test_clean_media_title_removes_common_release_noise():
    assert core.clean_media_title("nickelodeon_bumper_1998_1080p_x264.mp4") == "Nickelodeon Bumper 1998"


def test_infer_interstitial_type_from_filename_and_folder():
    assert core.infer_interstitial_type("/tmp/ads/Cereal Commercial 1994.mp4") == "commercial"
    assert core.infer_interstitial_type("/tmp/Bumpers/Cartoon Network Up Next.mov") == "bumper"
    assert core.infer_interstitial_type("/tmp/Station IDs/Nickelodeon Ident.mp4") == "station-id"


def test_plan_media_organization_uses_metadata_title(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")

    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {
            "title": "Nickelodeon Slime Bumper 1997",
            "comment": None,
            "description": None,
            "source": "ffprobe",
        },
    )

    plan = core.plan_media_organization(tmp_path)
    item = plan["items"][0]

    assert item["confidence"] == "high"
    assert item["type"] == "bumper"
    assert item["proposed_name"] == "Nickelodeon Slime Bumper 1997.mp4"
    assert item["folder"] == "Bumpers"


def test_plan_media_organization_flags_generic_names_for_review(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )

    plan = core.plan_media_organization(tmp_path)
    assert plan["review_count"] == 1
    assert plan["items"][0]["confidence"] == "low"


def test_apply_media_organization_skips_low_confidence_by_default(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(core, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(core, "CONFIG_DIR", tmp_path / "config")

    plan = core.plan_media_organization(tmp_path)
    result = core.apply_media_organization(plan)

    assert clip.exists()
    assert result["applied_count"] == 0
    assert result["skipped_count"] == 1


def test_apply_media_organization_moves_medium_confidence_file(tmp_path, monkeypatch):
    clip = tmp_path / "Cartoon Network Bumper 1999.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(core, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(core, "CONFIG_DIR", tmp_path / "config")

    plan = core.plan_media_organization(tmp_path)
    result = core.apply_media_organization(plan)

    target = tmp_path / "Bumpers" / "Cartoon Network Bumper 1999.mp4"
    assert target.exists()
    assert not clip.exists()
    assert result["applied_count"] == 1


def test_media_organizer_api_routes_registered():
    paths = {route.path for route in api.app.routes}
    assert "/api/v1/media-organizer/scan" in paths
    assert "/api/v1/media-organizer/apply" in paths


def test_media_review_cache_key_changes_when_file_changes(tmp_path):
    clip = tmp_path / "mystery.mp4"
    clip.write_bytes(b"one")
    first = core.media_review_cache_key(clip)
    clip.write_bytes(b"two-two")
    second = core.media_review_cache_key(clip)
    assert first != second


def test_low_confidence_plan_includes_review_frames(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(
        core,
        "extract_media_review_frames",
        lambda _path, frame_count=3: {
            "status": "available",
            "frames": [
                {"id": "abc/frame-1.jpg", "position": 0.12, "timestamp_seconds": 1.2},
                {"id": "abc/frame-2.jpg", "position": 0.5, "timestamp_seconds": 5.0},
            ],
        },
    )

    plan = core.plan_media_organization(tmp_path)
    item = plan["items"][0]
    assert item["review_frame_status"] == "available"
    assert len(item["review_frames"]) == 2


def test_medium_confidence_plan_does_not_extract_review_frames(tmp_path, monkeypatch):
    clip = tmp_path / "Cartoon Network Bumper 1999.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(
        core,
        "extract_media_review_frames",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not run")),
    )

    plan = core.plan_media_organization(tmp_path)
    item = plan["items"][0]
    assert item["review_frame_status"] == "not-needed"
    assert item["review_frames"] == []


def test_media_organizer_frame_route_registered():
    paths = {route.path for route in api.app.routes}
    assert "/api/v1/media-organizer/frame/{cache_key}/{frame_name}" in paths


def test_find_media_tool_falls_back_to_homebrew_paths(monkeypatch):
    monkeypatch.setattr(core.shutil, "which", lambda _name: None)

    class FakePath:
        def __init__(self, value):
            self.value = str(value)
        def __truediv__(self, other):
            return FakePath(self.value.rstrip("/") + "/" + str(other))
        def exists(self):
            return self.value == "/opt/homebrew/bin/ffmpeg"
        def __str__(self):
            return self.value

    original_path = core.Path
    monkeypatch.setattr(core, "Path", FakePath)
    monkeypatch.setattr(core.os, "access", lambda path, mode: str(path) == "/opt/homebrew/bin/ffmpeg")
    try:
        assert core.find_media_tool("ffmpeg") == "/opt/homebrew/bin/ffmpeg"
    finally:
        monkeypatch.setattr(core, "Path", original_path)


def test_review_override_promotes_low_confidence_and_changes_target(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )

    plan = core.plan_media_organization(
        tmp_path,
        overrides=[{
            "source": str(clip),
            "title": "Nickelodeon Slime Bumper 1997",
            "type": "bumper",
        }],
    )
    item = plan["items"][0]

    assert item["confidence"] == "reviewed"
    assert item["reviewed"] is True
    assert item["title_source"] == "review"
    assert item["folder"] == "Bumpers"
    assert item["proposed_name"] == "Nickelodeon Slime Bumper 1997.mp4"


def test_reviewed_low_confidence_clip_can_apply_without_bulk_override(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(core, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(core, "CONFIG_DIR", tmp_path / "config")

    plan = core.plan_media_organization(
        tmp_path,
        overrides=[{
            "source": str(clip),
            "title": "Retro Station ID 1996",
            "type": "station-id",
        }],
    )
    result = core.apply_media_organization(plan, include_low_confidence=False)

    assert result["applied_count"] == 1
    assert (tmp_path / "Station IDs" / "Retro Station ID 1996.mp4").exists()


def test_media_override_api_model():
    override = api.MediaOrganizerOverride(
        source="/tmp/video_0047.mp4",
        title="Nickelodeon Bumper 1997",
        type="bumper",
    )
    request = api.MediaOrganizerApplyRequest(
        path="/tmp",
        overrides=[override],
    )
    assert request.overrides[0].type == "bumper"


def test_fast_media_plan_defers_review_frames(tmp_path, monkeypatch):
    clips = []
    for index in range(4):
        clip = tmp_path / f"video_{index:04}.mp4"
        clip.write_bytes(b"fake")
        clips.append(clip)

    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(
        core,
        "extract_media_review_frames",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("bulk scan must not extract frames")
        ),
    )

    plan = core.plan_media_organization(
        tmp_path,
        extract_review_frames=False,
        metadata_workers=4,
    )

    assert plan["count"] == 4
    assert plan["review_count"] == 4
    assert all(item["review_frame_status"] == "deferred" for item in plan["items"])


def test_bulk_identity_scan_returns_each_source(tmp_path, monkeypatch):
    paths = []
    for index in range(3):
        clip = tmp_path / f"Bumper {index}.mp4"
        clip.write_bytes(b"fake")
        paths.append(clip)

    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )

    identities = core.infer_media_identities_bulk(paths, workers=3)
    assert set(identities) == {str(path.resolve()) for path in paths}


def test_single_file_analysis_generates_frames_for_mystery_clip(tmp_path, monkeypatch):
    clip = tmp_path / "video_0047.mp4"
    clip.write_bytes(b"fake")
    monkeypatch.setattr(
        core,
        "probe_video_metadata",
        lambda _path: {"title": None, "comment": None, "description": None, "source": None},
    )
    monkeypatch.setattr(
        core,
        "extract_media_review_frames",
        lambda _path, frame_count=3: {
            "status": "available",
            "frames": [{"id": "abc/frame-1.jpg", "position": 0.5, "timestamp_seconds": 5}],
        },
    )

    item = core.analyze_media_organizer_file(clip)
    assert item["review_frame_status"] == "available"
    assert len(item["review_frames"]) == 1


def test_media_organizer_analyze_route_registered():
    paths = {route.path for route in api.app.routes}
    assert "/api/v1/media-organizer/analyze" in paths


def test_media_exclude_patterns_are_case_insensitive_and_pre_probe(tmp_path, monkeypatch):
    sample = tmp_path / "Sample.avi"
    movie = tmp_path / "Movie.mkv"
    sample.write_bytes(b"sample")
    movie.write_bytes(b"movie")

    probed = []
    def probe(path):
        probed.append(Path(path).name)
        return {"title": None, "comment": None, "description": None, "source": None}

    monkeypatch.setattr(core, "probe_video_metadata", probe)
    plan = core.plan_media_organization(
        tmp_path,
        exclude_patterns=["sample.*"],
        extract_review_frames=False,
        metadata_workers=1,
    )

    assert plan["total_found"] == 2
    assert plan["count"] == 1
    assert plan["excluded_count"] == 1
    assert plan["excluded_items"][0]["original_name"] == "Sample.avi"
    assert plan["excluded_items"][0]["matched_pattern"] == "sample.*"
    assert probed == ["Movie.mkv"]


def test_media_exclude_pattern_matches_relative_subfolder(tmp_path):
    folder = tmp_path / "Movie One" / "Sample"
    folder.mkdir(parents=True)
    clip = folder / "clip.mkv"
    clip.write_bytes(b"sample")

    included, excluded = core.partition_video_files(
        tmp_path,
        recursive=True,
        exclude_patterns=["*/sample/*"],
    )

    assert included == []
    assert excluded[0]["original_name"] == "clip.mkv"


def test_delete_excluded_media_only_deletes_explicit_matches(tmp_path):
    sample = tmp_path / "Sample.avi"
    movie = tmp_path / "Movie.mkv"
    sample.write_bytes(b"sample")
    movie.write_bytes(b"movie")

    plan = {
        "excluded_items": [{
            "source": str(sample),
            "original_name": sample.name,
            "relative_path": sample.name,
            "matched_pattern": "sample.*",
        }],
        "items": [],
    }
    deleted, errors = core.delete_excluded_media(plan)

    assert errors == []
    assert len(deleted) == 1
    assert not sample.exists()
    assert movie.exists()


def test_media_organizer_request_accepts_excludes_and_delete_flag():
    request = api.MediaOrganizerApplyRequest(
        path="/tmp",
        exclude_patterns=["sample.*", "*/sample/*"],
        delete_excluded=True,
    )
    assert request.exclude_patterns == ["sample.*", "*/sample/*"]
    assert request.delete_excluded is True
