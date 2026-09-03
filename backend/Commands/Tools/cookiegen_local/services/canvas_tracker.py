"""Canvas strategy tracker — atribuye captchas/éxitos por estrategia de fingerprint.

Persiste en output/canvas_strategy_stats.json entre runs para acumular
estadísticas y auto-banear estrategias con captcha rate alto.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

_STATS_PATH: Path = Path("output") / "canvas_strategy_stats.json"
_LOCK = threading.Lock()

_DEFAULT_STRATEGIES: tuple[str, ...] = (
    "pixels_linear",
    "skia_soft",
    "cleartype_rgb",
    "entropy_layer",
)

_CAPTCHA_PER_ACCOUNT_FLAG: dict[str, bool] = {}
_PERSIST_PER_ACCOUNT_FLAG: dict[str, bool] = {}
_LEVEL4_PER_ACCOUNT_FLAG:  dict[str, bool] = {}


def _blank_row() -> dict[str, Any]:
    return {
        "metadata_uses": 0,
        "accounts_attempted": 0,
        "success_accounts": 0,
        "failed_accounts": 0,
        "captcha_triggered": 0,
        "captcha_accounts": 0,
        "captcha_level4": 0,
        "captcha_level4_accounts": 0,
        "captcha_solved": 0,
        "captcha_persisted": 0,
        "captcha_persisted_accounts": 0,
        "metadata1_len_sum": 0,
        "metadata1_len_count": 0,
        "last_used_ts": 0,
    }


def _load() -> dict[str, Any]:
    try:
        if _STATS_PATH.exists():
            data = json.loads(_STATS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "strategies" in data:
                for s in _DEFAULT_STRATEGIES:
                    data["strategies"].setdefault(s, _blank_row())
                return data
    except Exception:
        pass
    return {
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
        "total_accounts": 0,
        "strategies": {s: _blank_row() for s in _DEFAULT_STRATEGIES},
    }


def _save(state: dict[str, Any]) -> None:
    try:
        state["updated_at"] = int(time.time())
        _STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STATS_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _ensure_row(state: dict[str, Any], strategy: str) -> dict[str, Any]:
    if not strategy or strategy == "unknown":
        strategy = "skia_soft"
    rows = state.setdefault("strategies", {})
    row = rows.get(strategy)
    if row is None:
        row = _blank_row()
        rows[strategy] = row
    return row


def record_metadata_use(strategy: str, *, metadata1_len: int = 0) -> None:
    with _LOCK:
        state = _load()
        row = _ensure_row(state, strategy)
        row["metadata_uses"] += 1
        row["last_used_ts"] = int(time.time())
        if metadata1_len:
            row["metadata1_len_sum"] += int(metadata1_len)
            row["metadata1_len_count"] += 1
        _save(state)


def record_account_attempt(strategy: str) -> None:
    _CAPTCHA_PER_ACCOUNT_FLAG[strategy] = False
    _LEVEL4_PER_ACCOUNT_FLAG[strategy]  = False
    _PERSIST_PER_ACCOUNT_FLAG[strategy] = False
    with _LOCK:
        state = _load()
        state["total_accounts"] = state.get("total_accounts", 0) + 1
        row = _ensure_row(state, strategy)
        row["accounts_attempted"] += 1
        row["last_used_ts"] = int(time.time())
        _save(state)


def record_captcha(strategy: str, *, persisted: bool = False) -> None:
    first = not _CAPTCHA_PER_ACCOUNT_FLAG.get(strategy, False)
    first_persist = persisted and not _PERSIST_PER_ACCOUNT_FLAG.get(strategy, False)
    if first:
        _CAPTCHA_PER_ACCOUNT_FLAG[strategy] = True
    if first_persist:
        _PERSIST_PER_ACCOUNT_FLAG[strategy] = True
    with _LOCK:
        state = _load()
        row = _ensure_row(state, strategy)
        row["captcha_triggered"] += 1
        if first:
            row["captcha_accounts"] += 1
        if persisted:
            row["captcha_persisted"] += 1
            if first_persist:
                row["captcha_persisted_accounts"] += 1
        _save(state)


def record_account_result(strategy: str, *, success: bool) -> None:
    with _LOCK:
        state = _load()
        row = _ensure_row(state, strategy)
        if success:
            row["success_accounts"] += 1
        else:
            row["failed_accounts"] += 1
        _save(state)


def banned_strategies() -> set[str]:
    with _LOCK:
        state = _load()
    raw = state.get("banned") or []
    if isinstance(raw, dict):
        return {str(k) for k, v in raw.items() if v}
    return {str(x) for x in raw if x}


def apply_auto_ban(
    *,
    min_attempts: int = 4,
    captcha_rate_pct: float = 40.0,
    never_ban: tuple[str, ...] = ("skia_soft",),
) -> list[str]:
    report = build_report()
    newly: list[str] = []
    with _LOCK:
        state = _load()
        banned = set(state.get("banned") or [])
        if isinstance(state.get("banned"), dict):
            banned = {str(k) for k, v in state["banned"].items() if v}
        for row in report.get("strategies") or []:
            name = str(row.get("strategy") or "")
            if not name or name in never_ban or name in banned:
                continue
            att = int(row.get("accounts_attempted") or 0)
            if att < min_attempts:
                continue
            cap = float(row.get("captcha_rate_pct") or 0)
            if cap >= captcha_rate_pct:
                banned.add(name)
                newly.append(name)
        if newly or banned:
            state["banned"] = sorted(banned)
            _save(state)
    return newly


def build_report() -> dict[str, Any]:
    with _LOCK:
        state = _load()
    strategies = state.get("strategies", {})
    rows: list[dict[str, Any]] = []
    for name, row in strategies.items():
        att  = int(row.get("accounts_attempted") or 0)
        succ = int(row.get("success_accounts") or 0)
        fail = int(row.get("failed_accounts") or 0)
        cap_acc = int(row.get("captcha_accounts") or 0)
        s_l = int(row.get("metadata1_len_sum") or 0)
        c_l = int(row.get("metadata1_len_count") or 0)
        rows.append({
            "strategy":           name,
            "accounts_attempted": att,
            "success":            succ,
            "failed":             fail,
            "success_rate_pct":   round(100.0 * succ / att, 1) if att > 0 else 0.0,
            "captcha_accounts":   cap_acc,
            "captcha_rate_pct":   round(100.0 * cap_acc / att, 1) if att > 0 else 0.0,
            "avg_metadata1_len":  int(s_l / c_l) if c_l > 0 else 0,
        })
    rows.sort(key=lambda r: (r["captcha_rate_pct"], -r["success_rate_pct"]))
    best  = max(rows, key=lambda r: (r["success_rate_pct"], r["accounts_attempted"]))["strategy"] if rows else None
    worst = rows[-1]["strategy"] if rows else None
    return {
        "total_accounts": state.get("total_accounts", 0),
        "strategies":     rows,
        "_best":          best,
        "_worst":         worst,
        "stats_file":     str(_STATS_PATH.resolve()),
    }


def format_report_lines() -> list[str]:
    r = build_report()
    lines: list[str] = [
        "--- Canvas Strategy Report ---",
        f"total_accounts={r['total_accounts']}  stats_file={r['stats_file']}",
        f"{'strat':<17} {'att':>5} {'ok':>5} {'ok%':>6} {'fail':>5} {'capA':>5} {'cap%':>6} {'avg_md1':>8}",
    ]
    banned = banned_strategies()
    for s in r["strategies"]:
        flag = " [BAN]" if s["strategy"] in banned else ""
        lines.append(
            f"{s['strategy']:<17} {s['accounts_attempted']:>5} {s['success']:>5} "
            f"{s['success_rate_pct']:>5.1f} {s['failed']:>5} {s['captcha_accounts']:>5} "
            f"{s['captcha_rate_pct']:>5.1f} {s['avg_metadata1_len']:>8}{flag}"
        )
    if r["_worst"]:
        lines.append(f"WORST (captcha) : {r['_worst']}")
    if r["_best"]:
        lines.append(f"BEST  (exito)   : {r['_best']}")
    return lines


def reset() -> None:
    with _LOCK:
        state = {
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "total_accounts": 0,
            "banned": [],
            "strategies": {s: _blank_row() for s in _DEFAULT_STRATEGIES},
        }
        _save(state)
