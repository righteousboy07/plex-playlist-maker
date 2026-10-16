#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
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
REVIEW_FRAMES_DIR = CONFIG_DIR / "review-frames"
LOG_DIR = HOME / "Library" / "Logs" / "PlexCurator"
APP_VERSION = "13.2.3"

VIDEO_EXTENSIONS = {
    ".mp4", ".m4v", ".mov", ".mkv", ".avi", ".wmv", ".webm", ".mpg", ".mpeg", ".ts"
}
INTERSTITIAL_TYPE_FOLDERS = {
    "station-id": "Station IDs",
    "bumper": "Bumpers",
    "commercial": "Commercials",
    "promo": "Promos",
    "general": "General",
}
MEDIA_NOISE_TOKENS = {
    "1080p", "720p", "480p", "2160p", "4k", "uhd", "hdr", "x264", "x265",
    "h264", "h265", "hevc", "av1", "aac", "ac3", "webdl", "web-dl", "webrip",
    "bluray", "blu-ray", "dvdrip", "remux", "proper", "repack", "yt", "youtube",
}


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

def has_partial_progress(item):
    return not is_watched(item) and (getattr(item, "viewOffset", 0) or 0) > 0

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
# Local interstitial media organizer
# ---------------------------------------------------------------------------

def media_title_is_generic(value):
    text = (value or "").strip().casefold()
    if not text:
        return True
    generic_patterns = [
        r"^(video|clip|movie|recording|screen[-_ ]?recording|download)[-_ ]?\d*$",
        r"^[a-z]{0,4}\d{3,}$",
        r"^\d{4,}$",
    ]
    return any(re.match(pattern, text) for pattern in generic_patterns)

def clean_media_title(value):
    text = Path(str(value or "")).stem
    text = re.sub(r"[._]+", " ", text)
    text = re.sub(r"\s*[-–—]\s*", " - ", text)
    text = re.sub(r"[\[\(](?:[^\]\)]*(?:1080|720|480|2160|4k|x264|x265|h264|h265|hevc|web.?dl|webrip|bluray|dvdrip)[^\]\)]*)[\]\)]", " ", text, flags=re.I)

    parts = []
    for part in re.split(r"\s+", text.strip()):
        token = re.sub(r"[^a-z0-9-]", "", part.casefold())
        if token in MEDIA_NOISE_TOKENS:
            continue
        parts.append(part)

    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip(" -_.")
    if not text:
        return "Untitled Clip"

    # Preserve all-caps abbreviations while making machine-like lowercase names readable.
    if text == text.lower() or "_" in str(value) or "." in str(value):
        words = []
        for word in text.split():
            words.append(word.upper() if len(word) <= 4 and word.isupper() else word.capitalize())
        text = " ".join(words)
    return text

def sanitize_media_filename(title):
    title = re.sub(r'[/:*?"<>|\\]+', " - ", str(title or ""))
    title = re.sub(r"\s+", " ", title).strip(" .-")
    return title or "Untitled Clip"

def probe_video_metadata(path):
    path = Path(path)
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            result = subprocess.run(
                [
                    ffprobe, "-v", "quiet", "-print_format", "json",
                    "-show_entries", "format_tags=title,comment,description",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                payload = json.loads(result.stdout)
                tags_data = (payload.get("format") or {}).get("tags") or {}
                return {
                    "title": tags_data.get("title") or tags_data.get("TITLE"),
                    "comment": tags_data.get("comment") or tags_data.get("COMMENT"),
                    "description": tags_data.get("description") or tags_data.get("DESCRIPTION"),
                    "source": "ffprobe",
                }
        except Exception:
            pass

    mdls = shutil.which("mdls")
    if mdls:
        try:
            result = subprocess.run(
                [mdls, "-raw", "-name", "kMDItemTitle", str(path)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            title = result.stdout.strip().strip('"') if result.returncode == 0 else ""
            if title and title != "(null)" and title != path.name:
                return {"title": title, "comment": None, "description": None, "source": "mdls"}
        except Exception:
            pass

    return {"title": None, "comment": None, "description": None, "source": None}

def probe_video_duration_seconds(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        result = subprocess.run(
            [
                ffprobe, "-v", "quiet", "-print_format", "json",
                "-show_entries", "format=duration", str(Path(path)),
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        payload = json.loads(result.stdout)
        duration = (payload.get("format") or {}).get("duration")
        return float(duration) if duration is not None else None
    except Exception:
        return None

def media_review_cache_key(path):
    path = Path(path).resolve()
    try:
        stat = path.stat()
        fingerprint = f"{path}|{stat.st_size}|{stat.st_mtime_ns}"
    except OSError:
        fingerprint = str(path)
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24]

def extract_media_review_frames(path, frame_count=3):
    path = Path(path).resolve()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"status": "ffmpeg-missing", "frames": []}

    duration = probe_video_duration_seconds(path)
    if duration is None or duration <= 0:
        return {"status": "duration-unavailable", "frames": []}

    frame_count = max(1, min(int(frame_count), 5))
    cache_key = media_review_cache_key(path)
    cache_dir = REVIEW_FRAMES_DIR / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)

    if frame_count == 1:
        fractions = [0.5]
    else:
        fractions = [
            0.12 + (0.76 * idx / (frame_count - 1))
            for idx in range(frame_count)
        ]

    frames = []
    for index, fraction in enumerate(fractions, 1):
        target = cache_dir / f"frame-{index}.jpg"
        if not target.exists():
            timestamp = max(0.0, min(duration - 0.05, duration * fraction))
            try:
                result = subprocess.run(
                    [
                        ffmpeg, "-hide_banner", "-loglevel", "error",
                        "-ss", f"{timestamp:.3f}",
                        "-i", str(path),
                        "-frames:v", "1",
                        "-vf", "scale='min(640,iw)':-2",
                        "-q:v", "3",
                        "-y", str(target),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                if result.returncode != 0 or not target.exists():
                    continue
            except Exception:
                continue

        frames.append({
            "id": f"{cache_key}/frame-{index}.jpg",
            "position": round(fraction, 3),
            "timestamp_seconds": round(duration * fraction, 2),
        })

    return {
        "status": "available" if frames else "failed",
        "frames": frames,
    }

def infer_interstitial_type(path, metadata=None):
    metadata = metadata or {}
    haystack = " ".join([
        str(Path(path).parent.name),
        str(Path(path).stem),
        str(metadata.get("title") or ""),
        str(metadata.get("comment") or ""),
        str(metadata.get("description") or ""),
    ]).casefold()

    rules = [
        ("station-id", [
            "station id", "station-id", "channel id", "network id", "ident",
            "network ident", "station ident", "logo ident",
        ]),
        ("bumper", [
            "bumper", "bump", "up next", "we'll be right back", "well be right back",
            "be right back", "back to", "coming up",
        ]),
        ("commercial", [
            "commercial", "advertisement", "advert", "tv ad", "tv spot", " ad ",
            "sponsor", "sponsored",
        ]),
        ("promo", [
            "promo", "promotion", "trailer", "teaser", "preview",
        ]),
    ]
    for media_type, keywords in rules:
        if any(keyword in f" {haystack} " for keyword in keywords):
            return media_type
    return "general"

def infer_media_identity(path):
    path = Path(path)
    metadata = probe_video_metadata(path)
    metadata_title = clean_media_title(metadata.get("title")) if metadata.get("title") else None
    filename_title = clean_media_title(path.stem)

    if metadata_title and not media_title_is_generic(metadata_title):
        title = metadata_title
        confidence = "high"
        title_source = metadata.get("source") or "metadata"
    elif not media_title_is_generic(filename_title):
        title = filename_title
        confidence = "medium"
        title_source = "filename"
    else:
        title = filename_title
        confidence = "low"
        title_source = "filename"

    media_type = infer_interstitial_type(path, metadata)
    return {
        "title": sanitize_media_filename(title),
        "type": media_type,
        "confidence": confidence,
        "title_source": title_source,
        "metadata_title": metadata.get("title"),
    }

def iter_video_files(root, recursive=True):
    root = Path(root).expanduser()
    iterator = root.rglob("*") if recursive else root.glob("*")
    return sorted(
        path for path in iterator
        if path.is_file() and path.suffix.casefold() in VIDEO_EXTENSIONS
    )

def unique_media_target(target, reserved):
    target = Path(target)
    candidate = target
    counter = 2
    while str(candidate).casefold() in reserved or candidate.exists():
        candidate = target.with_name(f"{target.stem} ({counter}){target.suffix}")
        counter += 1
    reserved.add(str(candidate).casefold())
    return candidate

def plan_media_organization(root, destination=None, recursive=True):
    root = Path(root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Media organizer source folder not found: {root}")

    destination_root = Path(destination).expanduser().resolve() if destination else root
    plans = []
    reserved = set()

    for source in iter_video_files(root, recursive=recursive):
        identity = infer_media_identity(source)
        review = (
            extract_media_review_frames(source, frame_count=3)
            if identity["confidence"] == "low"
            else {"status": "not-needed", "frames": []}
        )
        folder_name = INTERSTITIAL_TYPE_FOLDERS[identity["type"]]
        target_dir = destination_root / folder_name
        base_target = target_dir / f'{identity["title"]}{source.suffix.casefold()}'

        if source.resolve() == base_target.resolve():
            target = base_target
            action = "unchanged"
        else:
            target = unique_media_target(base_target, reserved)
            action = "move"

        plans.append({
            "source": str(source),
            "target": str(target),
            "original_name": source.name,
            "proposed_name": target.name,
            "title": identity["title"],
            "type": identity["type"],
            "folder": folder_name,
            "confidence": identity["confidence"],
            "title_source": identity["title_source"],
            "metadata_title": identity["metadata_title"],
            "review_frame_status": review["status"],
            "review_frames": review["frames"],
            "action": action,
        })

    return {
        "root": str(root),
        "destination": str(destination_root),
        "recursive": bool(recursive),
        "count": len(plans),
        "review_count": sum(1 for item in plans if item["confidence"] == "low"),
        "items": plans,
    }

def write_media_organizer_manifest(plan, applied=False):
    ensure_config()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = "applied" if applied else "preview"
    path = EXPORT_DIR / f"media-organizer-{stamp}-{suffix}.json"
    payload = {
        **plan,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "applied": bool(applied),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path

def apply_media_organization(plan, include_low_confidence=False):
    applied = []
    skipped = []
    errors = []

    for item in plan.get("items", []):
        source = Path(item["source"])
        target = Path(item["target"])

        if item.get("action") == "unchanged":
            skipped.append({**item, "reason": "already-organized"})
            continue
        if item.get("confidence") == "low" and not include_low_confidence:
            skipped.append({**item, "reason": "low-confidence"})
            continue
        if not source.exists():
            errors.append({**item, "error": "source-missing"})
            continue
        if target.exists():
            errors.append({**item, "error": "target-exists"})
            continue

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            applied.append(item)
        except Exception as exc:
            errors.append({**item, "error": str(exc)})

    result = {
        **plan,
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "applied_items": applied,
        "skipped_items": skipped,
        "errors": errors,
    }
    manifest = write_media_organizer_manifest(result, applied=True)
    result["manifest"] = str(manifest)
    return result

def print_media_organizer_plan(plan):
    print(f'Source:      {plan["root"]}')
    print(f'Destination: {plan["destination"]}')
    print(f'Videos:      {plan["count"]}')
    print(f'Needs review:{plan["review_count"]:>3}')
    print()
    for item in plan["items"]:
        marker = "REVIEW" if item["confidence"] == "low" else item["confidence"].upper()
        print(
            f'[{marker:6}] {item["original_name"]} -> '
            f'{item["folder"]}/{item["proposed_name"]}'
        )

def cmd_media_organize(args):
    plan = plan_media_organization(
        args.path,
        destination=args.destination,
        recursive=not args.no_recursive,
    )
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print_media_organizer_plan(plan)

    preview_manifest = write_media_organizer_manifest(plan, applied=False)
    if not args.json:
        print()
        print(f"Preview manifest: {preview_manifest}")

    if not args.apply:
        if not args.json:
            print("DRY RUN: no files were moved or renamed.")
        return

    result = apply_media_organization(
        plan,
        include_low_confidence=args.include_low_confidence,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print()
        print(f'Applied: {result["applied_count"]}')
        print(f'Skipped: {result["skipped_count"]}')
        print(f'Errors:  {result["error_count"]}')
        print(f'Manifest: {result["manifest"]}')
    if result["error_count"]:
        raise SystemExit(1)


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
        "view_offset_ms": getattr(item, "viewOffset", None) or 0,
        "progress_percent": (
            round(((getattr(item, "viewOffset", 0) or 0) / duration) * 100, 1)
            if duration else None
        ),
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
    playback = []
    for idx, ep in enumerate(episodes):
        last = parse_dt(getattr(ep, "lastViewedAt", None))
        if is_watched(ep):
            playback.append(((idx + 1) % len(episodes), idx, last, "complete"))
        elif has_partial_progress(ep):
            playback.append((idx, idx, last, "partial"))

    if not playback:
        return None, None

    with_dates = [row for row in playback if row[2] is not None]
    if with_dates:
        next_idx, _source_idx, latest, _state = max(with_dates, key=lambda row: row[2])
    else:
        next_idx, _source_idx, _latest, _state = max(playback, key=lambda row: row[1])
        latest = None
    return next_idx, latest

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

def collect_interstitial_pool_states(plex, pool_defs, recent_keys=None, exclude_keys=None):
    recent_keys = set(recent_keys or ())
    exclude_keys = set(exclude_keys or ())
    seen = set()
    missing = []
    states = []

    for pool_def in pool_defs or []:
        playlist_name = pool_def["playlist"]
        playlist = find_playlist(plex, playlist_name)
        if not playlist:
            missing.append(playlist_name)
            continue

        pool_items = []
        for item in playlist.items():
            item_type = (getattr(item, "type", "") or "").casefold()
            if item_type in {"track", "album", "artist"}:
                continue
            key = str(getattr(item, "ratingKey", "") or "")
            if not key or key in recent_keys or key in exclude_keys or key in seen:
                continue
            seen.add(key)
            pool_items.append(item)

        random.shuffle(pool_items)
        states.append({
            "playlist": playlist_name,
            "type": pool_def.get("type", "general"),
            "weight": int(pool_def.get("weight", 1)),
            "items": deque(pool_items),
        })

    if missing:
        raise SystemExit(
            "Interstitial Plex playlist(s) not found: " + ", ".join(sorted(missing))
        )

    return states

def collect_interstitial_items(plex, playlist_names, recent_keys=None, exclude_keys=None):
    pool_defs = [
        {"playlist": name, "type": "general", "weight": 1}
        for name in (playlist_names or [])
    ]
    states = collect_interstitial_pool_states(
        plex, pool_defs, recent_keys=recent_keys, exclude_keys=exclude_keys
    )
    out = []
    for state in states:
        out.extend(state["items"])
    random.shuffle(out)
    return out

def choose_weighted_interstitial(pool_states):
    active = [state for state in pool_states if state["items"]]
    if not active:
        return None
    chosen = random.choices(
        active,
        weights=[state["weight"] for state in active],
        k=1,
    )[0]
    return chosen["items"].popleft()

def inject_weighted_interstitials(items, pool_states, every, count=1):
    if not pool_states or every <= 0 or count <= 0:
        return list(items)

    out = []
    since_break = 0
    for item in items:
        out.append(item)
        since_break += 1
        if since_break < every:
            continue

        for _ in range(count):
            candidate = choose_weighted_interstitial(pool_states)
            if candidate is None:
                break
            out.append(candidate)
        since_break = 0
    return out

def inject_interstitials(items, interstitials, every, count=1):
    state = [{
        "playlist": "legacy",
        "type": "general",
        "weight": 1,
        "items": deque(interstitials or []),
    }]
    return inject_weighted_interstitials(items, state, every, count)

def build_channel(plex, preset_name, channel_name, per_show, total, unwatched, avoid_recent,
                  sync_watch_progress, min_show_gap, seasonal, special_every, adult=False,
                  profile_overrides=None, interstitial_playlists=None,
                  interstitial_pools=None, interstitial_every=0, interstitial_count=1):
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
    items = inject_specials(base_items, specials, special_every, min_show_gap)

    effective_pools = interstitial_pools or [
        {"playlist": name, "type": "general", "weight": 1}
        for name in (interstitial_playlists or [])
    ]
    if effective_pools and interstitial_every > 0:
        program_keys = {
            str(getattr(item, "ratingKey", ""))
            for item in items
            if getattr(item, "ratingKey", None)
        }
        pool_states = collect_interstitial_pool_states(
            plex,
            effective_pools,
            recent_keys=recent,
            exclude_keys=program_keys,
        )
        items = inject_weighted_interstitials(
            items,
            pool_states,
            interstitial_every,
            interstitial_count,
        )

    items = items[:total]
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
        if show:
            print(f"{ts} [{channel}] {show} S{s:02}E{e:02} — {title}")
        else:
            print(f"{ts} [{channel}] {title}")

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
    "interstitial_every": int,
    "interstitial_count": int,
    "interstitial_playlists": list,
    "interstitial_pools": list,
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

INTERSTITIAL_TYPES = {"general", "bumper", "station-id", "commercial", "promo"}

def normalize_interstitial_pools(station_id, cfg):
    raw_pools = cfg.get("interstitial_pools")
    if raw_pools:
        pools = []
        for raw in raw_pools:
            if not isinstance(raw, dict):
                raise SystemExit(f'Station "{station_id}" has an invalid interstitial pool.')
            playlist = str(raw.get("playlist", "")).strip()
            pool_type = str(raw.get("type", "general")).strip().casefold() or "general"
            try:
                weight = int(raw.get("weight", 1))
            except (TypeError, ValueError):
                raise SystemExit(f'Station "{station_id}" has an invalid interstitial weight.')
            if not playlist:
                raise SystemExit(f'Station "{station_id}" has an interstitial pool without a playlist.')
            if pool_type not in INTERSTITIAL_TYPES:
                raise SystemExit(
                    f'Station "{station_id}" has invalid interstitial type "{pool_type}".'
                )
            if weight < 1 or weight > 1000:
                raise SystemExit(
                    f'Station "{station_id}" requires interstitial weights from 1 through 1000.'
                )
            pools.append({"playlist": playlist, "type": pool_type, "weight": weight})
        return pools

    return [
        {"playlist": str(name).strip(), "type": "general", "weight": 1}
        for name in (cfg.get("interstitial_playlists", []) or [])
        if str(name).strip()
    ]

def parse_interstitial_pool_spec(spec):
    parts = [part.strip() for part in str(spec).split("|")]
    playlist = parts[0] if parts else ""
    pool_type = parts[1].casefold() if len(parts) > 1 and parts[1] else "general"
    try:
        weight = int(parts[2]) if len(parts) > 2 and parts[2] else 1
    except ValueError:
        raise SystemExit(
            f'Invalid interstitial pool "{spec}". Expected PLAYLIST|TYPE|WEIGHT.'
        )
    return normalize_interstitial_pools(
        "cli",
        {"interstitial_pools": [{"playlist": playlist, "type": pool_type, "weight": weight}]},
    )[0]

def normalize_station(station_id, cfg):
    interstitial_pools = normalize_interstitial_pools(station_id, cfg)
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
        "interstitial_playlists": [pool["playlist"] for pool in interstitial_pools],
        "interstitial_pools": interstitial_pools,
        "interstitial_every": int(cfg.get("interstitial_every", 0) or 0),
        "interstitial_count": int(cfg.get("interstitial_count", 1) or 1),
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
    if out["interstitial_every"] < 0:
        raise SystemExit(f'Station "{station_id}" requires interstitial_every >= 0.')
    if out["interstitial_count"] < 1:
        raise SystemExit(f'Station "{station_id}" requires interstitial_count >= 1.')
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
        interstitial_playlists=cfg["interstitial_playlists"],
        interstitial_pools=cfg["interstitial_pools"],
        interstitial_every=cfg["interstitial_every"],
        interstitial_count=cfg["interstitial_count"],
    )

def print_station_lineup(station_id, cfg, items, shows, mode):
    print(f'{cfg["name"]} [{station_id}]')
    print(f'Playlist: {cfg["playlist"]}')
    print(f'Preset:   {cfg["preset"]}')
    print(f'Shows:    {len(shows)}')
    print(f'Seasonal: {mode}')
    print()
    for i, item in enumerate(items, 1):
        if getattr(item, "type", "") == "episode":
            print(
                f"{i:>3}. {getattr(item,'grandparentTitle','')} — "
                f"S{getattr(item,'parentIndex',0):02}E{getattr(item,'index',0):02} — {item.title}"
            )
        else:
            media_type = getattr(item, "type", None) or "video"
            print(f"{i:>3}. {item.title} [{media_type}]")

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
        "interstitial_playlists": args.interstitial_playlist or [],
        "interstitial_pools": (
            [parse_interstitial_pool_spec(spec) for spec in (args.interstitial_pool or [])]
            if args.interstitial_pool else []
        ),
        "interstitial_every": args.interstitial_every,
        "interstitial_count": args.interstitial_count,
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
        "interstitial_every": args.interstitial_every,
        "interstitial_count": args.interstitial_count,
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
    if args.clear_interstitials:
        cfg["interstitial_playlists"] = []
        cfg["interstitial_pools"] = []
    elif args.interstitial_pool is not None:
        cfg["interstitial_pools"] = [
            parse_interstitial_pool_spec(spec) for spec in args.interstitial_pool
        ]
        cfg["interstitial_playlists"] = [
            pool["playlist"] for pool in cfg["interstitial_pools"]
        ]
    elif args.interstitial_playlist is not None:
        cfg["interstitial_playlists"] = args.interstitial_playlist
        cfg["interstitial_pools"] = [
            {"playlist": name, "type": "general", "weight": 1}
            for name in args.interstitial_playlist
        ]

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
    p.add_argument("--interstitial-playlist", action="append", help="Legacy Plex video playlist pool; repeat for multiple pools.")
    p.add_argument("--interstitial-pool", action="append", help="Weighted pool as PLAYLIST|TYPE|WEIGHT. Types: general, bumper, station-id, commercial, promo.")
    p.add_argument("--interstitial-every", type=int, default=0, help="Insert an interstitial break after this many program items; 0 disables.")
    p.add_argument("--interstitial-count", type=int, default=1, help="Number of clips inserted at each break.")
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
    p.add_argument("--interstitial-playlist", action="append", help="Replace with legacy general pools; repeat for multiple pools.")
    p.add_argument("--interstitial-pool", action="append", help="Replace weighted pools using PLAYLIST|TYPE|WEIGHT; repeat for multiple pools.")
    p.add_argument("--clear-interstitials", action="store_true")
    p.add_argument("--interstitial-every", type=int)
    p.add_argument("--interstitial-count", type=int)
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

    p = sp.add_parser("media-organize", help="Preview or organize local interstitial video files.")
    p.add_argument("path", help="Folder containing video clips.")
    p.add_argument("--destination", help="Destination root; defaults to organizing inside the source folder.")
    p.add_argument("--no-recursive", action="store_true", help="Only scan the top-level folder.")
    p.add_argument("--apply", action="store_true", help="Move and rename medium/high-confidence matches.")
    p.add_argument("--include-low-confidence", action="store_true", help="Also apply low-confidence filename guesses.")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_media_organize)

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