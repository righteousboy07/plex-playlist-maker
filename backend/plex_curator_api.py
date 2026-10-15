#!/usr/bin/env python3
from __future__ import annotations

import json
import secrets
import sqlite3
import subprocess
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

import plex_curator as core

API_VERSION = "1.4"
API_KEY_FILE = core.CONFIG_DIR / "api.key"
LAUNCHD_MANAGER = core.APP_DIR / "launchd-manager.py"
KIDS_SCARY_WISHLIST = core.APP_DIR / "examples" / "kids-scary-missing-wishlist.txt"
TITLE_ALIASES_FILE = core.APP_DIR / "examples" / "title-aliases.json"

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

class MediaOrganizerRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)
    destination: Optional[str] = Field(default=None, max_length=4096)
    recursive: bool = True

class MediaOrganizerApplyRequest(MediaOrganizerRequest):
    include_low_confidence: bool = False

class BackupRequest(BaseModel):
    reason: str = Field(default="api", min_length=1, max_length=80)

class MovieFilterRequest(BaseModel):
    library: str = Field(default="Movies", min_length=1, max_length=120)
    genre: Optional[str] = Field(default=None, max_length=80)
    year_min: Optional[int] = Field(default=None, ge=1880, le=2200)
    year_max: Optional[int] = Field(default=None, ge=1880, le=2200)
    max_runtime: Optional[int] = Field(default=None, ge=1, le=1000)
    content_ratings: list[str] = Field(default_factory=list)
    min_audience: Optional[float] = Field(default=None, ge=0, le=10)
    min_critic: Optional[float] = Field(default=None, ge=0, le=10)
    watched: bool = False
    unwatched: bool = False
    random: bool = False
    limit: Optional[int] = Field(default=50, ge=1, le=500)

class MoviePlaylistRequest(MovieFilterRequest):
    playlist: str = Field(min_length=1, max_length=120)
    replace: bool = True

class ScheduleOptionsRequest(BaseModel):
    playlist: Optional[str] = Field(default=None, min_length=1, max_length=120)
    avoid_recent: int = Field(default=150, ge=0, le=100000)
    min_show_gap: int = Field(default=2, ge=0, le=100)
    seasonal: str = Field(default="auto")
    special_every: int = Field(default=8, ge=1, le=1000)
    unwatched: bool = False
    ignore_watch_progress: bool = False

class ScheduleBuildRequest(ScheduleOptionsRequest):
    replace: bool = True

class InterstitialPoolRequest(BaseModel):
    playlist: str = Field(min_length=1, max_length=120)
    type: str = Field(default="general")
    weight: int = Field(default=1, ge=1, le=1000)

class StationUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    enabled: Optional[bool] = None
    playlist: Optional[str] = Field(default=None, min_length=1, max_length=120)
    preset: Optional[str] = None
    year_min: Optional[int] = Field(default=None, ge=1900, le=2200)
    year_max: Optional[int] = Field(default=None, ge=1900, le=2200)
    kids_only: Optional[bool] = None
    adult: Optional[bool] = None
    per_show: Optional[int] = Field(default=None, ge=1, le=100)
    total: Optional[int] = Field(default=None, ge=1, le=1000)
    avoid_recent: Optional[int] = Field(default=None, ge=0, le=100000)
    min_show_gap: Optional[int] = Field(default=None, ge=0, le=100)
    seasonal: Optional[str] = None
    special_every: Optional[int] = Field(default=None, ge=1, le=1000)
    interstitial_playlists: Optional[list[str]] = None
    interstitial_pools: Optional[list[InterstitialPoolRequest]] = None
    interstitial_every: Optional[int] = Field(default=None, ge=0, le=1000)
    interstitial_count: Optional[int] = Field(default=None, ge=1, le=20)
    unwatched: Optional[bool] = None
    sync_watch_progress: Optional[bool] = None
    include_shows: Optional[list[str]] = None
    exclude_shows: Optional[list[str]] = None
    genres_any: Optional[list[str]] = None

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
    rating_key = str(getattr(item, "ratingKey", "") or "")
    duration_ms = getattr(item, "duration", None)
    data = {
        "rating_key": rating_key,
        "type": getattr(item, "type", None),
        "title": getattr(item, "title", None),
        "year": getattr(item, "year", None),
        "content_rating": getattr(item, "contentRating", None),
        "view_count": getattr(item, "viewCount", 0) or 0,
        "watched": core.is_watched(item),
        "summary": getattr(item, "summary", None),
        "duration_minutes": round(duration_ms / 60000) if duration_ms else None,
        "thumb_available": bool(getattr(item, "thumb", None)),
        "artwork_url": f"/api/v1/artwork/{rating_key}" if rating_key and getattr(item, "thumb", None) else None,
    }
    if position is not None:
        data["position"] = position
    if getattr(item, "type", "") == "episode":
        data.update({
            "show_title": getattr(item, "grandparentTitle", None),
            "season_number": getattr(item, "parentIndex", None),
            "episode_number": getattr(item, "index", None),
        })
    return data

def station_summary(station_id: str, raw: dict):
    cfg = core.normalize_station(station_id, raw)
    return {
        "id": station_id,
        **cfg,
    }

def update_station_config(station_id: str, changes: dict):
    stations = core.load_stations()
    if station_id not in stations:
        raise HTTPException(status_code=404, detail=f'Unknown station "{station_id}".')

    current = core.normalize_station(station_id, stations[station_id])
    merged = {**current, **changes}
    if "interstitial_playlists" in changes and "interstitial_pools" not in changes:
        merged["interstitial_pools"] = [
            {"playlist": name, "type": "general", "weight": 1}
            for name in (changes.get("interstitial_playlists") or [])
        ]
    if "interstitial_pools" in changes:
        merged["interstitial_pools"] = [
            pool.model_dump() if hasattr(pool, "model_dump") else pool
            for pool in (changes.get("interstitial_pools") or [])
        ]

    if merged.get("preset") not in core.CHANNEL_PRESETS:
        raise HTTPException(status_code=422, detail=f'Unknown station preset "{merged.get("preset")}".')
    if merged.get("seasonal") not in {"auto", "none", "halloween", "christmas"}:
        raise HTTPException(status_code=422, detail="Invalid seasonal setting.")

    try:
        normalized = core.normalize_station(station_id, merged)
    except SystemExit as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Persist normalized data so partial updates cannot leave incompatible types
    # or omit fields expected by the CLI and future API clients.
    stations[station_id] = normalized
    core.save_stations(stations)
    return station_summary(station_id, normalized)

def movie_request_options(request: MovieFilterRequest):
    if request.watched and request.unwatched:
        raise HTTPException(status_code=422, detail="watched and unwatched cannot both be true.")
    if request.year_min is not None and request.year_max is not None and request.year_min > request.year_max:
        raise HTTPException(status_code=422, detail="year_min cannot be greater than year_max.")
    return {
        "genre": request.genre,
        "year_min": request.year_min,
        "year_max": request.year_max,
        "max_runtime": request.max_runtime,
        "content_ratings": request.content_ratings,
        "min_audience": request.min_audience,
        "min_critic": request.min_critic,
        "watched": request.watched,
        "unwatched": request.unwatched,
        "random": request.random,
        "limit": request.limit,
    }

def select_movies(plex, request: MovieFilterRequest):
    try:
        section = core.get_section(plex, request.library)
    except SystemExit as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return core.movie_filter(section.all(), movie_request_options(request))

def load_title_aliases():
    if not TITLE_ALIASES_FILE.exists():
        return {}
    try:
        data = json.loads(TITLE_ALIASES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}

def resolve_title_with_aliases(section, title, year=None):
    item = core.resolve_title(section, title, year)
    if item:
        return item
    for alias in load_title_aliases().get(title, []):
        item = core.resolve_title(section, alias, year)
        if item:
            return item
    return None

def schedule_summary(schedule_id: str, cfg: dict):
    blocks = []
    total_minutes = 0
    for index, block in enumerate(cfg.get("blocks", []), 1):
        minutes = int(block.get("minutes", 60))
        total_minutes += minutes
        blocks.append({
            "index": index,
            "name": block.get("name", f"Block {index}"),
            "type": block.get("type"),
            "preset": block.get("preset"),
            "minutes": minutes,
            "seasonal": block.get("seasonal"),
        })
    return {
        "id": schedule_id,
        "description": cfg.get("description", ""),
        "playlist": cfg.get("playlist") or schedule_id.replace("-", " ").title(),
        "total_minutes": total_minutes,
        "blocks": blocks,
    }

def schedule_or_404(schedule_id: str):
    schedules = core.load_schedules()
    if schedule_id not in schedules:
        raise HTTPException(status_code=404, detail=f'Unknown schedule "{schedule_id}".')
    return schedules[schedule_id]

def schedule_options(request: ScheduleOptionsRequest):
    if request.seasonal not in {"auto", "none", "halloween", "christmas"}:
        raise HTTPException(status_code=422, detail="Invalid seasonal setting.")
    return {
        "avoid_recent": request.avoid_recent,
        "min_show_gap": request.min_show_gap,
        "seasonal": request.seasonal,
        "special_every": request.special_every,
        "unwatched": request.unwatched,
        "sync_watch_progress": not request.ignore_watch_progress,
    }

def build_schedule_payload(plex, schedule_id: str, request: ScheduleOptionsRequest):
    cfg = schedule_or_404(schedule_id)
    options = schedule_options(request)
    items = []
    pending_cursor_updates = {}
    block_results = []

    for index, block in enumerate(cfg.get("blocks", []), 1):
        block_name = block.get("name", f"Block {index}")
        block_type = block.get("type")
        minutes = int(block.get("minutes", 60))

        if block_type == "cartoons":
            estimated = max(1, round(minutes / 22))
            picked, _shows, mode, block_cursor_updates = core.build_channel(
                plex=plex,
                preset_name=block.get("preset", "all-cartoons"),
                channel_name=f"schedule:{schedule_id}:{block_name}",
                per_show=max(2, min(8, estimated)),
                total=estimated,
                unwatched=options["unwatched"],
                avoid_recent=options["avoid_recent"],
                sync_watch_progress=options["sync_watch_progress"],
                min_show_gap=options["min_show_gap"],
                seasonal=block.get("seasonal", options["seasonal"]),
                special_every=options["special_every"],
                adult=False,
            )
            pending_cursor_updates.update(block_cursor_updates)
        elif block_type == "movie":
            picked = core.choose_movie_block(
                plex,
                block.get("preset", "friday-movie-night"),
                minutes,
            )
            mode = block.get("seasonal", options["seasonal"])
        else:
            picked = []
            mode = block.get("seasonal", options["seasonal"])

        serialized = [
            serialize_item(item, len(items) + offset)
            for offset, item in enumerate(picked, 1)
        ]
        block_results.append({
            "index": index,
            "name": block_name,
            "type": block_type,
            "preset": block.get("preset"),
            "minutes": minutes,
            "seasonal_mode": mode,
            "item_count": len(picked),
            "items": serialized,
        })
        items.extend(picked)

    playlist = request.playlist or cfg.get("playlist") or schedule_id.replace("-", " ").title()
    return cfg, playlist, items, pending_cursor_updates, block_results

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

def run_launchd_manager(*args):
    result = subprocess.run(
        [sys.executable, str(LAUNCHD_MANAGER), *args],
        cwd=str(core.APP_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "launchd manager failed").strip()
        raise HTTPException(status_code=500, detail=detail)
    return result.stdout.strip()

def launchd_jobs_payload():
    try:
        return json.loads(run_launchd_manager("list-json"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid launchd manager JSON: {exc}")

def fetch_artwork_bytes(rating_key: int, width: int, height: int):
    plex = core.connect()
    try:
        item = plex.fetchItem(rating_key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Media item {rating_key} was not found.") from exc

    thumb = getattr(item, "thumb", None)
    if not thumb:
        raise HTTPException(status_code=404, detail="No artwork is available for this media item.")

    source_url = plex.url(thumb, includeToken=True)
    image_url = plex.transcodeImage(
        source_url,
        height=height,
        width=width,
        imageFormat="jpeg",
    )

    try:
        result = requests.get(image_url, timeout=15)
        result.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Plex artwork request failed.") from exc

    return result.content, result.headers.get("Content-Type", "image/jpeg")

@app.get("/api/v1/artwork/{rating_key}")
def artwork(
    rating_key: str,
    width: int = Query(default=240, ge=32, le=1200),
    height: int = Query(default=360, ge=32, le=1200),
):
    try:
        numeric_key = int(rating_key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="rating_key must be numeric.") from exc

    content, media_type = fetch_artwork_bytes(numeric_key, width, height)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )

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

@app.put("/api/v1/stations/{station_id}")
def station_update(
    station_id: str,
    request: StationUpdateRequest,
    _authorized: bool = Depends(require_api_key),
):
    changes = request.model_dump(exclude_unset=True)
    return {
        "ok": True,
        "station": update_station_config(station_id, changes),
    }

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

@app.post("/api/v1/media-organizer/scan")
def media_organizer_scan(request: MediaOrganizerRequest):
    try:
        plan = core.plan_media_organization(
            request.path,
            destination=request.destination,
            recursive=request.recursive,
        )
    except SystemExit as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {**plan, "read_only": True}

@app.post("/api/v1/media-organizer/apply")
def media_organizer_apply(
    request: MediaOrganizerApplyRequest,
    _authorized: bool = Depends(require_api_key),
):
    try:
        plan = core.plan_media_organization(
            request.path,
            destination=request.destination,
            recursive=request.recursive,
        )
        return core.apply_media_organization(
            plan,
            include_low_confidence=request.include_low_confidence,
        )
    except SystemExit as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/automation")
def automation_jobs():
    return launchd_jobs_payload()

@app.post("/api/v1/automation/{job_name}/install")
def automation_install(
    job_name: str,
    _authorized: bool = Depends(require_api_key),
):
    payload = launchd_jobs_payload()
    known = {job["name"] for job in payload.get("jobs", [])}
    if job_name not in known:
        raise HTTPException(status_code=404, detail=f'Unknown automation job "{job_name}".')
    run_launchd_manager("install", job_name)
    return {"ok": True, "job": json.loads(run_launchd_manager("status-json", job_name))}

@app.post("/api/v1/automation/{job_name}/uninstall")
def automation_uninstall(
    job_name: str,
    _authorized: bool = Depends(require_api_key),
):
    if job_name == "api-server":
        raise HTTPException(
            status_code=409,
            detail="The API server cannot uninstall its own LaunchAgent. Use launchd-manager.py from Terminal.",
        )
    payload = launchd_jobs_payload()
    known = {job["name"] for job in payload.get("jobs", [])}
    if job_name not in known:
        raise HTTPException(status_code=404, detail=f'Unknown automation job "{job_name}".')
    run_launchd_manager("uninstall", job_name)
    return {"ok": True, "job": json.loads(run_launchd_manager("status-json", job_name))}

@app.post("/api/v1/automation/{job_name}/run-now")
def automation_run_now(
    job_name: str,
    _authorized: bool = Depends(require_api_key),
):
    payload = launchd_jobs_payload()
    known = {job["name"] for job in payload.get("jobs", [])}
    if job_name not in known:
        raise HTTPException(status_code=404, detail=f'Unknown automation job "{job_name}".')
    run_launchd_manager("run-now", job_name)
    return {"ok": True, "job": json.loads(run_launchd_manager("status-json", job_name))}

@app.get("/api/v1/schedules")
def schedules_list():
    schedules = core.load_schedules()
    return {
        "schedules": [
            schedule_summary(schedule_id, schedules[schedule_id])
            for schedule_id in sorted(schedules)
        ]
    }

@app.get("/api/v1/schedules/{schedule_id}")
def schedule_detail(schedule_id: str):
    return schedule_summary(schedule_id, schedule_or_404(schedule_id))

@app.post("/api/v1/schedules/{schedule_id}/preview")
def schedule_preview(schedule_id: str, request: ScheduleOptionsRequest):
    plex = core.connect()
    cfg, playlist, items, _cursor_updates, blocks = build_schedule_payload(
        plex, schedule_id, request
    )
    return {
        "schedule": schedule_summary(schedule_id, cfg),
        "playlist": playlist,
        "item_count": len(items),
        "blocks": blocks,
        "items": [serialize_item(item, i) for i, item in enumerate(items, 1)],
        "read_only": True,
    }

@app.post("/api/v1/schedules/{schedule_id}/build")
def schedule_build(
    schedule_id: str,
    request: ScheduleBuildRequest,
    _authorized: bool = Depends(require_api_key),
):
    plex = core.connect()
    cfg, playlist_name, items, cursor_updates, blocks = build_schedule_payload(
        plex, schedule_id, request
    )
    if not items:
        raise HTTPException(status_code=409, detail="No schedule items were selected.")

    try:
        if request.replace:
            playlist = core.replace_playlist_with_rollback(plex, playlist_name, items)
        else:
            playlist = core.create_playlist(plex, playlist_name, items, replace=False)

        core.apply_cursor_updates(cursor_updates)
        for item in items:
            if getattr(item, "type", "") == "episode":
                core.remember_episode(item, f"schedule:{schedule_id}")
        core.remember_build(f"schedule:{schedule_id}", playlist.title, len(items))
    except SystemExit as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "ok": True,
        "schedule": schedule_summary(schedule_id, cfg),
        "playlist": playlist.title,
        "item_count": len(items),
        "blocks": blocks,
    }

@app.post("/api/v1/movies/preview")
def movies_preview(request: MovieFilterRequest):
    plex = core.connect()
    items = select_movies(plex, request)
    return {
        "count": len(items),
        "items": [serialize_item(item, i) for i, item in enumerate(items, 1)],
        "read_only": True,
    }

@app.post("/api/v1/movies/playlist")
def movies_create_playlist(
    request: MoviePlaylistRequest,
    _authorized: bool = Depends(require_api_key),
):
    plex = core.connect()
    items = select_movies(plex, request)
    if not items:
        raise HTTPException(status_code=409, detail="No movies matched the requested filters.")

    try:
        if request.replace:
            playlist = core.replace_playlist_with_rollback(plex, request.playlist, items)
        else:
            playlist = core.create_playlist(plex, request.playlist, items, replace=False)
    except SystemExit as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "ok": True,
        "playlist": playlist.title,
        "item_count": len(items),
    }

@app.get("/api/v1/wishlist/kids-scary")
def kids_scary_wishlist():
    plex = core.connect()
    try:
        section = core.get_section(plex, "Movies")
    except SystemExit as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    entries = []
    found_count = 0
    missing_count = 0

    for title, year in core.parse_wishlist(KIDS_SCARY_WISHLIST):
        item = resolve_title_with_aliases(section, title, year)
        if item:
            found_count += 1
            entries.append({
                "requested_title": title,
                "requested_year": year,
                "found": True,
                "matched_title": getattr(item, "title", None),
                "item": serialize_item(item),
            })
        else:
            missing_count += 1
            entries.append({
                "requested_title": title,
                "requested_year": year,
                "found": False,
                "matched_title": None,
                "item": None,
            })

    return {
        "found_count": found_count,
        "missing_count": missing_count,
        "total_count": len(entries),
        "entries": entries,
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
            "playlist_type": getattr(playlist, "playlistType", None),
            "smart": bool(getattr(playlist, "smart", False)),
            "updated_at": (
                getattr(playlist, "updatedAt", None).isoformat()
                if getattr(playlist, "updatedAt", None)
                else None
            ),
        })
    return {"playlists": result}

@app.get("/api/v1/playlist")
def playlist_detail_query(name: str = Query(min_length=1)):
    plex = core.connect()
    playlist = core.find_playlist(plex, name)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found.")
    items = list(playlist.items())
    return {
        "title": playlist.title,
        "rating_key": str(getattr(playlist, "ratingKey", "") or ""),
        "playlist_type": getattr(playlist, "playlistType", None),
        "smart": bool(getattr(playlist, "smart", False)),
        "item_count": len(items),
        "items": [serialize_item(item, i) for i, item in enumerate(items, 1)],
    }

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
