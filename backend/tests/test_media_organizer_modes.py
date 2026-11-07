from pathlib import Path

import plex_curator as core


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
