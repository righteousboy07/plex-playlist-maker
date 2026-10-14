#!/usr/bin/env python3
import argparse
import os
import plistlib
import subprocess
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
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
        "args": ["wishlist-check", str(APP_DIR / "kids-scary-missing-wishlist.txt")],
        "description": "Sunday at 9:00 AM",
    },
    "stations-nightly": {
        "label": "com.ry.plexcurator.stationsnightly",
        "calendar": {"Hour": 3, "Minute": 30},
        "args": ["station-refresh-all"],
        "description": "Daily at 3:30 AM; refresh every enabled station profile",
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

def status(name):
    job = JOBS[name]
    res = run(["launchctl", "print", f"gui/{os.getuid()}/{job['label']}"])
    print(f"{name}: {'loaded' if res.returncode == 0 else 'not loaded'}")
    print(f"plist exists: {plist_path(job['label']).exists()}")
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if "state =" in line or "last exit code =" in line or "runs =" in line:
                print(line.strip())

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

def main():
    ap = argparse.ArgumentParser(prog="launchd-manager.py")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("list"); p.set_defaults(fn=lambda a: list_jobs())
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
