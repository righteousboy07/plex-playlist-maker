from pathlib import Path
from types import SimpleNamespace

import plex_curator as core
import plex_curator_api as api


def _fake_identity(path):
    return {
        "title": Path(path).stem.replace("_", " ").title(),
        "type": "general",
        "confidence": "high",
        "title_source": "filename",
        "metadata_title": None,
    }


def _stub_identities(monkeypatch):
    def fake_bulk(sources, **_kwargs):
        return {
            str(Path(source).resolve()): _fake_identity(source)
            for source in sources
        }

    monkeypatch.setattr(core, "infer_media_identities_bulk", fake_bulk)


def test_no_folder_mode_renames_in_place(tmp_path, monkeypatch):
    _stub_identities(monkeypatch)
    nested = tmp_path / "nested"
    nested.mkdir()
    source = nested / "my_movie.MKV"
    source.write_bytes(b"video")

    plan = core.plan_media_organization(
        tmp_path,
        recursive=True,
        folder_mode="none",
    )

    assert plan["folder_mode"] == "none"
    assert len(plan["items"]) == 1
    item = plan["items"][0]
    assert Path(item["target"]).parent == nested
    assert Path(item["target"]).name == "My Movie.mkv"
    assert item["action"] == "rename"


def test_alpha_mode_groups_under_source_root(tmp_path, monkeypatch):
    _stub_identities(monkeypatch)
    source = tmp_path / "banana_clip.mp4"
    source.write_bytes(b"video")

    plan = core.plan_media_organization(
        tmp_path,
        recursive=False,
        folder_mode="alpha",
    )

    item = plan["items"][0]
    assert Path(item["target"]).parent == tmp_path / "B"
    assert item["folder"] == "B"
    assert Path(item["target"]).name == "Banana Clip.mp4"


def test_destination_no_folder_mode_moves_and_renames(tmp_path, monkeypatch):
    _stub_identities(monkeypatch)
    source_root = tmp_path / "source"
    destination = tmp_path / "destination"
    source_root.mkdir()
    destination.mkdir()
    source = source_root / "example_clip.avi"
    source.write_bytes(b"video")

    plan = core.plan_media_organization(
        source_root,
        destination=destination,
        recursive=False,
        folder_mode="none",
    )

    item = plan["items"][0]
    assert Path(item["target"]).parent == destination
    assert Path(item["target"]).name == "Example Clip.avi"
    assert item["action"] == "move"


def test_alpha_folder_uses_hash_for_non_letters():
    assert core.media_alpha_folder("7th Heaven") == "#"
    assert core.media_alpha_folder("_clip") == "#"
    assert core.media_alpha_folder("zebra") == "Z"


def test_media_request_accepts_folder_mode():
    request = api.MediaOrganizerRequest(path="/tmp/media", folder_mode="alpha")
    assert request.folder_mode == "alpha"


class _FakeSection:
    def __init__(self, title, locations):
        self.title = title
        self.locations = locations
        self.updated = False

    def update(self):
        self.updated = True


def _fake_plex_with_sections(*sections):
    return SimpleNamespace(
        library=SimpleNamespace(sections=lambda: list(sections))
    )


def test_plex_refresh_targets_only_matching_library(monkeypatch):
    movies = _FakeSection("Movies", ["/media/movies"])
    tv = _FakeSection("TV Shows", ["/media/tv"])
    monkeypatch.setattr(
        core,
        "connect",
        lambda: _fake_plex_with_sections(movies, tv),
    )

    result = api.refresh_plex_libraries(
        ["/media/movies/Example/Example.mkv"]
    )

    assert result["scope"] == "targeted"
    assert result["refreshed"] == ["Movies"]
    assert result["errors"] == []
    assert movies.updated is True
    assert tv.updated is False


def test_plex_refresh_targets_multiple_affected_libraries(monkeypatch):
    movies = _FakeSection("Movies", ["/media/movies"])
    tv = _FakeSection("TV Shows", ["/media/tv"])
    music = _FakeSection("Music", ["/media/music"])
    monkeypatch.setattr(
        core,
        "connect",
        lambda: _fake_plex_with_sections(movies, tv, music),
    )

    result = api.refresh_plex_libraries([
        "/media/movies/Example.mkv",
        "/media/tv/Show/Season 1/Episode.mkv",
    ])

    assert result["scope"] == "targeted"
    assert result["refreshed"] == ["Movies", "TV Shows"]
    assert movies.updated is True
    assert tv.updated is True
    assert music.updated is False


def test_plex_refresh_skips_when_changes_are_outside_libraries(monkeypatch):
    movies = _FakeSection("Movies", ["/media/movies"])
    tv = _FakeSection("TV Shows", ["/media/tv"])
    monkeypatch.setattr(
        core,
        "connect",
        lambda: _fake_plex_with_sections(movies, tv),
    )

    result = api.refresh_plex_libraries(["/tmp/export/Example.mkv"])

    assert result["scope"] == "none"
    assert result["refreshed"] == []
    assert result["errors"] == []
    assert movies.updated is False
    assert tv.updated is False


def test_plex_refresh_falls_back_to_all_when_locations_are_unavailable(monkeypatch):
    movies = _FakeSection("Movies", ["/media/movies"])
    unknown = _FakeSection("Unknown", [])
    monkeypatch.setattr(
        core,
        "connect",
        lambda: _fake_plex_with_sections(movies, unknown),
    )

    result = api.refresh_plex_libraries(["/media/movies/Example.mkv"])

    assert result["scope"] == "all-fallback"
    assert result["refreshed"] == ["Movies", "Unknown"]
    assert movies.updated is True
    assert unknown.updated is True


def test_changed_media_paths_include_move_sources_targets_and_deletions():
    result = {
        "applied_items": [
            {
                "source": "/old/Movies/A.mkv",
                "target": "/new/Movies/A.mkv",
            }
        ],
        "deleted_excluded_items": [
            {"source": "/old/Movies/sample.avi"}
        ],
    }

    assert api._changed_media_paths(result) == [
        "/new/Movies/A.mkv",
        "/old/Movies/A.mkv",
        "/old/Movies/sample.avi",
    ]
