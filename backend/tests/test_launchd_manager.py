import importlib.util
import plistlib
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "launchd-manager.py"
SPEC = importlib.util.spec_from_file_location("plex_curator_launchd", MODULE_PATH)
launchd = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(launchd)


def write_plist(path: Path, label: str):
    with path.open("wb") as fh:
        plistlib.dump({"Label": label}, fh)


def test_cleanup_stale_removes_legacy_and_preserves_current(tmp_path, monkeypatch):
    launch_agents = tmp_path / "LaunchAgents"
    launch_agents.mkdir()

    current = launch_agents / "com.ry.plexcurator.api.plist"
    legacy = launch_agents / "com.ry.plex-curator.api.plist"
    unrelated = launch_agents / "com.example.other.plist"

    write_plist(current, "com.ry.plexcurator.api")
    write_plist(legacy, "com.ry.plex-curator.api")
    write_plist(unrelated, "com.example.other")

    monkeypatch.setattr(launchd, "LAUNCH_AGENTS", launch_agents)
    monkeypatch.setattr(
        launchd,
        "run",
        lambda _cmd: type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    removed = launchd.cleanup_stale()

    assert str(legacy) in removed
    assert not legacy.exists()
    assert current.exists()
    assert unrelated.exists()


def test_reconcile_reinstalls_existing_current_jobs_and_required_jobs(tmp_path, monkeypatch):
    launch_agents = tmp_path / "LaunchAgents"
    launch_agents.mkdir()
    write_plist(
        launch_agents / "com.ry.plexcurator.saturdaymorning.plist",
        "com.ry.plexcurator.saturdaymorning",
    )

    installed = []
    monkeypatch.setattr(launchd, "LAUNCH_AGENTS", launch_agents)
    monkeypatch.setattr(launchd, "cleanup_stale", lambda: [])
    monkeypatch.setattr(launchd, "install", lambda name: installed.append(name))

    launchd.reconcile()

    assert "saturday-morning" in installed
    assert "api-server" in installed
    assert "log-cleanup" in installed
