from pathlib import Path

import plex_curator as core


def test_plan_rar_import_preserves_source_hierarchy(tmp_path, monkeypatch):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    nested = source / "Movies" / "Action"
    nested.mkdir(parents=True)
    (nested / "feature.rar").write_bytes(b"not-a-real-rar")
    (source / "root.rar").write_bytes(b"not-a-real-rar")

    monkeypatch.setattr(
        core,
        "find_rar_extractor",
        lambda: {"name": "unar", "path": "/usr/bin/unar"},
    )

    plan = core.plan_rar_import(source, destination)

    assert plan["archive_count"] == 2
    by_name = {item["archive_name"]: item for item in plan["archives"]}
    assert Path(by_name["feature.rar"]["target_root"]) == destination / "Movies" / "Action"
    assert by_name["feature.rar"]["relative_parent"] == str(Path("Movies") / "Action")
    assert Path(by_name["root.rar"]["target_root"]) == destination
    assert by_name["root.rar"]["relative_parent"] == ""


def test_copy_extracted_tree_preserves_internal_children_and_filters_media(tmp_path):
    extracted = tmp_path / "extracted"
    target = tmp_path / "target"
    (extracted / "Season 01").mkdir(parents=True)
    (extracted / "Season 01" / "Episode 01.mkv").write_bytes(b"video")
    (extracted / "Season 01" / "notes.nfo").write_text("metadata", encoding="utf-8")
    (extracted / ".DS_Store").write_bytes(b"junk")

    copied, skipped = core._copy_extracted_tree(
        extracted,
        target,
        media_only=True,
    )

    assert skipped == []
    assert len(copied) == 1
    assert (target / "Season 01" / "Episode 01.mkv").read_bytes() == b"video"
    assert not (target / "Season 01" / "notes.nfo").exists()


def test_copy_extracted_tree_never_overwrites_existing_files(tmp_path):
    extracted = tmp_path / "extracted"
    target = tmp_path / "target"
    extracted.mkdir()
    target.mkdir()
    (extracted / "movie.mp4").write_bytes(b"new")
    (target / "movie.mp4").write_bytes(b"existing")

    copied, skipped = core._copy_extracted_tree(
        extracted,
        target,
        media_only=True,
    )

    assert copied == []
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "target-exists"
    assert (target / "movie.mp4").read_bytes() == b"existing"


def test_split_rar_sets_only_process_first_volume(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "movie.part01.rar").write_bytes(b"part1")
    (source / "movie.part02.rar").write_bytes(b"part2")
    (source / "standalone.rar").write_bytes(b"single")

    archives = core.iter_rar_archives(source)

    assert [path.name for path in archives] == [
        "movie.part01.rar",
        "standalone.rar",
    ]
