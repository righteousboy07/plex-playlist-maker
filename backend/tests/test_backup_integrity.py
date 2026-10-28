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


def test_restore_backup_restores_owned_files_and_creates_safety_snapshot(tmp_path, monkeypatch):
    config = configure_paths(tmp_path, monkeypatch)
    (config / ".env").write_text("PLEX_TOKEN=old\n", encoding="utf-8")
    (config / "stations.json").write_text('{"version":"old"}', encoding="utf-8")
    with sqlite3.connect(config / "state.sqlite3") as db:
        db.execute("CREATE TABLE records (name TEXT)")
        db.execute("INSERT INTO records VALUES ('old')")

    backup = core.create_backup("known-good")

    (config / ".env").write_text("PLEX_TOKEN=new\n", encoding="utf-8")
    (config / "stations.json").write_text('{"version":"new"}', encoding="utf-8")
    with sqlite3.connect(config / "state.sqlite3") as db:
        db.execute("DELETE FROM records")
        db.execute("INSERT INTO records VALUES ('new')")

    result = core.restore_backup(backup.name)

    assert result["restored_backup"] == backup.name
    assert result["pre_restore_backup"].endswith("-pre-restore")
    assert (config / ".env").read_text(encoding="utf-8") == "PLEX_TOKEN=old\n"
    assert (config / "stations.json").read_text(encoding="utf-8") == '{"version":"old"}'
    with sqlite3.connect(config / "state.sqlite3") as db:
        assert db.execute("SELECT name FROM records").fetchone() == ("old",)


def test_restore_backup_rejects_manifest_path_escape(tmp_path, monkeypatch):
    config = configure_paths(tmp_path, monkeypatch)
    core.ensure_config()
    backup = core.BACKUP_DIR / "bad-backup"
    backup.mkdir(parents=True)
    (backup / "manifest.json").write_text(
        json.dumps({"files": ["../outside.txt"]}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        core.restore_backup("bad-backup")
