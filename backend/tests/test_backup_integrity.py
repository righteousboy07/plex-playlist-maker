import json
import sqlite3

import pytest

import plex_curator as core


def configure_paths(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    for attr, name in (
        ("CONFIG_FILE", ".env"),
        ("PRESETS_FILE", "presets.json"),
        ("SCHEDULES_FILE", "schedules.json"),
        ("STATIONS_FILE", "stations.json"),
        ("MEDIA_ORGANIZER_PRESETS_FILE", "media-organizer-presets.json"),
        ("STATE_DB", "state.sqlite3"),
    ):
        monkeypatch.setattr(core, attr, config / name)
    monkeypatch.setattr(core, "CONFIG_DIR", config)
    monkeypatch.setattr(core, "BACKUP_DIR", config / "backups")
    return config


def test_backup_copies_settings_and_valid_sqlite(tmp_path, monkeypatch):
    config = configure_paths(tmp_path, monkeypatch)
    (config / ".env").write_text("PLEX_TOKEN=example\n", encoding="utf-8")
    (config / "stations.json").write_text('{"stations":[]}', encoding="utf-8")
    with sqlite3.connect(config / "state.sqlite3") as db:
        db.execute("CREATE TABLE records (name TEXT)")
        db.execute("INSERT INTO records VALUES ('preserved')")

    target = core.create_backup("test")
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert {".env", "stations.json", "state.sqlite3"} <= set(manifest["files"])
    assert (target / ".env").read_bytes() == (config / ".env").read_bytes()
    with sqlite3.connect(target / "state.sqlite3") as db:
        assert db.execute("SELECT name FROM records").fetchone() == ("preserved",)
        assert db.execute("PRAGMA quick_check").fetchone() == ("ok",)


def test_backup_refuses_corrupt_sqlite(tmp_path, monkeypatch):
    config = configure_paths(tmp_path, monkeypatch)
    (config / "state.sqlite3").write_bytes(b"not a sqlite database")
    with pytest.raises(sqlite3.DatabaseError):
        core.create_backup("invalid")
    assert not list((config / "backups").glob("*/manifest.json"))
