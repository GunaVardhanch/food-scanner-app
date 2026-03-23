"""
history_service.py
──────────────────
Manages scan history storage in SQLite (food_scanner.db).

Tables
──────
  users          — auth accounts
  scans          — legacy blob-based history (kept for backwards compat)
  scan_results   — NEW flat schema: one column per nutrition/additive field,
                   linked to users via user_id, auto-purged after 90 days
  preferences    — per-user dietary toggles
  nutrition_cache — GTIN → product data cache
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DB_PATH = str(Path(__file__).resolve().parents[2] / "food_scanner.db")
_TTL_DAYS = 90  # records older than this are purged rolling


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Schema bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables and run migrations. Safe to call on every startup."""
    with _get_conn() as conn:
        # ── users ──────────────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                email      TEXT    NOT NULL UNIQUE,
                password   TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # ── legacy scans (blob-based, kept for backwards compat) ───────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER,
                product_name        TEXT,
                brand               TEXT,
                gtin                TEXT,
                health_score        TEXT,
                score_value         REAL,
                nutrition           TEXT,
                ingredients         TEXT,
                flagged_additives   TEXT,
                healthy_alternative TEXT,
                source              TEXT,
                timestamp           TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans (user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans (timestamp DESC)")

        # ── NEW flat scan_results table ────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                -- product identity
                product_name        TEXT,
                brand               TEXT,
                gtin                TEXT,
                source              TEXT,

                -- health verdict
                health_score        TEXT,           -- GREEN / YELLOW / RED
                score_value         REAL,           -- 0.0 – 10.0
                scan_mode           TEXT,           -- barcode | label

                -- nutrition (per 100 g, individual columns for SQL queries)
                calories_kcal       REAL,
                protein_g           REAL,
                fat_g               REAL,
                saturated_fat_g     REAL,
                carbs_g             REAL,
                sugar_g             REAL,
                fiber_g             REAL,
                sodium_mg           REAL,

                -- additives summary
                additive_count          INTEGER DEFAULT 0,
                harmful_additive_count  INTEGER DEFAULT 0,
                additives_json          TEXT,   -- full list as JSON
                harmful_additives_json  TEXT,   -- only RED-risk additives as JSON

                -- ingredients & recommendation
                ingredients_text    TEXT,
                healthy_alternative TEXT,

                -- TTL anchor
                scanned_at          TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at          TEXT NOT NULL  -- scanned_at + 90 days
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sr_user_id
            ON scan_results (user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sr_scanned_at
            ON scan_results (scanned_at DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sr_expires_at
            ON scan_results (expires_at)
        """)

        # ── preferences ────────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id     INTEGER PRIMARY KEY,
                vegan       INTEGER DEFAULT 0,
                no_sugar    INTEGER DEFAULT 0,
                low_sodium  INTEGER DEFAULT 0,
                gluten_free INTEGER DEFAULT 0
            )
        """)

        # ── nutrition_cache ────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_cache (
                gtin       TEXT PRIMARY KEY,
                data       TEXT NOT NULL,
                fetched_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

    _migrate_legacy_columns()
    _migrate_json_history()
    purge_expired()  # clean up any rows that expired while the server was down


# ─────────────────────────────────────────────────────────────────────────────
# Migrations
# ─────────────────────────────────────────────────────────────────────────────

_SCANS_REQUIRED_COLUMNS: List[tuple] = [
    ("user_id",             "INTEGER"),
    ("brand",               "TEXT"),
    ("gtin",                "TEXT"),
    ("ingredients",         "TEXT"),
    ("source",              "TEXT"),
    ("nutrition",           "TEXT"),
    ("flagged_additives",   "TEXT"),
    ("healthy_alternative", "TEXT"),
    ("score_value",         "REAL"),
    ("health_score",        "TEXT"),
]

# Columns that must exist on scan_results (added here for future migrations)
_SCAN_RESULTS_REQUIRED_COLUMNS: List[tuple] = [
    ("harmful_additives_json", "TEXT"),
    ("scan_mode",              "TEXT"),
]


def _migrate_legacy_columns() -> None:
    """Add missing columns to the legacy scans table and scan_results (non-destructive)."""
    with _get_conn() as conn:
        existing_scans = {row[1] for row in conn.execute("PRAGMA table_info(scans)").fetchall()}
        for col_name, col_def in _SCANS_REQUIRED_COLUMNS:
            if col_name not in existing_scans:
                conn.execute(f"ALTER TABLE scans ADD COLUMN {col_name} {col_def}")
                logger.info("DB migration: added column scans.%s", col_name)

        existing_sr = {row[1] for row in conn.execute("PRAGMA table_info(scan_results)").fetchall()}
        for col_name, col_def in _SCAN_RESULTS_REQUIRED_COLUMNS:
            if col_name not in existing_sr:
                conn.execute(f"ALTER TABLE scan_results ADD COLUMN {col_name} {col_def}")
                logger.info("DB migration: added column scan_results.%s", col_name)

        conn.commit()


def _migrate_json_history() -> None:
    """One-time import of legacy scan_history.json into the scans table."""
    json_path = Path(_DB_PATH).parent / "scan_history.json"
    if not json_path.exists():
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            old = json.load(f)
        if not isinstance(old, list) or not old:
            return
        with _get_conn() as conn:
            if conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0] > 0:
                return
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
        json_path.rename(json_path.with_suffix(".json.migrated"))
    except Exception as exc:
        logger.warning("JSON history migration failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# TTL purge — called on startup and before every history fetch
# ─────────────────────────────────────────────────────────────────────────────

def purge_expired() -> int:
    """Delete scan_results rows past their expires_at. Returns count deleted."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM scan_results WHERE expires_at < ?", (now,))
        conn.commit()
        deleted = cur.rowcount
    if deleted:
        logger.info("TTL purge: removed %d expired scan_results", deleted)
    return deleted


# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────

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
    scan_mode: Optional[str] = "barcode",
    user_id: Optional[int] = None,
) -> int:
    """
    Write to both tables:
      • scans        — legacy blob row (backwards compat)
      • scan_results — new flat row (only when user_id is present)

    Returns the scan_results.id if user is authenticated, else scans.id.
    """
    n = nutrition or {}
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    expires_str = (datetime.utcnow() + timedelta(days=_TTL_DAYS)).strftime("%Y-%m-%d %H:%M:%S")

    additives = flagged_additives or []
    harmful_count = sum(
        1 for a in additives
        if (isinstance(a, dict) and a.get("risk_level") == "RED")
    )
    ingredients_text = (
        ", ".join(ingredients) if isinstance(ingredients, list) else (ingredients or "")
    )

    with _get_conn() as conn:
        # ── legacy scans row ───────────────────────────────────────────────
        legacy_cur = conn.execute(
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
                json.dumps(n),
                json.dumps(ingredients or []),
                json.dumps(additives),
                healthy_alternative,
                source,
                now_str,
            ),
        )

        result_id = legacy_cur.lastrowid

        # ── flat scan_results row (authenticated users only) ───────────────
        if user_id is not None:
            harmful_additives = [
                a for a in additives
                if isinstance(a, dict) and a.get("risk_level") == "RED"
            ]
            sr_cur = conn.execute(
                """INSERT INTO scan_results (
                    user_id, product_name, brand, gtin, source,
                    health_score, score_value, scan_mode,
                    calories_kcal, protein_g, fat_g, saturated_fat_g,
                    carbs_g, sugar_g, fiber_g, sodium_mg,
                    additive_count, harmful_additive_count,
                    additives_json, harmful_additives_json,
                    ingredients_text, healthy_alternative,
                    scanned_at, expires_at
                ) VALUES (
                    ?,?,?,?,?,
                    ?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,
                    ?,?,
                    ?,?,
                    ?,?
                )""",
                (
                    user_id,
                    product_name or "Unknown Product",
                    brand,
                    gtin,
                    source,
                    health_score,
                    score_value,
                    scan_mode or "barcode",
                    _to_float(n.get("energy_kcal") or n.get("calories")),
                    _to_float(n.get("protein_g")   or n.get("protein")),
                    _to_float(n.get("fat_g")        or n.get("total_fat")),
                    _to_float(n.get("saturated_fat_g")),
                    _to_float(n.get("carbohydrates_g") or n.get("carbs")),
                    _to_float(n.get("sugars_g")     or n.get("sugar")),
                    _to_float(n.get("fiber_g")      or n.get("fiber")),
                    _to_float(n.get("sodium_mg")    or n.get("sodium")),
                    len(additives),
                    harmful_count,
                    json.dumps(additives),
                    json.dumps(harmful_additives),
                    ingredients_text,
                    healthy_alternative,
                    now_str,
                    expires_str,
                ),
            )
            result_id = sr_cur.lastrowid
            logger.info(
                "scan_results saved — user=%s | %s | %s %.1f | additives=%d | expires=%s",
                user_id, gtin or "label", health_score, score_value,
                len(additives), expires_str,
            )

        conn.commit()
    return result_id


def _to_float(val: Any) -> Optional[float]:
    """Convert a value like '12.3g' or 12.3 or None to float or None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).strip().split()[0].rstrip("gGmMkKcC%"))
    except (ValueError, IndexError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Fetch history
# ─────────────────────────────────────────────────────────────────────────────

def get_history(limit: int = 50, user_id: Optional[int] = None) -> List[Dict]:
    """
    Return the most recent scans for a user.

    Authenticated users  → reads from scan_results (flat, TTL-managed)
    Anonymous            → reads from legacy scans (no TTL)
    """
    purge_expired()  # rolling cleanup on every fetch — zero-infrastructure

    with _get_conn() as conn:
        if user_id is not None:
            rows = conn.execute(
                """SELECT * FROM scan_results
                   WHERE user_id = ?
                   ORDER BY scanned_at DESC
                   LIMIT ?""",
                (user_id, limit),
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                try:
                    d["flagged_additives"] = json.loads(d.get("additives_json") or "[]")
                except Exception:
                    d["flagged_additives"] = []
                try:
                    d["harmful_additives"] = json.loads(d.get("harmful_additives_json") or "[]")
                except Exception:
                    d["harmful_additives"] = []
                # normalise timestamp key so frontend works unchanged
                d["timestamp"] = d.get("scanned_at", "")[:16]
                # rebuild flat nutrition dict for hover card
                d["nutrition"] = {
                    "calories":  _fmt(d.get("calories_kcal"), " kcal"),
                    "protein":   _fmt(d.get("protein_g")),
                    "total_fat": _fmt(d.get("fat_g")),
                    "sugar":     _fmt(d.get("sugar_g")),
                    "carbs":     _fmt(d.get("carbs_g")),
                    "sodium":    _fmt(d.get("sodium_mg"), " mg"),
                    "fiber":     _fmt(d.get("fiber_g")),
                }
                result.append(d)
            return result
        else:
            rows = conn.execute(
                """SELECT * FROM scans
                   WHERE user_id IS NULL
                   ORDER BY id DESC LIMIT ?""",
                (limit,),
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


def _fmt(val: Optional[float], unit: str = "g") -> str:
    if val is None:
        return "N/A"
    return f"{round(val, 1)}{unit}"


# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

def delete_scan(scan_id: int, user_id: Optional[int] = None) -> bool:
    """Delete from scan_results (and legacy scans) by id with ownership check."""
    with _get_conn() as conn:
        if user_id is not None:
            r1 = conn.execute(
                "DELETE FROM scan_results WHERE id=? AND user_id=?", (scan_id, user_id)
            ).rowcount
            r2 = conn.execute(
                "DELETE FROM scans WHERE id=? AND user_id=?", (scan_id, user_id)
            ).rowcount
        else:
            r1 = conn.execute("DELETE FROM scan_results WHERE id=?", (scan_id,)).rowcount
            r2 = conn.execute("DELETE FROM scans WHERE id=?", (scan_id,)).rowcount
        conn.commit()
    return (r1 + r2) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Analytics — now powered by flat scan_results columns
# ─────────────────────────────────────────────────────────────────────────────

def get_analytics(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Compute analytics. Uses scan_results for auth users, legacy scans otherwise."""
    purge_expired()

    with _get_conn() as conn:
        if user_id is not None:
            rows = conn.execute(
                "SELECT * FROM scan_results WHERE user_id=? ORDER BY scanned_at ASC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id ASC"
            ).fetchall()

    scans = [dict(r) for r in rows]
    if not scans:
        return {
            "total_scans": 0, "avg_score": 0, "history_trend": [],
            "score_distribution": {"GREEN": 0, "YELLOW": 0, "RED": 0},
            "top_additives": [], "daily_avg": [], "green_streak": 0,
        }

    scores = [s.get("score_value") or 0 for s in scans]
    avg_score = round(sum(scores) / len(scores), 1)

    trend_scans = scans[-30:]
    ts_key = "scanned_at" if user_id else "timestamp"

    def _build_trend_item(s: Dict) -> Dict:
        # Parse additives
        raw_add = s.get("additives_json") or s.get("flagged_additives") or "[]"
        try:
            additives = json.loads(raw_add) if isinstance(raw_add, str) else (raw_add or [])
        except Exception:
            additives = []

        raw_harm = s.get("harmful_additives_json") or "[]"
        try:
            harmful = json.loads(raw_harm) if isinstance(raw_harm, str) else (raw_harm or [])
        except Exception:
            harmful = [a for a in additives if isinstance(a, dict) and a.get("risk_level") == "RED"]

        # Nutrition — prefer flat columns, fall back to blob
        if user_id is not None:
            nutrition = {
                "calories":  _fmt(s.get("calories_kcal"), " kcal"),
                "protein":   _fmt(s.get("protein_g")),
                "total_fat": _fmt(s.get("fat_g")),
                "sugar":     _fmt(s.get("sugar_g")),
                "carbs":     _fmt(s.get("carbs_g")),
                "sodium":    _fmt(s.get("sodium_mg"), " mg"),
                "fiber":     _fmt(s.get("fiber_g")),
            }
        else:
            raw_n = s.get("nutrition") or "{}"
            try:
                nutrition = json.loads(raw_n) if isinstance(raw_n, str) else (raw_n or {})
            except Exception:
                nutrition = {}

        return {
            "score":               round(s.get("score_value") or 0, 1),
            "product":             s.get("product_name") or "Unknown",
            "brand":               s.get("brand") or "",
            "grade":               s.get("health_score") or "YELLOW",
            "timestamp":           s.get(ts_key, ""),
            "nutrition":           nutrition,
            "flagged_additives":   additives,
            "harmful_additives":   harmful,
            "healthy_alternative": s.get("healthy_alternative") or "",
        }

    history_trend = [_build_trend_item(s) for s in trend_scans]

    dist = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for s in scans:
        grade = s.get("health_score") or "YELLOW"
        if grade in dist:
            dist[grade] += 1

    # Top additives — from additives_json (flat table) or flagged_additives blob
    additive_counts: Dict[str, int] = {}
    for s in scans:
        raw = s.get("additives_json") or s.get("flagged_additives") or "[]"
        try:
            flags = json.loads(raw) if isinstance(raw, str) else raw
            for a in flags:
                name = a.get("name", "") if isinstance(a, dict) else str(a)
                if name:
                    additive_counts[name] = additive_counts.get(name, 0) + 1
        except Exception:
            pass
    top_additives = sorted(
        [{"name": k, "count": v} for k, v in additive_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:5]

    streak = 0
    for s in reversed(scans):
        if s.get("health_score") == "GREEN":
            streak += 1
        else:
            break

    daily: Dict[str, List[float]] = defaultdict(list)
    for s in scans:
        day = (s.get(ts_key) or "")[:10]
        if day:
            daily[day].append(s.get("score_value") or 0)
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
