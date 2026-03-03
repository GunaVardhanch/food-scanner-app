"""
history_service.py
──────────────────
Manages scan history storage in SQLite (food_scanner.db).
Provides save, fetch, and analytics functions used by routes.py.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── DB path: same directory as this file's parent (backend/) ─────────────────
_DB_PATH = str(Path(__file__).resolve().parents[2] / "food_scanner.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist. Safe to call on every startup."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                email      TEXT    NOT NULL UNIQUE,
                password   TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER,
                product_name     TEXT,
                brand            TEXT,
                gtin             TEXT,
                health_score     TEXT,
                score_value      REAL,
                nutrition        TEXT,
                ingredients      TEXT,
                flagged_additives TEXT,
                healthy_alternative TEXT,
                source           TEXT,
                timestamp        TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_user_id
            ON scans (user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_timestamp
            ON scans (timestamp DESC)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id    INTEGER PRIMARY KEY,
                vegan      INTEGER DEFAULT 0,
                no_sugar   INTEGER DEFAULT 0,
                low_sodium INTEGER DEFAULT 0,
                gluten_free INTEGER DEFAULT 0
            )
        """)
        conn.commit()

    # ── Migrate old scan_history.json into DB (one-time) ────────────────────
    _migrate_json_history()


def _migrate_json_history() -> None:
    """Import entries from the legacy scan_history.json if present."""
    json_path = Path(_DB_PATH).parent / "scan_history.json"
    if not json_path.exists():
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            old = json.load(f)
        if not isinstance(old, list) or not old:
            return
        with _get_conn() as conn:
            existing = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
            if existing > 0:
                return          # already migrated
            for item in old:
                conn.execute(
                    """INSERT INTO scans
                       (product_name, health_score, score_value,
                        flagged_additives, healthy_alternative, timestamp)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        item.get("product_name", "Unknown"),
                        item.get("health_score", "YELLOW"),
                        item.get("score_value", 5.0),
                        json.dumps(item.get("flagged_additives", [])),
                        item.get("healthy_alternative"),
                        item.get("timestamp", datetime.utcnow().isoformat()),
                    ),
                )
            conn.commit()
        # Rename the old file so we don't migrate again
        json_path.rename(json_path.with_suffix(".json.migrated"))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("JSON history migration failed: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────

def save_scan(
    *,
    product_name: Optional[str] = None,
    brand: Optional[str] = None,
    gtin: Optional[str] = None,
    health_score: str = "YELLOW",
    score_value: float = 5.0,
    nutrition: Optional[Dict] = None,
    ingredients: Optional[List[str]] = None,
    flagged_additives: Optional[List] = None,
    healthy_alternative: Optional[str] = None,
    source: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    """Insert a scan record. Returns the new row id."""
    with _get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO scans
               (user_id, product_name, brand, gtin, health_score, score_value,
                nutrition, ingredients, flagged_additives, healthy_alternative,
                source, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user_id,
                product_name or "Unknown Product",
                brand,
                gtin,
                health_score,
                score_value,
                json.dumps(nutrition or {}),
                json.dumps(ingredients or []),
                json.dumps(flagged_additives or []),
                healthy_alternative,
                source,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_history(limit: int = 50, user_id: Optional[int] = None) -> List[Dict]:
    """Return the most recent `limit` scans, newest first."""
    with _get_conn() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT * FROM scans WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        for key in ("nutrition", "ingredients", "flagged_additives"):
            try:
                d[key] = json.loads(d[key] or "[]")
            except Exception:
                d[key] = []
        result.append(d)
    return result


def get_analytics(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Compute real analytics from scan history."""
    with _get_conn() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT * FROM scans WHERE user_id=? ORDER BY id ASC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id ASC"
            ).fetchall()

    scans = [dict(r) for r in rows]
    if not scans:
        return {
            "total_scans": 0,
            "avg_score": 0,
            "history_trend": [],
            "score_distribution": {"GREEN": 0, "YELLOW": 0, "RED": 0},
            "top_additives": [],
            "daily_avg": [],
            "green_streak": 0,
        }

    scores = [s["score_value"] or 0 for s in scans]
    avg_score = round(sum(scores) / len(scores), 1)

    # Last 30 entries for trend
    trend_scans = scans[-30:]
    history_trend = [
        {
            "score": round(s["score_value"] or 0, 1),
            "product": s["product_name"] or "Unknown",
            "grade": s["health_score"] or "YELLOW",
            "timestamp": s["timestamp"],
        }
        for s in trend_scans
    ]

    # Score distribution
    dist = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for s in scans:
        grade = s["health_score"] or "YELLOW"
        if grade in dist:
            dist[grade] += 1

    # Top flagged additives
    additive_counts: Dict[str, int] = {}
    for s in scans:
        try:
            flags = json.loads(s["flagged_additives"] or "[]")
            for a in flags:
                name = a.get("name", "") if isinstance(a, dict) else str(a)
                if name:
                    additive_counts[name] = additive_counts.get(name, 0) + 1
        except Exception:
            pass
    top_additives = sorted(
        [{"name": k, "count": v} for k, v in additive_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:5]

    # Green streak (consecutive GREEN from latest)
    streak = 0
    for s in reversed(scans):
        if s["health_score"] == "GREEN":
            streak += 1
        else:
            break

    # Daily rolling average (last 7 days)
    from collections import defaultdict
    daily: Dict[str, List[float]] = defaultdict(list)
    for s in scans:
        day = (s["timestamp"] or "")[:10]  # YYYY-MM-DD
        if day:
            daily[day].append(s["score_value"] or 0)
    daily_avg = [
        {"date": d, "avg": round(sum(v) / len(v), 1)}
        for d, v in sorted(daily.items())[-14:]
    ]

    return {
        "total_scans": len(scans),
        "avg_score": avg_score,
        "history_trend": history_trend,
        "score_distribution": dist,
        "top_additives": top_additives,
        "daily_avg": daily_avg,
        "green_streak": streak,
    }
