#!/usr/bin/env python3
import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
HOME = Path.home()
LAUNCH_AGENTS = HOME / "Library" / "LaunchAgents"
LOG_DIR = HOME / "Library" / "Logs" / "PlexCurator"

JOBS = {
    "saturday-morning": {
        "label": "com.ry.plexcurator.saturdaymorning",
        "calendar": {"Weekday": 7, "Hour": 7, "Minute": 30},
        "args": ["schedule-build","saturday-morning","--create","--replace","--avoid-recent","180","--min-show-gap","2","--seasonal","auto"],
        "description": "Saturday at 7:30 AM",
    },
    "retro-toon-night": {
        "label": "com.ry.plexcurator.retrotoonnight",
        "calendar": {"Weekday": 6, "Hour": 17, "Minute": 0},
        "args": ["schedule-build","retro-toon-night","--create","--replace","--avoid-recent","120","--min-show-gap","2"],
        "description": "Friday at 5:00 PM",
    },
    "80s-cartoon-refresh": {
        "label": "com.ry.plexcurator.80scartoons",
        "calendar": {"Weekday": 2, "Hour": 4, "Minute": 15},
        "args": ["channel","--preset","80s-cartoons","--create","--replace","--avoid-recent","150","--min-show-gap","2","--seasonal","auto"],
        "description": "Monday at 4:15 AM",
    },
    "90s-cartoon-refresh": {
        "label": "com.ry.plexcurator.90scartoons",
        "calendar": {"Weekday": 3, "Hour": 4, "Minute": 15},
        "args": ["channel","--preset","90s-cartoons","--create","--replace","--avoid-recent","150","--min-show-gap","2","--seasonal","auto"],
        "description": "Tuesday at 4:15 AM",
    },
    "all-cartoon-refresh": {
        "label": "com.ry.plexcurator.allcartoons",
        "calendar": {"Weekday": 4, "Hour": 4, "Minute": 15},
        "args": ["channel","--preset","all-cartoons","--create","--replace","--avoid-recent","200","--min-show-gap","3","--seasonal","auto"],
        "description": "Wednesday at 4:15 AM",
    },
    "october-kids": {
        "label": "com.ry.plexcurator.octoberkids",
        "calendar": {"Month": 10, "Hour": 7, "Minute": 0},
        "args": ["schedule-build","october-kids","--create","--replace","--seasonal","halloween","--avoid-recent","200"],
        "description": "Daily at 7:00 AM during October",
    },
    "kids-scary-wishlist": {
        "label": "com.ry.plexcurator.kidsscarywishlist",
        "calendar": {"Weekday": 1, "Hour": 9, "Minute": 0},
        "args": ["wishlist-check", str(APP_DIR / "examples" / "kids-scary-missing-wishlist.txt")],
        "description": "Sunday at 9:00 AM",
    },
    "stations-nightly": {
        "label": "com.ry.plexcurator.stationsnightly",
        "calendar": {"Hour": 3, "Minute": 30},
        "args": ["station-refresh-all"],
        "description": "Daily at 3:30 AM; refresh every enabled station profile",
    },
    "log-cleanup": {
        "label": "com.ry.plexcurator.logcleanup",
        "calendar": {"Hour": 2, "Minute": 45},
        "args": ["logs-cleanup"],
        "description": "Daily retention check; clears Plex Curator logs every 30 days",
    },
    "api-server": {
        "label": "com.ry.plexcurator.api",
        "program": str(APP_DIR / "plex-curator-api"),
        "args": ["serve", "--port", "8765", "--no-access-log"],
        "keep_alive": True,
        "description": "Persistent localhost API on 127.0.0.1:8765",
    },
}

def plist_path(label):
    return LAUNCH_AGENTS / f"{label}.plist"

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

def plist(name, job):
    program = job.get("program", str(APP_DIR / "plex-curator"))
    data = {
        "Label": job["label"],
        "ProgramArguments": [program] + job["args"],
        "WorkingDirectory": str(APP_DIR),
        "StandardOutPath": str(LOG_DIR / f"{name}.out.log"),
        "StandardErrorPath": str(LOG_DIR / f"{name}.err.log"),
        "ProcessType": "Background",
        "EnvironmentVariables": {
            "HOME": str(HOME),
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        },
    }

    if job.get("keep_alive"):
        data["RunAtLoad"] = True
        data["KeepAlive"] = True
        data["ThrottleInterval"] = 10
    else:
        data["RunAtLoad"] = False
        data["StartCalendarInterval"] = job["calendar"]

    return data

def install(name):
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    job = JOBS[name]
    path = plist_path(job["label"])
    run(["launchctl", "bootout", f"gui/{os.getuid()}", str(path)])
    with path.open("wb") as fh:
        plistlib.dump(plist(name, job), fh, sort_keys=False)
    os.chmod(path, 0o644)
    res = run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(path)])
    print(f"Installed {name}: {job['description']}")
    print(f"plist: {path}")
    if res.returncode:
        print((res.stderr or res.stdout).strip())

def uninstall(name):
    job = JOBS[name]
    path = plist_path(job["label"])
    run(["launchctl", "bootout", f"gui/{os.getuid()}", str(path)])
    if path.exists():
        path.unlink()
    print(f"Removed {name}")

def job_snapshot(name):
    job = JOBS[name]
    path = plist_path(job["label"])
    res = run(["launchctl", "print", f"gui/{os.getuid()}/{job['label']}"])
    loaded = res.returncode == 0
    state = None
    last_exit_code = None
    runs = None
    if loaded:
        for line in res.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("state ="):
                state = stripped.split("=", 1)[1].strip()
            elif stripped.startswith("last exit code ="):
                value = stripped.split("=", 1)[1].strip()
                try:
                    last_exit_code = int(value)
                except ValueError:
                    last_exit_code = value
            elif stripped.startswith("runs ="):
                value = stripped.split("=", 1)[1].strip()
                try:
                    runs = int(value)
                except ValueError:
                    runs = value
    return {
        "name": name,
        "label": job["label"],
        "description": job["description"],
        "loaded": loaded,
        "plist_exists": path.exists(),
        "state": state,
        "last_exit_code": last_exit_code,
        "runs": runs,
        "keep_alive": bool(job.get("keep_alive", False)),
        "protected": name == "api-server",
    }

def status(name):
    snap = job_snapshot(name)
    print(f"{name}: {'loaded' if snap['loaded'] else 'not loaded'}")
    print(f"plist exists: {snap['plist_exists']}")
    if snap["state"] is not None:
        print(f"state = {snap['state']}")
    if snap["last_exit_code"] is not None:
        print(f"last exit code = {snap['last_exit_code']}")
    if snap["runs"] is not None:
        print(f"runs = {snap['runs']}")

def run_now(name):
    job = JOBS[name]
    target = f"gui/{os.getuid()}/{job['label']}"
    res = run(["launchctl", "kickstart", "-k", target])
    if res.returncode == 0:
        print(f"Triggered {name}")
    else:
        print("Job not loaded; running the command directly.")
        subprocess.run([str(APP_DIR / "plex-curator")] + job["args"])

def list_jobs():
    for name, job in JOBS.items():
        print(f"{name:24} {job['description']}")

def list_jobs_json():
    import json
    print(json.dumps({"jobs": [job_snapshot(name) for name in JOBS]}, indent=2))

def status_json(name):
    import json
    print(json.dumps(job_snapshot(name), indent=2))

def main():
    ap = argparse.ArgumentParser(prog="launchd-manager.py")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("list"); p.set_defaults(fn=lambda a: list_jobs())
    p = sp.add_parser("list-json"); p.set_defaults(fn=lambda a: list_jobs_json())
    p = sp.add_parser("status-json"); p.add_argument("name", choices=JOBS); p.set_defaults(fn=lambda a: status_json(a.name))
    p = sp.add_parser("install"); p.add_argument("name", choices=JOBS); p.set_defaults(fn=lambda a: install(a.name))
    p = sp.add_parser("install-all"); p.set_defaults(fn=lambda a: [install(n) for n in JOBS])
    p = sp.add_parser("uninstall"); p.add_argument("name", choices=JOBS); p.set_defaults(fn=lambda a: uninstall(a.name))
    p = sp.add_parser("uninstall-all"); p.set_defaults(fn=lambda a: [uninstall(n) for n in JOBS])
    p = sp.add_parser("status"); p.add_argument("name", choices=JOBS); p.set_defaults(fn=lambda a: status(a.name))
    p = sp.add_parser("run-now"); p.add_argument("name", choices=JOBS); p.set_defaults(fn=lambda a: run_now(a.name))

    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
