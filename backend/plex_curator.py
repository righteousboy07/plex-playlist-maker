#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import sqlite3
import sys
from collections import Counter
from collections import deque
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from plexapi.exceptions import NotFound
from plexapi.server import PlexServer

APP_DIR = Path(__file__).resolve().parent
HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "plex-curator"
CONFIG_FILE = CONFIG_DIR / ".env"
STATE_DB = CONFIG_DIR / "state.sqlite3"
PRESETS_FILE = CONFIG_DIR / "presets.json"
SCHEDULES_FILE = CONFIG_DIR / "schedules.json"
STATIONS_FILE = CONFIG_DIR / "stations.json"
EXPORT_DIR = CONFIG_DIR / "exports"
BACKUP_DIR = CONFIG_DIR / "backups"
LOG_DIR = HOME / "Library" / "Logs" / "PlexCurator"
APP_VERSION = "13.2.3"

DEFAULT_MOVIE_PRESETS = {
    "kids-scary": {
        "description": "Gentler spooky/family movies.",
        "library": "Movies",
        "genre_any": ["Family", "Animation", "Fantasy", "Comedy", "Horror"],
        "content_ratings": ["G", "PG"],
        "year_min": 1980,
        "limit": 30,
        "random": False,
        "playlist": "Kids Scary Movies",
    },
    "friday-movie-night": {
        "description": "A short randomized group of unwatched movies.",
        "library": "Movies",
        "unwatched": True,
        "max_runtime": 130,
        "limit": 5,
        "random": True,
    },
    "unwatched-gems": {
        "description": "Unwatched movies with strong audience ratings.",
        "library": "Movies",
        "unwatched": True,
        "min_audience": 7.5,
        "limit": 25,
        "random": False,
    },
    "forgotten-80s": {
        "description": "Unwatched movies from the 1980s.",
        "library": "Movies",
        "year_min": 1980,
        "year_max": 1989,
        "unwatched": True,
        "limit": 30,
        "random": False,
    },
    "october-horror": {
        "description": "Unwatched horror picks for October.",
        "library": "Movies",
        "genre": "Horror",
        "unwatched": True,
        "limit": 31,
        "random": True,
        "playlist": "October Horror",
    },
}

CHANNEL_PRESETS = {
    "80s-cartoons": {
        "description": "Family-oriented animated shows that began in the 1980s.",
        "year_min": 1980,
        "year_max": 1989,
        "kids_only": True,
        "playlist": "80s Cartoon Channel",
    },
    "90s-cartoons": {
        "description": "Family-oriented animated shows that began in the 1990s.",
        "year_min": 1990,
        "year_max": 1999,
        "kids_only": True,
        "playlist": "90s Cartoon Channel",
    },
    "all-cartoons": {
        "description": "Family-oriented animated shows from all decades.",
        "kids_only": True,
        "playlist": "Cartoon Channel",
    },
    "saturday-morning": {
        "description": "A broad family-friendly Saturday-morning-style cartoon rotation.",
        "kids_only": True,
        "playlist": "Saturday Morning Cartoons",
    },
}


DEFAULT_STATIONS = {
    "retro-kids": {
        "name": "Retro Kids",
        "description": "Family-friendly animation from 1980 through 1999.",
        "enabled": True,
        "playlist": "Retro Kids Channel",
        "preset": "all-cartoons",
        "year_min": 1980,
        "year_max": 1999,
        "kids_only": True,
        "adult": False,
        "per_show": 6,
        "total": 60,
        "avoid_recent": 220,
        "min_show_gap": 3,
        "seasonal": "auto",
        "special_every": 8,
        "unwatched": False,
        "sync_watch_progress": True,
        "include_shows": [],
        "exclude_shows": [],
    },
    "80s-cartoons": {
        "name": "80s Cartoon Channel",
        "description": "Family-oriented animated shows that began in the 1980s.",
        "enabled": True,
        "playlist": "80s Cartoon Channel",
        "preset": "80s-cartoons",
        "kids_only": True,
        "adult": False,
        "per_show": 6,
        "total": 50,
        "avoid_recent": 180,
        "min_show_gap": 2,
        "seasonal": "auto",
        "special_every": 8,
        "unwatched": False,
        "sync_watch_progress": True,
        "include_shows": [],
        "exclude_shows": [],
    },
    "90s-cartoons": {
        "name": "90s Cartoon Channel",
        "description": "Family-oriented animated shows that began in the 1990s.",
        "enabled": True,
        "playlist": "90s Cartoon Channel",
        "preset": "90s-cartoons",
        "kids_only": True,
        "adult": False,
        "per_show": 6,
        "total": 50,
        "avoid_recent": 180,
        "min_show_gap": 2,
        "seasonal": "auto",
        "special_every": 8,
        "unwatched": False,
        "sync_watch_progress": True,
        "include_shows": [],
        "exclude_shows": [],
    },
    "spooky-tv": {
        "name": "Spooky TV",
        "description": "Family cartoon station with Halloween specials inserted year-round.",
        "enabled": False,
        "playlist": "Spooky TV",
        "preset": "all-cartoons",
        "kids_only": True,
        "adult": False,
        "per_show": 5,
        "total": 50,
        "avoid_recent": 200,
        "min_show_gap": 3,
        "seasonal": "halloween",
        "special_every": 5,
        "unwatched": False,
        "sync_watch_progress": True,
        "include_shows": [],
        "exclude_shows": [],
    },
    "christmas-cartoons": {
        "name": "Christmas Cartoons",
        "description": "Family cartoon station with Christmas and holiday specials.",
        "enabled": False,
        "playlist": "Christmas Cartoons",
        "preset": "all-cartoons",
        "kids_only": True,
        "adult": False,
        "per_show": 5,
        "total": 50,
        "avoid_recent": 200,
        "min_show_gap": 3,
        "seasonal": "christmas",
        "special_every": 5,
        "unwatched": False,
        "sync_watch_progress": True,
        "include_shows": [],
        "exclude_shows": [],
    },
    "adult-animation": {
        "name": "Adult Animation",
        "description": "Animation station that allows mature-rated series.",
        "enabled": False,
        "playlist": "Adult Animation",
        "preset": "all-cartoons",
        "kids_only": False,
        "adult": True,
        "per_show": 5,
        "total": 50,
        "avoid_recent": 180,
        "min_show_gap": 3,
        "seasonal": "none",
        "special_every": 8,
        "unwatched": False,
        "sync_watch_progress": True,
        "include_shows": [],
        "exclude_shows": [],
    },
}

DEFAULT_SCHEDULES = {
    "saturday-morning": {
        "description": "A nostalgic multi-hour cartoon block with a family movie.",
        "playlist": "Saturday Morning TV",
        "blocks": [
            {"name": "80s Kickoff", "type": "cartoons", "preset": "80s-cartoons", "minutes": 60},
            {"name": "90s Power Hour", "type": "cartoons", "preset": "90s-cartoons", "minutes": 60},
            {"name": "Mixed Cartoons", "type": "cartoons", "preset": "all-cartoons", "minutes": 75},
            {"name": "Family Movie", "type": "movie", "preset": "kids-scary", "minutes": 120},
        ],
    },
    "retro-toon-night": {
        "description": "A two-hour 80s/90s cartoon block.",
        "playlist": "Retro Toon Night",
        "blocks": [
            {"name": "80s", "type": "cartoons", "preset": "80s-cartoons", "minutes": 60},
            {"name": "90s", "type": "cartoons", "preset": "90s-cartoons", "minutes": 60},
        ],
    },
    "october-kids": {
        "description": "Family spooky programming with seasonal cartoon inserts and a movie.",
        "playlist": "October Kids Channel",
        "blocks": [
            {"name": "Spooky Cartoons", "type": "cartoons", "preset": "all-cartoons", "minutes": 90, "seasonal": "halloween"},
            {"name": "Kids Scary Movie", "type": "movie", "preset": "kids-scary", "minutes": 120},
        ],
    },
}

SEASONAL_KEYWORDS = {
    "halloween": ["halloween", "ghost", "haunted", "monster", "witch", "vampire", "spooky", "pumpkin", "scare"],
    "christmas": ["christmas", "xmas", "santa", "holiday", "snow", "reindeer", "mistletoe", "north pole"],
}

def ensure_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not PRESETS_FILE.exists():
        PRESETS_FILE.write_text(json.dumps(DEFAULT_MOVIE_PRESETS, indent=2), encoding="utf-8")
    if not SCHEDULES_FILE.exists():
        SCHEDULES_FILE.write_text(json.dumps(DEFAULT_SCHEDULES, indent=2), encoding="utf-8")
    if not STATIONS_FILE.exists():
        STATIONS_FILE.write_text(json.dumps(DEFAULT_STATIONS, indent=2), encoding="utf-8")
    init_db()

def init_db():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS episode_play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating_key TEXT,
            show_title TEXT,
            season_number INTEGER,
            episode_number INTEGER,
            episode_title TEXT,
            selected_at TEXT,
            channel_name TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_episode_history_channel_time ON episode_play_history(channel_name, selected_at)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS show_cursor (
            show_rating_key TEXT PRIMARY KEY,
            show_title TEXT,
            next_episode_index INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS build_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT,
            playlist_name TEXT,
            built_at TEXT,
            item_count INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS channel_show_cursor (
            channel_name TEXT NOT NULL,
            show_rating_key TEXT NOT NULL,
            show_title TEXT,
            next_episode_index INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT,
            PRIMARY KEY(channel_name, show_rating_key)
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_show_cursor_channel
        ON channel_show_cursor(channel_name)
    """)
    # Seed channel-scoped cursors from the legacy global cursor table once.
    cur.execute("SELECT COUNT(*) FROM channel_show_cursor")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            SELECT DISTINCT channel_name
            FROM (
                SELECT channel_name FROM episode_play_history
                UNION
                SELECT channel_name FROM build_history
            )
            WHERE channel_name IS NOT NULL AND channel_name != ''
        """)
        legacy_channels = [row[0] for row in cur.fetchall()]
        for channel_name in legacy_channels:
            cur.execute("""
                INSERT OR IGNORE INTO channel_show_cursor(
                    channel_name, show_rating_key, show_title,
                    next_episode_index, updated_at
                )
                SELECT ?, show_rating_key, show_title,
                       next_episode_index, updated_at
                FROM show_cursor
            """, (channel_name,))
    # Migrate the simple v8 history once if it exists.
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='episode_history'")
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) FROM episode_play_history")
        if cur.fetchone()[0] == 0:
            try:
                cur.execute("""
                    INSERT INTO episode_play_history(
                        rating_key, show_title, season_number, episode_number,
                        episode_title, selected_at, channel_name
                    )
                    SELECT rating_key, show_title, season_number, episode_number,
                           episode_title, selected_at, channel_name
                    FROM episode_history
                """)
            except sqlite3.Error:
                pass
    con.commit()
    con.close()

def load_env():
    ensure_config()
    load_dotenv(CONFIG_FILE)

def connect() -> PlexServer:
    load_env()
    url = os.getenv("PLEX_URL", "http://127.0.0.1:32400").strip()
    token = os.getenv("PLEX_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "PLEX_TOKEN is missing.\n"
            "Run ./plex-curator setup or edit ~/.config/plex-curator/.env"
        )
    return PlexServer(url, token, timeout=30)

def get_section(plex: PlexServer, name: str):
    try:
        return plex.library.section(name)
    except NotFound:
        available = ", ".join(s.title for s in plex.library.sections())
        raise SystemExit(f'Library "{name}" not found. Available: {available}')

def safe_date(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)

def parse_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def tags(values):
    out = set()
    for v in values or []:
        name = getattr(v, "tag", None) or getattr(v, "title", None) or str(v)
        if name:
            out.add(str(name).casefold())
    return out

def tags_join(values):
    vals = []
    for v in values or []:
        name = getattr(v, "tag", None) or getattr(v, "title", None)
        if name:
            vals.append(str(name))
    return "; ".join(vals)

def is_watched(item):
    return (getattr(item, "viewCount", 0) or 0) > 0

def runtime_minutes(item):
    d = getattr(item, "duration", None)
    return d / 60000 if d else None

def numeric(item, attr):
    try:
        v = getattr(item, attr, None)
        return float(v) if v is not None else None
    except Exception:
        return None

def item_label(item):
    y = getattr(item, "year", None)
    t = getattr(item, "type", item.__class__.__name__)
    return f"{item.title}{f' ({y})' if y else ''} [{t}]"

def find_playlist(plex, title):
    for p in plex.playlists():
        if p.title.casefold() == title.casefold():
            return p
    return None

def create_playlist(plex, title, items, replace=False):
    existing = find_playlist(plex, title)
    if existing:
        if not replace:
            raise SystemExit(f'Playlist "{title}" exists. Use --replace.')
        existing.delete()
    p = plex.createPlaylist(title, items=items)
    print(f'\nCreated playlist "{p.title}" with {len(items)} items.')
    return p

def resolve_title(section, title, year=None):
    hits = section.search(title=title)
    exact = [x for x in hits if getattr(x, "title", "").strip().casefold() == title.strip().casefold()]
    hits = exact or hits
    if year is not None:
        yh = [x for x in hits if getattr(x, "year", None) == year]
        hits = yh or hits
    return hits[0] if hits else None

def parse_title_spec(spec):
    if "|" not in spec:
        return spec.strip(), None
    left, right = spec.rsplit("|", 1)
    try:
        return left.strip(), int(right.strip())
    except ValueError:
        return spec.strip(), None


# ---------------------------------------------------------------------------
# Backups / reliability helpers (v11)
# ---------------------------------------------------------------------------

def backup_sqlite(source, destination):
    if not source.exists():
        return False
    src = sqlite3.connect(source)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    return True

def create_backup(reason="manual"):
    ensure_config()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"{stamp}-{reason}"
    target.mkdir(parents=True, exist_ok=False)

    copied = []
    for src in (CONFIG_FILE, PRESETS_FILE, SCHEDULES_FILE, STATIONS_FILE):
        if src.exists():
            dest = target / src.name
            shutil.copy2(src, dest)
            copied.append(dest.name)

    if STATE_DB.exists():
        dest = target / STATE_DB.name
        backup_sqlite(STATE_DB, dest)
        copied.append(dest.name)

    (target / "manifest.json").write_text(
        json.dumps({
            "app_version": APP_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "source_config_dir": str(CONFIG_DIR),
            "files": copied,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    return target

def cmd_backup(args):
    target = create_backup(args.reason or "manual")
    print(f"Backup created: {target}")

def cmd_backup_list(args):
    ensure_config()
    dirs = sorted(
        [p for p in BACKUP_DIR.iterdir() if p.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )
    if not dirs:
        print("No Plex Curator backups.")
        return
    for path in dirs[:args.limit]:
        reason = ""
        manifest = path / "manifest.json"
        if manifest.exists():
            try:
                reason = json.loads(manifest.read_text(encoding="utf-8")).get("reason", "")
            except Exception:
                pass
        print(f"{path.name}\t{reason}")

def playlist_item_key(item):
    return str(getattr(item, "ratingKey", "") or getattr(item, "key", "") or getattr(item, "title", ""))

def describe_media_item(item):
    if getattr(item, "type", "") == "episode":
        return (
            f"{getattr(item,'grandparentTitle','')} "
            f"S{getattr(item,'parentIndex',0):02}E{getattr(item,'index',0):02} — "
            f"{getattr(item,'title','')}"
        )
    year = getattr(item, "year", None)
    return f"{getattr(item,'title','')}{f' ({year})' if year else ''}"

def replace_playlist_with_rollback(plex, title, items):
    existing = find_playlist(plex, title)
    old_items = []
    if existing:
        try:
            old_items = list(existing.items())
        except Exception:
            old_items = []
        existing.delete()

    try:
        playlist = plex.createPlaylist(title, items=items)
        print(f'\nCreated playlist "{playlist.title}" with {len(items)} items.')
        return playlist
    except Exception:
        if old_items:
            try:
                plex.createPlaylist(title, items=old_items)
                print(
                    f'Restored previous playlist "{title}" after refresh failure.',
                    file=sys.stderr,
                )
            except Exception as restore_exc:
                print(
                    f'WARNING: failed to restore previous playlist "{title}": {restore_exc}',
                    file=sys.stderr,
                )
        raise

# ---------------------------------------------------------------------------
# Setup / diagnostics
# ---------------------------------------------------------------------------

def cmd_setup(args):
    ensure_config()
    if CONFIG_FILE.exists() and not args.force:
        print(f"Permanent config already exists: {CONFIG_FILE}")
        return
    candidates = [
        APP_DIR / ".env",
        APP_DIR.parent / "plex-curator-v8" / ".env",
        APP_DIR.parent / "plex-curator-v7" / ".env",
        APP_DIR.parent / "plex-curator-v6" / ".env",
        APP_DIR.parent / "plex-playlist-agent-v2" / ".env",
    ]
    source = next((p for p in candidates if p.exists()), None)
    if source:
        shutil.copy2(source, CONFIG_FILE)
        os.chmod(CONFIG_FILE, 0o600)
        print(f"Copied existing Plex config to {CONFIG_FILE}")
    else:
        CONFIG_FILE.write_text("PLEX_URL=http://127.0.0.1:32400\nPLEX_TOKEN=\n", encoding="utf-8")
        os.chmod(CONFIG_FILE, 0o600)
        print(f"Created {CONFIG_FILE}")
        print("Add the Plex token once; future versions reuse this file.")

def cmd_config(_args):
    ensure_config()
    print(f"Config directory: {CONFIG_DIR}")
    print(f"Plex config:      {CONFIG_FILE}")
    print(f"State database:   {STATE_DB}")
    print(f"Movie presets:    {PRESETS_FILE}")
    print(f"Schedules:        {SCHEDULES_FILE}")
    print(f"Stations:         {STATIONS_FILE}")
    print(f"Exports:          {EXPORT_DIR}")
    print(f"Backups:          {BACKUP_DIR}")
    print(f"Logs:             {LOG_DIR}")
    print(f"App version:      {APP_VERSION}")

def cmd_test(_args):
    plex = connect()
    print(f"Connected: {plex.friendlyName}")
    print(f"Version:   {plex.version}")
    print(f"Config:    {CONFIG_FILE}")
    print(f"State DB:  {STATE_DB}")

def cmd_libraries(_args):
    plex = connect()
    for sec in plex.library.sections():
        print(f"{sec.title}\t{sec.type}")

def cmd_search(args):
    plex = connect()
    sec = get_section(plex, args.library)
    hits = sec.search(title=args.query)[:args.limit]
    for i, x in enumerate(hits, 1):
        print(f"{i:>3}. {item_label(x)}")

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_record(item, library):
    duration = getattr(item, "duration", None)
    return {
        "library": library,
        "type": getattr(item, "type", None),
        "title": getattr(item, "title", None),
        "year": getattr(item, "year", None),
        "summary": getattr(item, "summary", None),
        "content_rating": getattr(item, "contentRating", None),
        "audience_rating": getattr(item, "audienceRating", None),
        "critic_rating": getattr(item, "rating", None),
        "user_rating": getattr(item, "userRating", None),
        "studio": getattr(item, "studio", None),
        "runtime_minutes": round(duration / 60000, 1) if duration else None,
        "added_at": safe_date(getattr(item, "addedAt", None)),
        "last_viewed_at": safe_date(getattr(item, "lastViewedAt", None)),
        "view_count": getattr(item, "viewCount", None) or 0,
        "watched": is_watched(item),
        "genres": tags_join(getattr(item, "genres", [])),
        "collections": tags_join(getattr(item, "collections", [])),
        "directors": tags_join(getattr(item, "directors", [])),
        "actors": tags_join(getattr(item, "roles", [])),
        "rating_key": getattr(item, "ratingKey", None),
        "guid": getattr(item, "guid", None),
    }

def write_records(records, stem):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = EXPORT_DIR / f"{stem}-{stamp}.json"
    csv_path = EXPORT_DIR / f"{stem}-{stamp}.csv"
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = []
    seen = set()
    for r in records:
        for k in r:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(records)
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")

def cmd_export(args):
    plex = connect()
    sec = get_section(plex, args.library)
    records = []
    items = sec.all()
    for idx, item in enumerate(items, 1):
        try:
            item.reload()
        except Exception:
            pass
        records.append(export_record(item, args.library))
        if idx % 100 == 0 or idx == len(items):
            print(f"{idx}/{len(items)}")
    stem = "".join(ch.lower() if ch.isalnum() else "-" for ch in args.library).strip("-")
    write_records(records, stem)

    if sec.type == "show" and args.include_episodes:
        eps = []
        for show in items:
            for ep in show.episodes():
                r = export_record(ep, args.library)
                r.update({
                    "show_title": getattr(ep, "grandparentTitle", None),
                    "season_number": getattr(ep, "parentIndex", None),
                    "episode_number": getattr(ep, "index", None),
                })
                eps.append(r)
        write_records(eps, stem + "-episodes")

# ---------------------------------------------------------------------------
# Generic playlist file management
# ---------------------------------------------------------------------------

def cmd_create_file(args):
    plex = connect()
    sec = get_section(plex, args.library)
    path = Path(args.file).expanduser()
    specs = [x.strip() for x in path.read_text(encoding="utf-8").splitlines()
             if x.strip() and not x.lstrip().startswith("#")]
    selected, missing = [], []
    for spec in specs:
        title, year = parse_title_spec(spec)
        item = resolve_title(sec, title, year)
        if item:
            selected.append(item)
        else:
            missing.append(spec)
    if missing:
        print("Missing from Plex:")
        for x in missing:
            print(f"  - {x}")
    if not selected:
        raise SystemExit("No matching items.")
    if getattr(args, "dry_run", False):
        print(f'DRY RUN: would create/refresh "{args.name}" with {len(selected)} items.')
        return
    if args.replace:
        replace_playlist_with_rollback(plex, args.name, selected)
    else:
        create_playlist(plex, args.name, selected, False)

def cmd_playlists(_args):
    plex = connect()
    for p in sorted(plex.playlists(), key=lambda x: x.title.casefold()):
        print(f"{p.title}\t{getattr(p, 'leafCount', '?')} items")

def cmd_show_playlist(args):
    plex = connect()
    p = find_playlist(plex, args.name)
    if not p:
        raise SystemExit(f'Playlist "{args.name}" not found.')
    for i, x in enumerate(p.items(), 1):
        if getattr(x, "type", "") == "episode":
            print(f"{i:>3}. {getattr(x,'grandparentTitle','')} — S{getattr(x,'parentIndex',0):02}E{getattr(x,'index',0):02} — {x.title}")
        else:
            print(f"{i:>3}. {item_label(x)}")

def cmd_delete_playlist(args):
    plex = connect()
    p = find_playlist(plex, args.name)
    if not p:
        raise SystemExit(f'Playlist "{args.name}" not found.')
    if getattr(args, "dry_run", False):
        print(f'DRY RUN: would delete playlist "{args.name}". No media files would be deleted.')
        return
    if not args.yes:
        answer = input(f'Delete playlist "{args.name}"? Type YES: ')
        if answer != "YES":
            print("Cancelled.")
            return
    p.delete()
    print(f'Deleted playlist "{args.name}".')

# ---------------------------------------------------------------------------
# Movie curation
# ---------------------------------------------------------------------------

def load_movie_presets():
    ensure_config()
    return json.loads(PRESETS_FILE.read_text(encoding="utf-8"))

def movie_filter(items, opts):
    genre_any = [x.casefold() for x in opts.get("genre_any", [])]
    def ok(x):
        y = getattr(x, "year", None)
        if opts.get("year_min") and (not y or y < opts["year_min"]): return False
        if opts.get("year_max") and (not y or y > opts["year_max"]): return False
        gs = tags(getattr(x, "genres", []))
        if opts.get("genre") and opts["genre"].casefold() not in gs: return False
        if genre_any and not any(g in gs for g in genre_any): return False
        if opts.get("unwatched") and is_watched(x): return False
        if opts.get("watched") and not is_watched(x): return False
        if opts.get("max_runtime"):
            rt = runtime_minutes(x)
            if rt is None or rt > opts["max_runtime"]: return False
        if opts.get("content_ratings"):
            cr = (getattr(x, "contentRating", "") or "").casefold()
            if cr not in {r.casefold() for r in opts["content_ratings"]}: return False
        ar = numeric(x, "audienceRating")
        cr = numeric(x, "rating")
        if opts.get("min_audience") is not None and (ar is None or ar < opts["min_audience"]): return False
        if opts.get("min_critic") is not None and (cr is None or cr < opts["min_critic"]): return False
        return True
    selected = [x for x in items if ok(x)]
    if opts.get("random"):
        random.shuffle(selected)
    else:
        selected.sort(
            key=lambda x: (numeric(x, "audienceRating") or 0)
            + (numeric(x, "rating") or 0)
            + (2 if not is_watched(x) else 0),
            reverse=True,
        )
    if opts.get("limit"):
        selected = selected[:opts["limit"]]
    return selected

def cmd_presets(_args):
    print("Movie presets:")
    for n, c in load_movie_presets().items():
        print(f"  {n:22} {c.get('description','')}")
    print("\nChannel presets:")
    for n, c in CHANNEL_PRESETS.items():
        print(f"  {n:22} {c.get('description','')}")
    print("\nSchedules:")
    for n, c in load_schedules().items():
        print(f"  {n:22} {c.get('description','')}")
    print("\nStation profiles:")
    for sid, raw in load_stations().items():
        cfg = normalize_station(sid, raw)
        state = "enabled" if cfg["enabled"] else "disabled"
        print(f"  {sid:22} {state:8} {cfg.get('description','')}")

def cmd_curate(args):
    plex = connect()
    sec = get_section(plex, args.library)
    opts = {
        "genre": args.genre,
        "year_min": args.year_min,
        "year_max": args.year_max,
        "max_runtime": args.max_runtime,
        "content_ratings": args.content_rating or [],
        "min_audience": args.min_audience,
        "min_critic": args.min_critic,
        "watched": args.watched,
        "unwatched": args.unwatched,
        "random": args.random,
        "limit": args.limit,
    }
    chosen = movie_filter(sec.all(), opts)
    for i, x in enumerate(chosen, 1):
        print(f"{i:>3}. {item_label(x)}")
    if args.playlist and chosen:
        if getattr(args, "dry_run", False):
            print(f'\nDRY RUN: would create/refresh "{args.playlist}" with {len(chosen)} items.')
        elif args.replace:
            replace_playlist_with_rollback(plex, args.playlist, chosen)
        else:
            create_playlist(plex, args.playlist, chosen, False)

def cmd_preset(args):
    presets = load_movie_presets()
    if args.name not in presets:
        raise SystemExit(f'Unknown movie preset "{args.name}".')
    cfg = dict(presets[args.name])
    plex = connect()
    sec = get_section(plex, cfg.get("library", "Movies"))
    chosen = movie_filter(sec.all(), cfg)
    for i, x in enumerate(chosen, 1):
        print(f"{i:>3}. {item_label(x)}")
    playlist = args.playlist or cfg.get("playlist")
    if args.create or playlist:
        target = playlist or args.name.replace("-", " ").title()
        if getattr(args, "dry_run", False):
            print(f'\nDRY RUN: would create/refresh "{target}" with {len(chosen)} items.')
        elif args.replace:
            replace_playlist_with_rollback(plex, target, chosen)
        else:
            create_playlist(plex, target, chosen, False)

# ---------------------------------------------------------------------------
# Stateful cartoon channels
# ---------------------------------------------------------------------------

def show_is_animation(show):
    return "animation" in tags(getattr(show, "genres", []))

def kids_rating_ok(show):
    rating = (getattr(show, "contentRating", "") or "").upper()
    return rating not in {"TV-14", "TV-MA", "R", "NC-17"}

def eligible_cartoon_shows(section, cfg):
    result = []
    include = {x.casefold() for x in cfg.get("include_shows", [])}
    exclude = {x.casefold() for x in cfg.get("exclude_shows", [])}
    genres_any = {x.casefold() for x in cfg.get("genres_any", [])}

    for show in section.all():
        if not show_is_animation(show):
            continue

        title_cf = show.title.casefold()
        if include and title_cf not in include:
            continue
        if title_cf in exclude:
            continue

        y = getattr(show, "year", None)
        if cfg.get("year_min") and (not y or y < cfg["year_min"]):
            continue
        if cfg.get("year_max") and (not y or y > cfg["year_max"]):
            continue
        if cfg.get("kids_only", True) and not kids_rating_ok(show):
            continue
        if genres_any and not (genres_any & tags(getattr(show, "genres", []))):
            continue

        result.append(show)
    return result

def get_recent_keys(channel_name, limit):
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        SELECT rating_key FROM episode_play_history
        WHERE channel_name = ?
        ORDER BY id DESC LIMIT ?
    """, (channel_name, limit))
    rows = {r[0] for r in cur.fetchall()}
    con.close()
    return rows

def get_cursor(channel_name, show):
    key = str(getattr(show, "ratingKey", show.title))
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        SELECT next_episode_index, updated_at
        FROM channel_show_cursor
        WHERE channel_name=? AND show_rating_key=?
    """, (channel_name, key))
    row = cur.fetchone()
    con.close()
    if not row:
        return 0, None
    return row[0], parse_dt(row[1])

def set_cursor(channel_name, show, idx):
    key = str(getattr(show, "ratingKey", show.title))
    now = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO channel_show_cursor(
            channel_name, show_rating_key, show_title,
            next_episode_index, updated_at
        )
        VALUES(?,?,?,?,?)
        ON CONFLICT(channel_name, show_rating_key) DO UPDATE SET
            show_title=excluded.show_title,
            next_episode_index=excluded.next_episode_index,
            updated_at=excluded.updated_at
    """, (channel_name, key, show.title, idx, now))
    con.commit()
    con.close()

def remember_episode(ep, channel_name):
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO episode_play_history(
            rating_key, show_title, season_number, episode_number,
            episode_title, selected_at, channel_name
        ) VALUES(?,?,?,?,?,?,?)
    """, (
        str(getattr(ep, "ratingKey", "")),
        getattr(ep, "grandparentTitle", ""),
        getattr(ep, "parentIndex", 0),
        getattr(ep, "index", 0),
        getattr(ep, "title", ""),
        datetime.now(timezone.utc).isoformat(),
        channel_name,
    ))
    con.commit()
    con.close()

def remember_build(channel_name, playlist_name, count):
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO build_history(channel_name, playlist_name, built_at, item_count)
        VALUES(?,?,?,?)
    """, (channel_name, playlist_name, datetime.now(timezone.utc).isoformat(), count))
    con.commit()
    con.close()

def ordered_episodes(show, unwatched=False):
    eps = show.episodes()
    eps.sort(key=lambda e: (getattr(e, "parentIndex", 0) or 0, getattr(e, "index", 0) or 0))
    if unwatched:
        eps = [e for e in eps if not is_watched(e)]
    return eps

def plex_watch_next_index(episodes):
    watched = []
    for idx, ep in enumerate(episodes):
        if is_watched(ep):
            last = parse_dt(getattr(ep, "lastViewedAt", None))
            watched.append((idx, last))
    if not watched:
        return None, None
    with_dates = [(idx, dt) for idx, dt in watched if dt is not None]
    if with_dates:
        idx, latest = max(with_dates, key=lambda x: x[1])
    else:
        idx = max(i for i, _ in watched)
        latest = None
    return (idx + 1) % len(episodes), latest

def choose_start_index(channel_name, show, episodes, sync_watch_progress=True):
    cursor_idx, cursor_updated = get_cursor(channel_name, show)
    if not sync_watch_progress or not episodes:
        return cursor_idx % max(len(episodes), 1), "curator"
    watch_idx, watch_updated = plex_watch_next_index(episodes)
    if watch_idx is None:
        return cursor_idx % len(episodes), "curator"
    if cursor_updated is None:
        return watch_idx, "plex"
    if watch_updated is not None and watch_updated > cursor_updated:
        return watch_idx, "plex"
    return cursor_idx % len(episodes), "curator"

def seasonal_mode(requested):
    if requested != "auto":
        return requested
    month = datetime.now().month
    if month == 10:
        return "halloween"
    if month == 12:
        return "christmas"
    return "none"

def ep_keyword_match(ep, keywords):
    hay = " ".join([
        getattr(ep, "title", "") or "",
        getattr(ep, "summary", "") or "",
    ]).casefold()
    return any(k.casefold() in hay for k in keywords)

def collect_seasonal_specials(shows, mode, recent_keys):
    if mode in ("none", None):
        return []
    keywords = SEASONAL_KEYWORDS.get(mode, [])
    specials = []
    for show in shows:
        for ep in show.episodes():
            key = str(getattr(ep, "ratingKey", ""))
            if key in recent_keys:
                continue
            if ep_keyword_match(ep, keywords):
                specials.append(ep)
    random.shuffle(specials)
    return specials

def choose_episode_queue(channel_name, show, count, recent_keys, unwatched, sync_watch_progress):
    eps = ordered_episodes(show, unwatched=unwatched)
    if not eps:
        return [], "none"
    start, source = choose_start_index(channel_name, show, eps, sync_watch_progress)
    chosen = []
    chosen_keys = set()
    idx = start
    scanned = 0
    while len(chosen) < count and scanned < len(eps) * 2:
        ep = eps[idx % len(eps)]
        key = str(getattr(ep, "ratingKey", ""))
        idx = (idx + 1) % len(eps)
        if key not in recent_keys and key not in chosen_keys:
            chosen.append((ep, idx))
            chosen_keys.add(key)
        scanned += 1
    if len(chosen) < count:
        idx = start
        scanned = 0
        while len(chosen) < count and scanned < len(eps):
            ep = eps[idx % len(eps)]
            key = str(getattr(ep, "ratingKey", ""))
            idx = (idx + 1) % len(eps)
            if key not in chosen_keys:
                chosen.append((ep, idx))
                chosen_keys.add(key)
            scanned += 1
    return chosen, source

def interleave_show_queues(queues, total, min_show_gap):
    result = []
    cursor_steps = {}
    recent_shows = deque(maxlen=max(0, min_show_gap))
    queues = list(queues)

    while queues and len(result) < total:
        picked_index = None
        for i, (show, q, source) in enumerate(queues):
            if q and show.title not in recent_shows:
                picked_index = i
                break
        if picked_index is None:
            for i, (_show, q, _source) in enumerate(queues):
                if q:
                    picked_index = i
                    break
        if picked_index is None:
            break

        show, q, source = queues.pop(picked_index)
        ep, next_idx = q.popleft()
        result.append(ep)
        recent_shows.append(show.title)
        cursor_steps[str(getattr(ep, "ratingKey", ""))] = (show, next_idx)
        if q:
            queues.append((show, q, source))

    return result, cursor_steps

def cursor_updates_for_items(channel_name, items, cursor_steps):
    updates = {}
    for ep in items:
        step = cursor_steps.get(str(getattr(ep, "ratingKey", "")))
        if not step:
            continue
        show, next_idx = step
        show_key = str(getattr(show, "ratingKey", show.title))
        updates[show_key] = (channel_name, show, next_idx)
    return updates

def apply_cursor_updates(cursor_updates):
    for _key, (channel_name, show, next_idx) in cursor_updates.items():
        set_cursor(channel_name, show, next_idx)

def inject_specials(items, specials, every, min_show_gap):
    if not specials or every <= 0:
        return items
    out = []
    special_idx = 0
    for idx, item in enumerate(items, 1):
        out.append(item)
        if idx % every == 0 and special_idx < len(specials):
            candidate = specials[special_idx]
            special_idx += 1
            # Avoid immediately duplicating the same series if possible.
            if out and getattr(candidate, "grandparentTitle", "") == getattr(out[-1], "grandparentTitle", ""):
                continue
            out.append(candidate)
    return out

def build_channel(plex, preset_name, channel_name, per_show, total, unwatched, avoid_recent,
                  sync_watch_progress, min_show_gap, seasonal, special_every, adult=False,
                  profile_overrides=None):
    if preset_name not in CHANNEL_PRESETS:
        raise SystemExit(f"Unknown channel preset: {preset_name}")
    cfg = dict(CHANNEL_PRESETS[preset_name])
    if profile_overrides:
        for key in (
            "year_min", "year_max", "kids_only", "include_shows",
            "exclude_shows", "genres_any"
        ):
            if key in profile_overrides and profile_overrides[key] is not None:
                cfg[key] = profile_overrides[key]
    if adult:
        cfg["kids_only"] = False

    sec = get_section(plex, "TV Shows")
    shows = eligible_cartoon_shows(sec, cfg)
    random.shuffle(shows)
    recent = get_recent_keys(channel_name, avoid_recent)
    queues = []
    for show in shows:
        chosen, source = choose_episode_queue(
            channel_name, show, per_show, recent, unwatched, sync_watch_progress
        )
        if chosen:
            queues.append((show, deque(chosen), source))
    base_items, cursor_steps = interleave_show_queues(queues, total, min_show_gap)
    mode = seasonal_mode(seasonal)
    base_keys = {str(getattr(ep, "ratingKey", "")) for ep in base_items}
    specials = collect_seasonal_specials(shows, mode, recent | base_keys)
    items = inject_specials(base_items, specials, special_every, min_show_gap)[:total]
    cursor_updates = cursor_updates_for_items(channel_name, items, cursor_steps)
    return items, shows, mode, cursor_updates

def cmd_channel(args):
    plex = connect()
    cfg = CHANNEL_PRESETS[args.preset]
    items, shows, mode, cursor_updates = build_channel(
        plex=plex,
        preset_name=args.preset,
        channel_name=args.preset,
        per_show=args.per_show,
        total=args.total,
        unwatched=args.unwatched,
        avoid_recent=args.avoid_recent,
        sync_watch_progress=not args.ignore_watch_progress,
        min_show_gap=args.min_show_gap,
        seasonal=args.seasonal,
        special_every=args.special_every,
        adult=args.adult,
    )
    print(f"Shows in pool: {len(shows)}")
    print(f"Seasonal mode: {mode}")
    for i, ep in enumerate(items, 1):
        print(f"{i:>3}. {getattr(ep,'grandparentTitle','')} — "
              f"S{getattr(ep,'parentIndex',0):02}E{getattr(ep,'index',0):02} — {ep.title}")
    playlist = args.playlist or cfg.get("playlist")
    if args.create and items:
        if getattr(args, "dry_run", False):
            print("\nDRY RUN: Plex playlist and state were not changed.")
        else:
            if args.replace:
                replace_playlist_with_rollback(plex, playlist, items)
            else:
                create_playlist(plex, playlist, items, False)
            apply_cursor_updates(cursor_updates)
            for ep in items:
                remember_episode(ep, args.preset)
            remember_build(args.preset, playlist, len(items))

# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

def load_schedules():
    ensure_config()
    return json.loads(SCHEDULES_FILE.read_text(encoding="utf-8"))

def cmd_schedule_list(_args):
    for n, c in load_schedules().items():
        print(f"{n:22} {c.get('description','')}")

def cmd_schedule_show(args):
    s = load_schedules()
    if args.name not in s:
        raise SystemExit(f"Unknown schedule: {args.name}")
    print(json.dumps(s[args.name], indent=2))

def choose_movie_block(plex, preset_name, minutes):
    presets = load_movie_presets()
    if preset_name not in presets:
        return []
    cfg = dict(presets[preset_name])
    cfg["limit"] = 30
    sec = get_section(plex, cfg.get("library", "Movies"))
    candidates = movie_filter(sec.all(), cfg)
    fitting = [m for m in candidates if (runtime_minutes(m) or 9999) <= minutes]
    pool = fitting or candidates
    if not pool:
        return []
    random.shuffle(pool)
    return [pool[0]]

def cmd_schedule_build(args):
    schedules = load_schedules()
    if args.name not in schedules:
        raise SystemExit(f"Unknown schedule: {args.name}")
    cfg = schedules[args.name]
    plex = connect()
    items = []
    pending_cursor_updates = {}
    print(f"{args.name}: {cfg.get('description','')}\n")

    for block in cfg.get("blocks", []):
        bname = block.get("name", "Block")
        btype = block.get("type")
        minutes = int(block.get("minutes", 60))
        print(f"[{bname}] {minutes} min")
        if btype == "cartoons":
            estimated = max(1, round(minutes / 22))
            picked, _shows, _mode, block_cursor_updates = build_channel(
                plex=plex,
                preset_name=block.get("preset", "all-cartoons"),
                channel_name=f"schedule:{args.name}:{bname}",
                per_show=max(2, min(8, estimated)),
                total=estimated,
                unwatched=args.unwatched,
                avoid_recent=args.avoid_recent,
                sync_watch_progress=not args.ignore_watch_progress,
                min_show_gap=args.min_show_gap,
                seasonal=block.get("seasonal", args.seasonal),
                special_every=args.special_every,
                adult=False,
            )
            pending_cursor_updates.update(block_cursor_updates)
        elif btype == "movie":
            picked = choose_movie_block(plex, block.get("preset", "friday-movie-night"), minutes)
        else:
            picked = []
        for x in picked:
            if getattr(x, "type", "") == "episode":
                print(f"  {getattr(x,'grandparentTitle','')} — {x.title}")
            else:
                print(f"  {x.title}")
        items.extend(picked)

    playlist = args.playlist or cfg.get("playlist") or args.name.replace("-", " ").title()
    if args.create and items:
        if getattr(args, "dry_run", False):
            print("\nDRY RUN: Plex playlist and state were not changed.")
        else:
            if args.replace:
                replace_playlist_with_rollback(plex, playlist, items)
            else:
                create_playlist(plex, playlist, items, False)
            apply_cursor_updates(pending_cursor_updates)
            for x in items:
                if getattr(x, "type", "") == "episode":
                    remember_episode(x, f"schedule:{args.name}")
            remember_build(f"schedule:{args.name}", playlist, len(items))

# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------

def parse_wishlist(path):
    out = []
    for line in Path(path).expanduser().read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        title, year = line, None
        if "|" in line:
            title, ys = line.rsplit("|", 1)
            try: year = int(ys.strip())
            except ValueError: title, year = line, None
        elif line.endswith(")") and "(" in line:
            left, right = line.rsplit("(", 1)
            try:
                year = int(right.rstrip(") ").strip())
                title = left.strip()
            except ValueError:
                pass
        out.append((title.strip(), year))
    return out

def cmd_wishlist_check(args):
    plex = connect()
    sec = get_section(plex, args.library)
    found, missing = [], []
    for title, year in parse_wishlist(args.file):
        item = resolve_title(sec, title, year)
        (found if item else missing).append((title, year))
    print("Now in Plex:")
    if not found: print("  none")
    for t, y in found:
        print(f"  + {t}{f' ({y})' if y else ''}")
    print("\nStill missing:")
    if not missing: print("  none")
    for t, y in missing:
        print(f"  - {t}{f' ({y})' if y else ''}")
    if args.output_missing:
        Path(args.output_missing).write_text(
            "\n".join(f"{t} ({y})" if y else t for t, y in missing) + ("\n" if missing else ""),
            encoding="utf-8",
        )
        print(f"\nWrote: {args.output_missing}")

# ---------------------------------------------------------------------------
# Progress / history / state
# ---------------------------------------------------------------------------

def cmd_progress(args):
    plex = connect()
    sec = get_section(plex, "TV Shows")
    cfg = dict(CHANNEL_PRESETS.get(args.preset, CHANNEL_PRESETS["all-cartoons"]))
    shows = eligible_cartoon_shows(sec, cfg)
    for show in sorted(shows, key=lambda s: s.title.casefold()):
        eps = ordered_episodes(show, unwatched=False)
        cursor_idx, cursor_updated = get_cursor(show)
        watch_idx, watch_updated = plex_watch_next_index(eps) if eps else (None, None)
        next_cur = eps[cursor_idx % len(eps)] if eps else None
        next_watch = eps[watch_idx % len(eps)] if eps and watch_idx is not None else None
        print(show.title)
        print(f"  curator next: {getattr(next_cur,'title','n/a')} (index {cursor_idx})")
        print(f"  Plex next:    {getattr(next_watch,'title','n/a')} (index {watch_idx})")
        print(f"  Plex watched: {sum(1 for e in eps if is_watched(e))}/{len(eps)}")
        if watch_updated:
            print(f"  last watched: {watch_updated.isoformat()}")

def cmd_history(args):
    ensure_config()
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    if args.channel:
        cur.execute("""
            SELECT selected_at, show_title, season_number, episode_number, episode_title, channel_name
            FROM episode_play_history
            WHERE channel_name LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (f"%{args.channel}%", args.limit))
    else:
        cur.execute("""
            SELECT selected_at, show_title, season_number, episode_number, episode_title, channel_name
            FROM episode_play_history
            ORDER BY id DESC LIMIT ?
        """, (args.limit,))
    rows = cur.fetchall()
    con.close()
    for ts, show, s, e, title, channel in rows:
        print(f"{ts} [{channel}] {show} S{s:02}E{e:02} — {title}")

def cmd_build_history(args):
    ensure_config()
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute("""
        SELECT built_at, channel_name, playlist_name, item_count
        FROM build_history ORDER BY id DESC LIMIT ?
    """, (args.limit,))
    rows = cur.fetchall()
    con.close()
    for built, channel, playlist, count in rows:
        print(f"{built} {channel} -> {playlist} ({count} items)")

def cmd_state_info(_args):
    ensure_config()
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    print(f"State DB: {STATE_DB}")
    for table in ("episode_play_history", "show_cursor", "channel_show_cursor", "build_history"):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table:22} {cur.fetchone()[0]}")
    con.close()

def cmd_state_reset(args):
    ensure_config()
    if not args.yes:
        raise SystemExit("Refusing to reset state without --yes")
    backup = create_backup("before-state-reset")
    print(f"Safety backup: {backup}")
    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    if args.channel:
        pattern = f"%{args.channel}%"
        cur.execute("DELETE FROM episode_play_history WHERE channel_name LIKE ?", (pattern,))
        cur.execute("DELETE FROM channel_show_cursor WHERE channel_name LIKE ?", (pattern,))
        cur.execute("DELETE FROM build_history WHERE channel_name LIKE ?", (pattern,))
        print(f"Cleared history and cursor state for: {args.channel}")
    else:
        cur.execute("DELETE FROM episode_play_history")
        cur.execute("DELETE FROM show_cursor")
        cur.execute("DELETE FROM channel_show_cursor")
        cur.execute("DELETE FROM build_history")
        print("Cleared all Plex Curator state.")
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# Station Profiles (v10)
# ---------------------------------------------------------------------------

STATION_UPDATE_FIELDS = {
    "name": str,
    "description": str,
    "playlist": str,
    "preset": str,
    "year_min": int,
    "year_max": int,
    "per_show": int,
    "total": int,
    "avoid_recent": int,
    "min_show_gap": int,
    "seasonal": str,
    "special_every": int,
}

def load_stations():
    ensure_config()
    try:
        data = json.loads(STATIONS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Could not read stations file {STATIONS_FILE}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"Stations file must contain a JSON object: {STATIONS_FILE}")
    return data

def save_stations(stations):
    ensure_config()
    temp = STATIONS_FILE.with_suffix(".json.tmp")
    temp.write_text(json.dumps(stations, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(STATIONS_FILE)

def validate_station_id(value):
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if not value or any(ch not in allowed for ch in value):
        raise SystemExit("Station ID may contain only lowercase letters, numbers, '-' and '_'.")
    return value

def normalize_station(station_id, cfg):
    out = {
        "name": cfg.get("name") or station_id.replace("-", " ").title(),
        "description": cfg.get("description", ""),
        "enabled": bool(cfg.get("enabled", True)),
        "playlist": cfg.get("playlist") or cfg.get("name") or station_id.replace("-", " ").title(),
        "preset": cfg.get("preset", "all-cartoons"),
        "year_min": cfg.get("year_min"),
        "year_max": cfg.get("year_max"),
        "kids_only": bool(cfg.get("kids_only", True)),
        "adult": bool(cfg.get("adult", False)),
        "per_show": int(cfg.get("per_show", 5)),
        "total": int(cfg.get("total", 40)),
        "avoid_recent": int(cfg.get("avoid_recent", 120)),
        "min_show_gap": int(cfg.get("min_show_gap", 2)),
        "seasonal": cfg.get("seasonal", "auto"),
        "special_every": int(cfg.get("special_every", 8)),
        "unwatched": bool(cfg.get("unwatched", False)),
        "sync_watch_progress": bool(cfg.get("sync_watch_progress", True)),
        "include_shows": list(cfg.get("include_shows", [])),
        "exclude_shows": list(cfg.get("exclude_shows", [])),
        "genres_any": list(cfg.get("genres_any", [])),
    }
    if out["preset"] not in CHANNEL_PRESETS:
        raise SystemExit(f'Station "{station_id}" has unknown preset "{out["preset"]}".')
    if out["seasonal"] not in {"auto", "none", "halloween", "christmas"}:
        raise SystemExit(f'Station "{station_id}" has invalid seasonal setting.')
    if out["year_min"] is not None and out["year_max"] is not None and out["year_min"] > out["year_max"]:
        raise SystemExit(f'Station "{station_id}" has year_min greater than year_max.')
    if out["per_show"] < 1 or out["total"] < 1:
        raise SystemExit(f'Station "{station_id}" requires positive per_show and total values.')
    return out

def cmd_station_list(_args):
    stations = load_stations()
    if not stations:
        print("No stations configured.")
        return
    for sid in sorted(stations):
        cfg = normalize_station(sid, stations[sid])
        state = "enabled" if cfg["enabled"] else "disabled"
        years = ""
        if cfg["year_min"] or cfg["year_max"]:
            years = f' [{cfg["year_min"] or "…"}-{cfg["year_max"] or "…"}]'
        print(f'{sid:22} {state:8} {cfg["name"]}{years} -> {cfg["playlist"]}')

def cmd_station_show(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    cfg = normalize_station(args.station_id, stations[args.station_id])
    print(json.dumps(cfg, indent=2, ensure_ascii=False))

def station_build_items(plex, station_id, cfg, total_override=None):
    total = total_override if total_override is not None else cfg["total"]
    return build_channel(
        plex=plex,
        preset_name=cfg["preset"],
        channel_name=f"station:{station_id}",
        per_show=cfg["per_show"],
        total=total,
        unwatched=cfg["unwatched"],
        avoid_recent=cfg["avoid_recent"],
        sync_watch_progress=cfg["sync_watch_progress"],
        min_show_gap=cfg["min_show_gap"],
        seasonal=cfg["seasonal"],
        special_every=cfg["special_every"],
        adult=cfg["adult"],
        profile_overrides=cfg,
    )

def print_station_lineup(station_id, cfg, items, shows, mode):
    print(f'{cfg["name"]} [{station_id}]')
    print(f'Playlist: {cfg["playlist"]}')
    print(f'Preset:   {cfg["preset"]}')
    print(f'Shows:    {len(shows)}')
    print(f'Seasonal: {mode}')
    print()
    for i, ep in enumerate(items, 1):
        print(
            f"{i:>3}. {getattr(ep,'grandparentTitle','')} — "
            f"S{getattr(ep,'parentIndex',0):02}E{getattr(ep,'index',0):02} — {ep.title}"
        )

def cmd_station_preview(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    cfg = normalize_station(args.station_id, stations[args.station_id])
    plex = connect()
    items, shows, mode, _cursor_updates = station_build_items(plex, args.station_id, cfg, args.total)
    print_station_lineup(args.station_id, cfg, items, shows, mode)

def cmd_station_refresh(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    cfg = normalize_station(args.station_id, stations[args.station_id])
    if not cfg["enabled"] and not args.force:
        raise SystemExit(
            f'Station "{args.station_id}" is disabled. Use station-enable or --force.'
        )
    plex = connect()
    items, shows, mode, cursor_updates = station_build_items(plex, args.station_id, cfg, args.total)
    print_station_lineup(args.station_id, cfg, items, shows, mode)
    if not items:
        raise SystemExit("No station items were selected.")
    if getattr(args, "dry_run", False):
        print_station_diff(plex, args.station_id, cfg, items, as_json=False)
        print("\nDRY RUN: Plex playlist and station state were not changed.")
        return
    replace_playlist_with_rollback(plex, cfg["playlist"], items)
    apply_cursor_updates(cursor_updates)
    for ep in items:
        remember_episode(ep, f"station:{args.station_id}")
    remember_build(f"station:{args.station_id}", cfg["playlist"], len(items))

def cmd_station_refresh_all(args):
    stations = load_stations()
    selected = []
    for sid in sorted(stations):
        cfg = normalize_station(sid, stations[sid])
        if cfg["enabled"] or args.include_disabled:
            selected.append((sid, cfg))
    if not selected:
        print("No enabled stations.")
        return

    plex = connect()
    failures = []
    for sid, cfg in selected:
        print(f"\\n=== {cfg['name']} ({sid}) ===")
        try:
            items, shows, mode, cursor_updates = station_build_items(plex, sid, cfg)
            print_station_lineup(sid, cfg, items, shows, mode)
            if items:
                if getattr(args, "dry_run", False):
                    print_station_diff(plex, sid, cfg, items, as_json=False)
                    print("DRY RUN: no changes made.")
                else:
                    replace_playlist_with_rollback(plex, cfg["playlist"], items)
                    apply_cursor_updates(cursor_updates)
                    for ep in items:
                        remember_episode(ep, f"station:{sid}")
                    remember_build(f"station:{sid}", cfg["playlist"], len(items))
            else:
                failures.append((sid, "no items selected"))
        except Exception as exc:
            failures.append((sid, str(exc)))

    if failures:
        print("\\nStations with errors:")
        for sid, err in failures:
            print(f"  - {sid}: {err}")

def cmd_station_create(args):
    sid = validate_station_id(args.station_id)
    stations = load_stations()
    if sid in stations and not args.replace:
        raise SystemExit(f'Station "{sid}" already exists. Use --replace to overwrite its profile.')

    cfg = {
        "name": args.name or sid.replace("-", " ").title(),
        "description": args.description or "",
        "enabled": not args.disabled,
        "playlist": args.playlist or args.name or sid.replace("-", " ").title(),
        "preset": args.preset,
        "year_min": args.year_min,
        "year_max": args.year_max,
        "kids_only": not args.adult,
        "adult": args.adult,
        "per_show": args.per_show,
        "total": args.total,
        "avoid_recent": args.avoid_recent,
        "min_show_gap": args.min_show_gap,
        "seasonal": args.seasonal,
        "special_every": args.special_every,
        "unwatched": args.unwatched,
        "sync_watch_progress": not args.ignore_watch_progress,
        "include_shows": args.include_show or [],
        "exclude_shows": args.exclude_show or [],
        "genres_any": args.genre or [],
    }
    cfg = normalize_station(sid, cfg)
    stations[sid] = cfg
    save_stations(stations)
    print(f'Created station "{sid}".')
    cmd_station_show(argparse.Namespace(station_id=sid))

def cmd_station_update(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    cfg = normalize_station(args.station_id, stations[args.station_id])

    updates = {
        "name": args.name,
        "description": args.description,
        "playlist": args.playlist,
        "preset": args.preset,
        "year_min": args.year_min,
        "year_max": args.year_max,
        "per_show": args.per_show,
        "total": args.total,
        "avoid_recent": args.avoid_recent,
        "min_show_gap": args.min_show_gap,
        "seasonal": args.seasonal,
        "special_every": args.special_every,
    }
    for key, val in updates.items():
        if val is not None:
            cfg[key] = val

    if args.adult is True:
        cfg["adult"] = True
        cfg["kids_only"] = False
    if args.kids_only is True:
        cfg["adult"] = False
        cfg["kids_only"] = True
    if args.unwatched is True:
        cfg["unwatched"] = True
    if args.allow_watched is True:
        cfg["unwatched"] = False
    if args.ignore_watch_progress is True:
        cfg["sync_watch_progress"] = False
    if args.follow_watch_progress is True:
        cfg["sync_watch_progress"] = True

    if args.include_show is not None:
        cfg["include_shows"] = args.include_show
    if args.exclude_show is not None:
        cfg["exclude_shows"] = args.exclude_show
    if args.genre is not None:
        cfg["genres_any"] = args.genre

    cfg = normalize_station(args.station_id, cfg)
    stations[args.station_id] = cfg
    save_stations(stations)
    print(f'Updated station "{args.station_id}".')
    cmd_station_show(argparse.Namespace(station_id=args.station_id))

def cmd_station_clone(args):
    new_id = validate_station_id(args.new_station_id)
    stations = load_stations()
    if args.source_station_id not in stations:
        raise SystemExit(f'Unknown source station "{args.source_station_id}".')
    if new_id in stations and not args.replace:
        raise SystemExit(f'Station "{new_id}" already exists.')
    cfg = normalize_station(args.source_station_id, stations[args.source_station_id])
    cfg = dict(cfg)
    cfg["name"] = args.name or new_id.replace("-", " ").title()
    cfg["playlist"] = args.playlist or cfg["name"]
    cfg["enabled"] = not args.disabled
    stations[new_id] = normalize_station(new_id, cfg)
    save_stations(stations)
    print(f'Cloned "{args.source_station_id}" -> "{new_id}".')

def cmd_station_enable(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    stations[args.station_id]["enabled"] = True
    save_stations(stations)
    print(f'Enabled station "{args.station_id}".')

def cmd_station_disable(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    stations[args.station_id]["enabled"] = False
    save_stations(stations)
    print(f'Disabled station "{args.station_id}".')

def cmd_station_delete(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    if not args.yes:
        raise SystemExit("Refusing to delete a station profile without --yes.")
    backup = create_backup("before-station-delete")
    print(f"Safety backup: {backup}")
    del stations[args.station_id]
    save_stations(stations)
    print(f'Deleted station profile "{args.station_id}".')
    print("The Plex playlist and station history were left untouched.")

def cmd_station_history(args):
    args.channel = f"station:{args.station_id}"
    cmd_history(args)




def calculate_playlist_diff(current_items, proposed_items):
    current_keys = [playlist_item_key(x) for x in current_items]
    proposed_keys = [playlist_item_key(x) for x in proposed_items]
    current_counts = Counter(current_keys)
    proposed_counts = Counter(proposed_keys)

    added_keys = list((proposed_counts - current_counts).elements())
    removed_keys = list((current_counts - proposed_counts).elements())
    keep_count = sum((current_counts & proposed_counts).values())

    current_map = {}
    proposed_map = {}
    for item in current_items:
        current_map.setdefault(playlist_item_key(item), item)
    for item in proposed_items:
        proposed_map.setdefault(playlist_item_key(item), item)

    current_pos = {key: i for i, key in enumerate(current_keys)}
    proposed_pos = {key: i for i, key in enumerate(proposed_keys)}
    moved = [
        key for key in set(current_pos) & set(proposed_pos)
        if current_pos[key] != proposed_pos[key]
    ]

    return {
        "current_count": len(current_items),
        "proposed_count": len(proposed_items),
        "keep_count": keep_count,
        "add_count": len(added_keys),
        "remove_count": len(removed_keys),
        "moved_count": len(moved),
        "added": [describe_media_item(proposed_map[k]) for k in added_keys if k in proposed_map],
        "removed": [describe_media_item(current_map[k]) for k in removed_keys if k in current_map],
    }

def print_station_diff(plex, station_id, cfg, proposed_items, as_json=False):
    existing = find_playlist(plex, cfg["playlist"])
    current_items = list(existing.items()) if existing else []
    diff = calculate_playlist_diff(current_items, proposed_items)
    payload = {
        "station_id": station_id,
        "station_name": cfg["name"],
        "playlist": cfg["playlist"],
        **diff,
    }

    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return payload

    print()
    print(f'Station Diff: {cfg["name"]} [{station_id}]')
    print(f'Playlist: {cfg["playlist"]}')
    print()
    print(f'Current Plex playlist: {diff["current_count"]}')
    print(f'Proposed lineup:       {diff["proposed_count"]}')
    print()
    print(f'KEEP    {diff["keep_count"]}')
    print(f'ADD     {diff["add_count"]}')
    print(f'REMOVE  {diff["remove_count"]}')
    print(f'MOVED   {diff["moved_count"]}')

    if diff["added"]:
        print("\\nAdding:")
        for title in diff["added"]:
            print(f"  + {title}")
    if diff["removed"]:
        print("\\nRemoving:")
        for title in diff["removed"]:
            print(f"  - {title}")

    print("\\nNo changes have been made.")
    return payload

def cmd_station_diff(args):
    stations = load_stations()
    if args.station_id not in stations:
        raise SystemExit(f'Unknown station "{args.station_id}".')
    cfg = normalize_station(args.station_id, stations[args.station_id])
    plex = connect()
    proposed, _shows, _mode, _cursor_updates = station_build_items(
        plex, args.station_id, cfg, args.total
    )
    print_station_diff(plex, args.station_id, cfg, proposed, as_json=args.json)


# ---------------------------------------------------------------------------
# Logs (v11)
# ---------------------------------------------------------------------------

def tail_lines(path, count):
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.readlines()[-count:]
    except FileNotFoundError:
        return []

def cmd_logs(args):
    if not LOG_DIR.exists():
        raise SystemExit(f"Log directory not found: {LOG_DIR}")

    suffix = "err.log" if args.errors else "out.log"
    if args.job:
        paths = [LOG_DIR / f"{args.job}.{suffix}"]
    else:
        paths = sorted(
            LOG_DIR.glob(f"*.{suffix}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    if not paths:
        print("No matching logs.")
        return

    if args.follow:
        if len(paths) != 1:
            raise SystemExit("--follow requires a specific JOB.")
        import subprocess
        subprocess.run(["tail", "-f", str(paths[0])])
        return

    for path in paths:
        print(f"===== {path.name} =====")
        lines = tail_lines(path, args.lines)
        if lines:
            print("".join(lines), end="" if lines[-1].endswith("\\n") else "\\n")
        else:
            print("(empty or not found)")

# ---------------------------------------------------------------------------
# Doctor / reliability checks (v11)
# ---------------------------------------------------------------------------

def doctor_result(status, label, detail=""):
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")

def json_file_check(path, expected_type=dict):
    if not path.exists():
        return ("FAIL", f"missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ("FAIL", f"invalid JSON: {exc}")
    if not isinstance(data, expected_type):
        return ("FAIL", f"expected {expected_type.__name__}, got {type(data).__name__}")
    return ("PASS", f"{len(data)} entries")


def repair_trailing_json_junk(path, expected_type=dict):
    """Repair a valid JSON document followed only by known harmless trailing junk.

    This intentionally refuses to discard a second JSON object or arbitrary content.
    It is primarily a migration repair for older Plex Curator builds that could append
    a literal backslash-n after stations.json.
    """
    if not path.exists():
        return (False, "file does not exist")

    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pass
    else:
        if isinstance(data, expected_type):
            return (False, "already valid")
        return (False, f"expected {expected_type.__name__}, got {type(data).__name__}")

    stripped = raw.lstrip()
    decoder = json.JSONDecoder()
    try:
        data, end = decoder.raw_decode(stripped)
    except json.JSONDecodeError as exc:
        return (False, f"could not recover first JSON document: {exc}")

    if not isinstance(data, expected_type):
        return (False, f"expected {expected_type.__name__}, got {type(data).__name__}")

    trailing = stripped[end:].strip()
    if trailing not in {"\\n", "\\r\\n"}:
        return (False, f"refusing to discard unexpected trailing data: {trailing[:80]!r}")

    backup = path.with_name(path.name + ".pre-repair")
    shutil.copy2(path, backup)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return (True, f"removed legacy trailing data; backup: {backup}")

def sqlite_integrity_check(path):
    if not path.exists():
        return ("WARN", "state database does not exist yet")
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()[0]
        con.close()
        return ("PASS", "integrity_check=ok") if result == "ok" else ("FAIL", str(result))
    except Exception as exc:
        return ("FAIL", str(exc))

def cmd_doctor(args):
    import subprocess

    failures = 0
    warnings = 0
    results = []

    def report(status, label, detail=""):
        nonlocal failures, warnings
        results.append({"status": status, "label": label, "detail": detail})
        if not getattr(args, "json", False):
            doctor_result(status, label, detail)
        if status == "FAIL":
            failures += 1
        elif status == "WARN":
            warnings += 1

    if not getattr(args, "json", False):
        print("Plex Curator Doctor")
        print("===================")
        print()

    if sys.version_info >= (3, 10):
        report("PASS", "Python", sys.version.split()[0])
    else:
        report("FAIL", "Python", f"{sys.version.split()[0]} (3.10+ required)")

    try:
        import plexapi
        report("PASS", "PlexAPI", getattr(plexapi, "__version__", "installed"))
    except Exception as exc:
        report("FAIL", "PlexAPI", str(exc))

    try:
        import dotenv
        report("PASS", "python-dotenv", "installed")
    except Exception as exc:
        report("FAIL", "python-dotenv", str(exc))

    for module_name, label in [
        ("requests", "requests"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
    ]:
        try:
            module = __import__(module_name)
            report("PASS", label, getattr(module, "__version__", "installed"))
        except Exception as exc:
            report("FAIL", label, str(exc))

    for path, label in [
        (APP_DIR / "plex-curator", "CLI wrapper"),
        (APP_DIR / "plex-curator-api", "API wrapper"),
        (APP_DIR / "plex_curator.py", "Core program"),
        (APP_DIR / "launchd-manager.py", "launchd manager"),
    ]:
        report("PASS" if path.exists() else "FAIL", label, str(path))

    if args.fix:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_DIR.exists() and os.access(CONFIG_DIR, os.W_OK):
        report("PASS", "Config directory", f"writable: {CONFIG_DIR}")
    else:
        report("FAIL", "Config directory", f"not writable or missing: {CONFIG_DIR}")

    if CONFIG_FILE.exists():
        try:
            mode = CONFIG_FILE.stat().st_mode & 0o777
            if args.fix and mode != 0o600:
                os.chmod(CONFIG_FILE, 0o600)
                mode = 0o600
            report("PASS", "Permanent config", f"{CONFIG_FILE} mode={oct(mode)}")
            if mode & 0o077:
                report("WARN", ".env permissions", "recommended mode is 0o600")
        except Exception as exc:
            report("FAIL", "Permanent config", str(exc))
    else:
        report("FAIL", "Permanent config", f"missing: {CONFIG_FILE}")

    load_dotenv(CONFIG_FILE, override=True)
    plex_url = os.getenv("PLEX_URL", "").strip()
    plex_token = os.getenv("PLEX_TOKEN", "").strip()

    report("PASS" if plex_url else "FAIL", "PLEX_URL", plex_url or "missing or blank")
    report("PASS" if plex_token else "FAIL", "PLEX_TOKEN", f"present ({len(plex_token)} chars; value hidden)" if plex_token else "missing or blank")

    if args.fix:
        try:
            ensure_config()
            report("PASS", "Safe repair", "default config/state files initialized")
        except Exception as exc:
            report("FAIL", "Safe repair", str(exc))

        repaired, detail = repair_trailing_json_junk(STATIONS_FILE)
        if repaired:
            report("PASS", "Stations JSON repair", detail)
        elif detail not in {"already valid", "file does not exist"}:
            report("WARN", "Stations JSON repair", detail)

    for path, label in [
        (PRESETS_FILE, "Movie presets JSON"),
        (SCHEDULES_FILE, "Schedules JSON"),
        (STATIONS_FILE, "Stations JSON"),
    ]:
        status, detail = json_file_check(path)
        report(status, label, detail)

    try:
        stations = load_stations()
        for sid, raw in stations.items():
            normalize_station(sid, raw)
        report("PASS", "Station profile validation", f"{len(stations)} valid")
    except Exception as exc:
        report("FAIL", "Station profile validation", str(exc))

    status, detail = sqlite_integrity_check(STATE_DB)
    report(status, "State database", detail)

    if args.fix:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if EXPORT_DIR.exists() and os.access(EXPORT_DIR, os.W_OK):
        report("PASS", "Export directory", f"writable: {EXPORT_DIR}")
    else:
        report("WARN", "Export directory", f"missing/not writable: {EXPORT_DIR}")

    if plex_url and plex_token:
        try:
            plex = PlexServer(plex_url, plex_token, timeout=10)
            report("PASS", "Plex connection", f"{plex.friendlyName} ({plex.version})")
            sections = plex.library.sections()
            report("PASS" if sections else "WARN", "Plex libraries", ", ".join(f"{s.title} [{s.type}]" for s in sections) if sections else "none returned")
            names = {s.title for s in sections}
            for expected in ("Movies", "TV Shows"):
                report("PASS" if expected in names else "WARN", f'Library "{expected}"', "found" if expected in names else "not found")
        except Exception as exc:
            report("FAIL", "Plex connection", str(exc))
    else:
        report("WARN", "Plex connection", "skipped because URL/token is incomplete")

    manager = APP_DIR / "launchd-manager.py"
    if manager.exists():
        report("PASS", "launchd manager", str(manager))
        if args.verbose:
            launch_agents = HOME / "Library" / "LaunchAgents"
            plists = sorted(launch_agents.glob("com.ry.plexcurator.*.plist")) if launch_agents.exists() else []
            if plists:
                for plist in plists:
                    label = plist.stem
                    try:
                        res = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{label}"], capture_output=True, text=True)
                        report("PASS" if res.returncode == 0 else "WARN", f"launchd {label}", "loaded" if res.returncode == 0 else "plist exists, job not loaded")
                    except Exception as exc:
                        report("WARN", f"launchd {label}", str(exc))
            else:
                report("WARN", "launchd jobs", "none installed (optional)")
    else:
        report("WARN", "launchd manager", "not found")

    overall = "NEEDS ATTENTION" if failures else ("HEALTHY WITH WARNINGS" if warnings else "HEALTHY")
    if getattr(args, "json", False):
        print(json.dumps({
            "app_version": APP_VERSION,
            "result": overall,
            "failures": failures,
            "warnings": warnings,
            "checks": results,
        }, indent=2))
    else:
        print()
        print("-------------------")
        print(f"Failures: {failures}")
        print(f"Warnings: {warnings}")
        print(f"Result: {overall}")

    if failures:
        raise SystemExit(1)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(prog="plex-curator", description="Local Plex playlist and channel curator.")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("setup"); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_setup)
    p = sp.add_parser("config"); p.set_defaults(func=cmd_config)
    p = sp.add_parser("test"); p.set_defaults(func=cmd_test)
    p = sp.add_parser("libraries"); p.set_defaults(func=cmd_libraries)

    p = sp.add_parser("search")
    p.add_argument("library"); p.add_argument("query"); p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    p = sp.add_parser("export")
    p.add_argument("library"); p.add_argument("--include-episodes", action="store_true")
    p.set_defaults(func=cmd_export)

    p = sp.add_parser("create-file")
    p.add_argument("name"); p.add_argument("library"); p.add_argument("file"); p.add_argument("--replace", action="store_true"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_create_file)

    p = sp.add_parser("playlists"); p.set_defaults(func=cmd_playlists)
    p = sp.add_parser("show-playlist"); p.add_argument("name"); p.set_defaults(func=cmd_show_playlist)
    p = sp.add_parser("delete-playlist"); p.add_argument("name"); p.add_argument("--yes", action="store_true"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_delete_playlist)

    p = sp.add_parser("presets"); p.set_defaults(func=cmd_presets)
    p = sp.add_parser("preset")
    p.add_argument("name"); p.add_argument("--create", action="store_true"); p.add_argument("--playlist")
    p.add_argument("--replace", action="store_true"); p.add_argument("--dry-run", action="store_true"); p.set_defaults(func=cmd_preset)

    p = sp.add_parser("curate")
    p.add_argument("--library", default="Movies")
    p.add_argument("--genre"); p.add_argument("--year-min", type=int); p.add_argument("--year-max", type=int)
    p.add_argument("--max-runtime", type=float); p.add_argument("--content-rating", action="append")
    p.add_argument("--min-audience", type=float); p.add_argument("--min-critic", type=float)
    p.add_argument("--watched", action="store_true"); p.add_argument("--unwatched", action="store_true")
    p.add_argument("--random", action="store_true"); p.add_argument("--limit", type=int, default=25)
    p.add_argument("--playlist"); p.add_argument("--replace", action="store_true"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_curate)

    p = sp.add_parser("channel")
    p.add_argument("--preset", required=True, choices=sorted(CHANNEL_PRESETS))
    p.add_argument("--per-show", type=int, default=5)
    p.add_argument("--total", type=int, default=40)
    p.add_argument("--playlist"); p.add_argument("--unwatched", action="store_true")
    p.add_argument("--adult", action="store_true")
    p.add_argument("--avoid-recent", type=int, default=120)
    p.add_argument("--min-show-gap", type=int, default=2)
    p.add_argument("--seasonal", choices=["auto", "none", "halloween", "christmas"], default="auto")
    p.add_argument("--special-every", type=int, default=8)
    p.add_argument("--ignore-watch-progress", action="store_true")
    p.add_argument("--create", action="store_true"); p.add_argument("--replace", action="store_true"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_channel)

    p = sp.add_parser("schedule-list"); p.set_defaults(func=cmd_schedule_list)
    p = sp.add_parser("schedule-show"); p.add_argument("name"); p.set_defaults(func=cmd_schedule_show)
    p = sp.add_parser("schedule-build")
    p.add_argument("name"); p.add_argument("--playlist")
    p.add_argument("--avoid-recent", type=int, default=150)
    p.add_argument("--min-show-gap", type=int, default=2)
    p.add_argument("--seasonal", choices=["auto", "none", "halloween", "christmas"], default="auto")
    p.add_argument("--special-every", type=int, default=8)
    p.add_argument("--unwatched", action="store_true")
    p.add_argument("--ignore-watch-progress", action="store_true")
    p.add_argument("--create", action="store_true"); p.add_argument("--replace", action="store_true"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_schedule_build)

    p = sp.add_parser("wishlist-check")
    p.add_argument("file"); p.add_argument("--library", default="Movies"); p.add_argument("--output-missing")
    p.set_defaults(func=cmd_wishlist_check)

    p = sp.add_parser("progress")
    p.add_argument("--preset", choices=sorted(CHANNEL_PRESETS), default="all-cartoons")
    p.set_defaults(func=cmd_progress)

    p = sp.add_parser("history")
    p.add_argument("--channel"); p.add_argument("--limit", type=int, default=50); p.set_defaults(func=cmd_history)

    p = sp.add_parser("build-history")
    p.add_argument("--limit", type=int, default=20); p.set_defaults(func=cmd_build_history)

    p = sp.add_parser("state-info"); p.set_defaults(func=cmd_state_info)

    p = sp.add_parser("state-reset")
    p.add_argument("--channel"); p.add_argument("--yes", action="store_true"); p.set_defaults(func=cmd_state_reset)


    # Station Profiles (v10)
    p = sp.add_parser("station-list", help="List persistent station profiles.")
    p.set_defaults(func=cmd_station_list)

    p = sp.add_parser("station-show", help="Show one station profile.")
    p.add_argument("station_id")
    p.set_defaults(func=cmd_station_show)

    p = sp.add_parser("station-preview", help="Preview a station without modifying Plex.")
    p.add_argument("station_id")
    p.add_argument("--total", type=int)
    p.set_defaults(func=cmd_station_preview)

    p = sp.add_parser("station-refresh", help="Rebuild one station's Plex playlist.")
    p.add_argument("station_id")
    p.add_argument("--total", type=int)
    p.add_argument("--force", action="store_true", help="Refresh even when station is disabled.")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_station_refresh)

    p = sp.add_parser("station-refresh-all", help="Refresh all enabled station profiles.")
    p.add_argument("--include-disabled", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_station_refresh_all)

    p = sp.add_parser("station-create", help="Create a persistent station profile.")
    p.add_argument("station_id")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--playlist")
    p.add_argument("--preset", choices=sorted(CHANNEL_PRESETS), default="all-cartoons")
    p.add_argument("--year-min", type=int)
    p.add_argument("--year-max", type=int)
    p.add_argument("--adult", action="store_true")
    p.add_argument("--disabled", action="store_true")
    p.add_argument("--per-show", type=int, default=5)
    p.add_argument("--total", type=int, default=40)
    p.add_argument("--avoid-recent", type=int, default=120)
    p.add_argument("--min-show-gap", type=int, default=2)
    p.add_argument("--seasonal", choices=["auto","none","halloween","christmas"], default="auto")
    p.add_argument("--special-every", type=int, default=8)
    p.add_argument("--unwatched", action="store_true")
    p.add_argument("--ignore-watch-progress", action="store_true")
    p.add_argument("--include-show", action="append")
    p.add_argument("--exclude-show", action="append")
    p.add_argument("--genre", action="append")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=cmd_station_create)

    p = sp.add_parser("station-update", help="Update selected station settings.")
    p.add_argument("station_id")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--playlist")
    p.add_argument("--preset", choices=sorted(CHANNEL_PRESETS))
    p.add_argument("--year-min", type=int)
    p.add_argument("--year-max", type=int)
    p.add_argument("--adult", action="store_true", default=None)
    p.add_argument("--kids-only", action="store_true", default=None)
    p.add_argument("--per-show", type=int)
    p.add_argument("--total", type=int)
    p.add_argument("--avoid-recent", type=int)
    p.add_argument("--min-show-gap", type=int)
    p.add_argument("--seasonal", choices=["auto","none","halloween","christmas"])
    p.add_argument("--special-every", type=int)
    p.add_argument("--unwatched", action="store_true", default=None)
    p.add_argument("--allow-watched", action="store_true", default=None)
    p.add_argument("--ignore-watch-progress", action="store_true", default=None)
    p.add_argument("--follow-watch-progress", action="store_true", default=None)
    p.add_argument("--include-show", action="append")
    p.add_argument("--exclude-show", action="append")
    p.add_argument("--genre", action="append")
    p.set_defaults(func=cmd_station_update)

    p = sp.add_parser("station-clone", help="Clone a station profile.")
    p.add_argument("source_station_id")
    p.add_argument("new_station_id")
    p.add_argument("--name")
    p.add_argument("--playlist")
    p.add_argument("--disabled", action="store_true")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=cmd_station_clone)

    p = sp.add_parser("station-enable")
    p.add_argument("station_id")
    p.set_defaults(func=cmd_station_enable)

    p = sp.add_parser("station-disable")
    p.add_argument("station_id")
    p.set_defaults(func=cmd_station_disable)

    p = sp.add_parser("station-delete", help="Delete a station profile, not its Plex playlist.")
    p.add_argument("station_id")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_station_delete)

    p = sp.add_parser("station-history")
    p.add_argument("station_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_station_history)


    p = sp.add_parser("doctor", help="Run Plex Curator health and configuration checks.")
    p.add_argument("--verbose", action="store_true", help="Show optional launchd job checks.")
    p.add_argument("--fix", action="store_true", help="Apply safe local repairs only.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    p.set_defaults(func=cmd_doctor)


    p = sp.add_parser("station-diff", help="Compare current Plex playlist with the proposed station lineup.")
    p.add_argument("station_id")
    p.add_argument("--total", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_station_diff)

    p = sp.add_parser("backup", help="Back up persistent Plex Curator configuration and state.")
    p.add_argument("--reason", default="manual")
    p.set_defaults(func=cmd_backup)

    p = sp.add_parser("backup-list", help="List recent Plex Curator backups.")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_backup_list)

    p = sp.add_parser("logs", help="Read launchd logs.")
    p.add_argument("job", nargs="?")
    p.add_argument("--errors", action="store_true")
    p.add_argument("--lines", type=int, default=100)
    p.add_argument("--follow", action="store_true")
    p.set_defaults(func=cmd_logs)

    return ap

def main():
    args = build_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()