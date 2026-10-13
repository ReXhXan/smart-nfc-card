"""Aggregate tap events into a small analytics summary."""
from collections import Counter


def _device(ua: str) -> str:
    ua = (ua or "").lower()
    if "iphone" in ua or "ipad" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    return "desktop/other" if ua else "unknown"


def summarize(rows) -> dict:
    by_day = Counter(r["ts"][:10] for r in rows)
    return {
        "total": len(rows),
        "by_source": dict(Counter(r["source"] for r in rows)),
        "by_device": dict(Counter(_device(r["user_agent"]) for r in rows)),
        "by_day": dict(sorted(by_day.items())),
        "last_tap": rows[-1]["ts"] if rows else None,
    }
