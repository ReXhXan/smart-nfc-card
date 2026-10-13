"""SQLite persistence for cards and tap events (stdlib only, no ORM)."""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from .models import Card, CardIn

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    slug TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS taps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL REFERENCES cards(slug) ON DELETE CASCADE,
    ts TEXT NOT NULL,
    source TEXT NOT NULL,
    user_agent TEXT,
    referrer TEXT
);
CREATE INDEX IF NOT EXISTS idx_taps_slug ON taps(slug);
"""


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()

    # ---- cards ----
    def upsert(self, card: CardIn) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO cards(slug, data, created_at) VALUES (?, ?, ?) "
                "ON CONFLICT(slug) DO UPDATE SET data = excluded.data",
                (card.slug, card.model_dump_json(), _now()),
            )

    def get(self, slug: str) -> Card | None:
        row = self._conn.execute("SELECT data FROM cards WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return None
        taps = self._conn.execute("SELECT COUNT(*) FROM taps WHERE slug = ?", (slug,)).fetchone()[0]
        return Card(**json.loads(row["data"]), taps=taps)

    def delete(self, slug: str) -> bool:
        with self._lock, self._conn:
            return self._conn.execute("DELETE FROM cards WHERE slug = ?", (slug,)).rowcount > 0

    # ---- analytics ----
    def record_tap(self, slug: str, source: str, user_agent: str = "", referrer: str = "") -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO taps(slug, ts, source, user_agent, referrer) VALUES (?, ?, ?, ?, ?)",
                (slug, _now(), source, user_agent[:300], referrer[:300]),
            )

    def tap_rows(self, slug: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT ts, source, user_agent FROM taps WHERE slug = ? ORDER BY ts", (slug,)
        ).fetchall()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
