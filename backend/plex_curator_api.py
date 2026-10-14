#!/usr/bin/env python3
from __future__ import annotations

import json
import secrets
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

import plex_curator as core

API_VERSION = "1.0"
API_KEY_FILE = core.CONFIG_DIR / "api.key"

app = FastAPI(
    title="Plex Curator Local API",
    version=API_VERSION,
    description="Localhost-only API for Plex Curator.",
)

class PreviewRequest(BaseModel):
    total: Optional[int] = Field(default=None, ge=1, le=1000)

class RefreshRequest(BaseModel):
    total: Optional[int] = Field(default=None, ge=1, le=1000)
    dry_run: bool = False
    force: bool = False

class RefreshAllRequest(BaseModel):
    dry_run: bool = False
    include_disabled: bool = False

class BackupRequest(BaseModel):
    reason: str = Field(default="api", min_length=1, max_length=80)

def ensure_api_key() -> str:
    core.ensure_config()
    if not API_KEY_FILE.exists():
        API_KEY_FILE.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
        API_KEY_FILE.chmod(0o600)
    else:
        mode = API_KEY_FILE.stat().st_mode & 0o777
        if mode != 0o600:
            API_KEY_FILE.chmod(0o600)
    return API_KEY_FILE.read_text(encoding="utf-8").strip()

def require_api_key(
    x_plex_curator_key: Optional[str] = Header(default=None, alias="X-Plex-Curator-Key"),
):
    expected = ensure_api_key()
    if not x_plex_curator_key or not secrets.compare_digest(x_plex_curator_key, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid Plex Curator API key.")
    return True

def station_or_404(station_id: str):
    stations = core.load_stations()
    if station_id not in stations:
        raise HTTPException(status_code=404, detail=f'Unknown station "{station_id}".')
    try:
        return core.normalize_station(station_id, stations[station_id])
    except SystemExit as exc:
        raise HTTPException(status_code=422, detail=str(exc))

def serialize_item(item, position: Optional[int] = None):
    data = {
        "rating_key": str(getattr(item, "ratingKey", "") or ""),
        "type": getattr(item, "type", None),
        "title": getattr(item, "title", None),
        "year": getattr(item, "year", None),
        "content_rating": getattr(item, "contentRating", None),
        "view_count": getattr(item, "viewCount", 0) or 0,
        "watched": core.is_watched(item),
    }
    if position is not None:
        data["position"] = position
    if getattr(item, "type", "") == "episode":
        data.update({
            "show_title": getattr(item, "grandparentTitle", None),
            "season_number": getattr(item, "parentIndex", None),
            "episode_number": getattr(item, "index", None),
            "summary": getattr(item, "summary", None),
        })
    return data

def station_summary(station_id: str, raw: dict):
    cfg = core.normalize_station(station_id, raw)
    return {
        "id": station_id,
        **cfg,
    }

def build_station_payload(station_id: str, total: Optional[int] = None):
    cfg = station_or_404(station_id)
    plex = core.connect()
    items, shows, mode, cursor_updates = core.station_build_items(
        plex, station_id, cfg, total
    )
    return plex, cfg, items, shows, mode, cursor_updates

def playlist_diff_payload(plex, cfg, proposed_items):
    existing = core.find_playlist(plex, cfg["playlist"])
    current_items = list(existing.items()) if existing else []
    return core.calculate_playlist_diff(current_items, proposed_items)

@app.get("/api/v1/ping")
def ping():
    return {
        "ok": True,
        "api_version": API_VERSION,
        "curator_version": getattr(core, "APP_VERSION", "unknown"),
        "time": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/v1/status")
def status():
    core.ensure_config()
    stations = core.load_stations()
    enabled = 0
    for sid, raw in stations.items():
        try:
            if core.normalize_station(sid, raw)["enabled"]:
                enabled += 1
        except Exception:
            pass

    plex_status = {
        "connected": False,
        "server_name": None,
        "server_version": None,
        "libraries": [],
        "error": None,
    }
    try:
        plex = core.connect()
        plex_status.update({
            "connected": True,
            "server_name": plex.friendlyName,
            "server_version": plex.version,
            "libraries": [
                {"name": s.title, "type": s.type}
                for s in plex.library.sections()
            ],
        })
    except BaseException as exc:
        plex_status["error"] = str(exc)

    return {
        "api_version": API_VERSION,
        "curator_version": getattr(core, "APP_VERSION", "unknown"),
        "plex": plex_status,
        "station_count": len(stations),
        "enabled_station_count": enabled,
        "paths": {
            "config_dir": str(core.CONFIG_DIR),
            "state_db": str(core.STATE_DB),
            "stations": str(core.STATIONS_FILE),
            "schedules": str(core.SCHEDULES_FILE),
            "backups": str(core.BACKUP_DIR),
            "logs": str(core.LOG_DIR),
        },
    }

@app.get("/api/v1/doctor")
def doctor():
    result = subprocess.run(
        [str(core.APP_DIR / "plex-curator"), "doctor", "--json"],
        cwd=str(core.APP_DIR),
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
    except Exception:
        payload = {
            "result": "ERROR",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    return payload

@app.get("/api/v1/stations")
def stations():
    raw = core.load_stations()
    return {
        "stations": [
            station_summary(sid, raw[sid])
            for sid in sorted(raw)
        ]
    }

@app.get("/api/v1/stations/{station_id}")
def station_detail(station_id: str):
    return station_summary(station_id, core.load_stations().get(station_id, {})) if station_id in core.load_stations() else station_or_404(station_id)

@app.post("/api/v1/stations/{station_id}/preview")
def station_preview(station_id: str, request: PreviewRequest):
    _plex, cfg, items, shows, mode, _cursor_updates = build_station_payload(
        station_id, request.total
    )
    return {
        "station": {"id": station_id, **cfg},
        "show_count": len(shows),
        "seasonal_mode": mode,
        "item_count": len(items),
        "items": [
            serialize_item(item, i)
            for i, item in enumerate(items, 1)
        ],
        "read_only": True,
    }

@app.get("/api/v1/stations/{station_id}/diff")
def station_diff(station_id: str, total: Optional[int] = Query(default=None, ge=1, le=1000)):
    plex, cfg, items, shows, mode, _cursor_updates = build_station_payload(station_id, total)
    diff = playlist_diff_payload(plex, cfg, items)
    return {
        "station": {"id": station_id, **cfg},
        "show_count": len(shows),
        "seasonal_mode": mode,
        "diff": diff,
        "proposed_items": [
            serialize_item(item, i)
            for i, item in enumerate(items, 1)
        ],
        "read_only": True,
    }

@app.post("/api/v1/stations/{station_id}/refresh")
def station_refresh(
    station_id: str,
    request: RefreshRequest,
    _authorized: bool = Depends(require_api_key),
):
    plex, cfg, items, shows, mode, cursor_updates = build_station_payload(
        station_id, request.total
    )
    if not cfg["enabled"] and not request.force:
        raise HTTPException(
            status_code=409,
            detail=f'Station "{station_id}" is disabled.',
        )
    if not items:
        raise HTTPException(status_code=409, detail="No station items were selected.")

    diff = playlist_diff_payload(plex, cfg, items)
    if request.dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "station": {"id": station_id, **cfg},
            "diff": diff,
            "item_count": len(items),
            "read_only": True,
        }

    try:
        core.replace_playlist_with_rollback(plex, cfg["playlist"], items)
        core.apply_cursor_updates(cursor_updates)
        for ep in items:
            core.remember_episode(ep, f"station:{station_id}")
        core.remember_build(f"station:{station_id}", cfg["playlist"], len(items))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "ok": True,
        "dry_run": False,
        "station_id": station_id,
        "playlist": cfg["playlist"],
        "item_count": len(items),
        "seasonal_mode": mode,
        "diff": diff,
    }

@app.post("/api/v1/stations/refresh-all")
def station_refresh_all(
    request: RefreshAllRequest,
    _authorized: bool = Depends(require_api_key),
):
    raw = core.load_stations()
    plex = core.connect()
    results = []

    for station_id in sorted(raw):
        cfg = core.normalize_station(station_id, raw[station_id])
        if not cfg["enabled"] and not request.include_disabled:
            continue
        try:
            items, shows, mode, cursor_updates = core.station_build_items(
                plex, station_id, cfg, None
            )
            diff = playlist_diff_payload(plex, cfg, items)
            if request.dry_run:
                results.append({
                    "station_id": station_id,
                    "ok": True,
                    "dry_run": True,
                    "item_count": len(items),
                    "diff": diff,
                })
                continue

            if not items:
                results.append({
                    "station_id": station_id,
                    "ok": False,
                    "error": "No items selected.",
                })
                continue

            core.replace_playlist_with_rollback(plex, cfg["playlist"], items)
            core.apply_cursor_updates(cursor_updates)
            for ep in items:
                core.remember_episode(ep, f"station:{station_id}")
            core.remember_build(f"station:{station_id}", cfg["playlist"], len(items))
            results.append({
                "station_id": station_id,
                "ok": True,
                "dry_run": False,
                "item_count": len(items),
                "playlist": cfg["playlist"],
            })
        except Exception as exc:
            results.append({
                "station_id": station_id,
                "ok": False,
                "error": str(exc),
            })

    return {
        "ok": all(r.get("ok") for r in results) if results else True,
        "dry_run": request.dry_run,
        "results": results,
    }

@app.get("/api/v1/playlists")
def playlists():
    plex = core.connect()
    result = []
    for playlist in sorted(plex.playlists(), key=lambda x: x.title.casefold()):
        result.append({
            "title": playlist.title,
            "item_count": getattr(playlist, "leafCount", None),
            "rating_key": str(getattr(playlist, "ratingKey", "") or ""),
        })
    return {"playlists": result}

@app.get("/api/v1/playlists/{playlist_name}")
def playlist_detail(playlist_name: str):
    plex = core.connect()
    playlist = core.find_playlist(plex, playlist_name)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    items = list(playlist.items())
    return {
        "title": playlist.title,
        "item_count": len(items),
        "items": [
            serialize_item(item, i)
            for i, item in enumerate(items, 1)
        ],
    }

@app.get("/api/v1/history")
def history(
    station_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=1000),
):
    core.ensure_config()
    con = sqlite3.connect(core.STATE_DB)
    cur = con.cursor()
    if station_id:
        channel = f"station:{station_id}"
        cur.execute(
            """
            SELECT selected_at, show_title, season_number, episode_number,
                   episode_title, channel_name
            FROM episode_play_history
            WHERE channel_name = ?
            ORDER BY id DESC LIMIT ?
            """,
            (channel, limit),
        )
    else:
        cur.execute(
            """
            SELECT selected_at, show_title, season_number, episode_number,
                   episode_title, channel_name
            FROM episode_play_history
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        )
    rows = cur.fetchall()
    con.close()
    return {
        "history": [
            {
                "selected_at": row[0],
                "show_title": row[1],
                "season_number": row[2],
                "episode_number": row[3],
                "episode_title": row[4],
                "channel_name": row[5],
            }
            for row in rows
        ]
    }

@app.get("/api/v1/build-history")
def build_history(limit: int = Query(default=20, ge=1, le=1000)):
    core.ensure_config()
    con = sqlite3.connect(core.STATE_DB)
    cur = con.cursor()
    cur.execute(
        """
        SELECT built_at, channel_name, playlist_name, item_count
        FROM build_history ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    con.close()
    return {
        "builds": [
            {
                "built_at": row[0],
                "channel_name": row[1],
                "playlist_name": row[2],
                "item_count": row[3],
            }
            for row in rows
        ]
    }

@app.get("/api/v1/backups")
def backups(limit: int = Query(default=20, ge=1, le=200)):
    core.ensure_config()
    entries = []
    if core.BACKUP_DIR.exists():
        for path in sorted(
            [p for p in core.BACKUP_DIR.iterdir() if p.is_dir()],
            key=lambda p: p.name,
            reverse=True,
        )[:limit]:
            manifest = {}
            manifest_path = path / "manifest.json"
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            entries.append({
                "name": path.name,
                "path": str(path),
                "manifest": manifest,
            })
    return {"backups": entries}

@app.post("/api/v1/backups")
def create_backup(
    request: BackupRequest,
    _authorized: bool = Depends(require_api_key),
):
    try:
        path = core.create_backup(request.reason)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        "ok": True,
        "path": str(path),
        "name": path.name,
    }

@app.get("/api/v1/logs/{job}")
def logs(
    job: str,
    errors: bool = False,
    lines: int = Query(default=100, ge=1, le=5000),
):
    suffix = "err.log" if errors else "out.log"
    path = core.LOG_DIR / f"{job}.{suffix}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Log file not found.")
    content = core.tail_lines(path, lines)
    return {
        "job": job,
        "errors": errors,
        "path": str(path),
        "lines": [line.rstrip("\n") for line in content],
    }

@app.get("/api/v1/security")
def security():
    ensure_api_key()
    return {
        "bind_address": "127.0.0.1",
        "network_exposure": False,
        "cors_enabled": False,
        "mutation_auth": "X-Plex-Curator-Key",
        "api_key_file": str(API_KEY_FILE),
    }
