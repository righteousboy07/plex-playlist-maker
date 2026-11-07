from pathlib import Path
from types import SimpleNamespace

import plex_curator as core
import plex_curator_api as api


def test_primary_rar_detection_handles_multipart_sets():
    assert core.is_primary_rar_archive(Path("movie.rar")) is True
    assert core.is_primary_rar_archive(Path("movie.part1.rar")) is True
    assert core.is_primary_rar_archive(Path("movie.part01.rar")) is True
    assert core.is_primary_rar_archive(Path("movie.part001.rar")) is True
    assert core.is_primary_rar_archive(Path("movie.part2.rar")) is False
    assert core.is_primary_rar_archive(Path("movie.part10.rar")) is False
    assert core.is_primary_rar_archive(Path("movie.r00")) is False


def test_safe_archive_member_blocks_escape_paths():
    assert core.safe_archive_member("video/movie.mkv") == Path("video/movie.mkv")
    assert core.safe_archive_member("../escape.mkv") is None
    assert core.safe_archive_member("folder/../../escape.mkv") is None
    assert core.safe_archive_member("/absolute/movie.mkv") is None
    assert core.safe_archive_member(r"C:\\escape\\movie.mkv") is None


def test_archive_destination_preserves_source_parent_hierarchy(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    archive = source / "Show Name" / "Season 01" / "episode.rar"
    archive.parent.mkdir(parents=True)
    destination.mkdir()

    result = core.archive_destination_base(source, archive, destination)

    assert result == destination / "Show Name" / "Season 01"


def test_plan_rar_import_preserves_archive_child_folders(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    archive = source / "Show Name" / "Season 01" / "episode.part01.rar"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"rar")
    destination.mkdir()

    monkeypatch.setattr(
        core,
        "rar_extractor",
        lambda: {"name": "unrar", "path": "/fake/unrar", "list_path": None},
    )
    monkeypatch.setattr(core, "find_rar_archives", lambda *_args, **_kwargs: [archive])
    monkeypatch.setattr(
        core,
        "list_rar_members",
        lambda *_args, **_kwargs: (
            [
                Path("Episode Folder") / "episode.mkv",
                Path("Episode Folder") / "episode.en.srt",
                Path("notes.txt"),
            ],
            [],
        ),
    )

    plan = core.plan_rar_import(source, destination, media_only=True)

    assert plan["archive_count"] == 1
    assert plan["ready_count"] == 1
    item = plan["items"][0]
    assert item["relative_parent"] == "Show Name/Season 01"
    assert Path(item["destination_parent"]) == destination / "Show Name" / "Season 01"
    assert item["files"] == [
        "Episode Folder/episode.mkv",
        "Episode Folder/episode.en.srt",
    ]


def test_plan_blocks_archives_with_unsafe_members(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    archive = source / "movie.rar"
    source.mkdir()
    destination.mkdir()
    archive.write_bytes(b"rar")

    monkeypatch.setattr(
        core,
        "rar_extractor",
        lambda: {"name": "unrar", "path": "/fake/unrar", "list_path": None},
    )
    monkeypatch.setattr(core, "find_rar_archives", lambda *_args, **_kwargs: [archive])
    monkeypatch.setattr(
        core,
        "list_rar_members",
        lambda *_args, **_kwargs: ([Path("movie.mkv")], ["../escape.txt"]),
    )

    plan = core.plan_rar_import(source, destination)

    assert plan["blocked_count"] == 1
    assert plan["ready_count"] == 0
    assert plan["items"][0]["status"] == "blocked"


def test_apply_rar_import_copies_preserved_tree_and_avoids_overwrite(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    archive = source / "Show" / "Season 1" / "episode.rar"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"rar")
    destination.mkdir()

    fake_plan = {
        "source": str(source),
        "destination": str(destination),
        "recursive": True,
        "media_only": True,
        "extractor": "unrar",
        "archive_count": 1,
        "ready_count": 1,
        "blocked_count": 0,
        "items": [{
            "archive": str(archive),
            "relative_parent": "Show/Season 1",
            "destination_parent": str(destination / "Show" / "Season 1"),
            "file_count": 1,
            "files": ["Child/episode.mkv"],
            "unsafe_members": [],
            "status": "ready",
        }],
    }

    monkeypatch.setattr(core, "plan_rar_import", lambda *_args, **_kwargs: fake_plan)
    monkeypatch.setattr(
        core,
        "rar_extractor",
        lambda: {"name": "unrar", "path": "/fake/unrar", "list_path": None},
    )

    def fake_run(command, capture_output, text, check):
        temp_root = Path(command[-1])
        extracted = temp_root / "Child" / "episode.mkv"
        extracted.parent.mkdir(parents=True)
        extracted.write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    existing = destination / "Show" / "Season 1" / "Child" / "episode.mkv"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"existing")

    result = core.apply_rar_import(source, destination)

    assert result["copied_count"] == 1
    copied_target = Path(result["copied"][0]["target"])
    assert copied_target == existing.with_name("episode (2).mkv")
    assert existing.read_bytes() == b"existing"
    assert copied_target.read_bytes() == b"video"


def test_archive_import_api_routes_registered():
    paths = {route.path for route in api.app.routes}
    assert "/api/v1/media-organizer/archive-import/status" in paths
    assert "/api/v1/media-organizer/archive-import/preview" in paths
    assert "/api/v1/media-organizer/archive-import/apply" in paths
