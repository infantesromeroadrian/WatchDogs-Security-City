"""
Daily LLM call budget (protects the provider key from abuse and runaway loops).

Counters live in SQLite so they survive gunicorn worker recycling (``--max-requests``). They are
keyed by UTC day and by scope: ``global`` and ``user:<name>``. Each provider call reserves one
unit *before* it is made (retries included, so the cap is conservative); the API layer also does a
cheap pre-check so a request that cannot finish is rejected with 429 instead of failing half-way.
"""

from __future__ import annotations

import contextvars
import logging
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .. import config

logger = logging.getLogger(__name__)

# Who is making LLM calls. Set by the HTTP layer; contextvars propagate into LangGraph workers.
current_principal: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_principal", default=None
)


class BudgetExceeded(RuntimeError):
    """The daily call budget for a scope is exhausted."""

    def __init__(self, scope: str, limit: int, used: int) -> None:
        super().__init__(f"Daily LLM budget exhausted for {scope} ({used}/{limit})")
        self.scope = scope
        self.limit = limit
        self.used = used


def seconds_until_reset() -> int:
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())


class DailyBudget:
    """SQLite-backed per-day counters with atomic reserve."""

    def __init__(self, db_path: str, global_limit: int, per_user_limit: int) -> None:
        self.db_path = db_path
        self.global_limit = global_limit
        self.per_user_limit = per_user_limit
        self._init_lock = threading.Lock()
        self._ready = False

    def _connect(self) -> sqlite3.Connection:
        with self._init_lock:
            if not self._ready:
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
                with sqlite3.connect(self.db_path, timeout=10) as conn:
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS counters ("
                        "day TEXT NOT NULL, scope TEXT NOT NULL, calls INTEGER NOT NULL DEFAULT 0, "
                        "PRIMARY KEY (day, scope))"
                    )
                self._ready = True
        return sqlite3.connect(self.db_path, timeout=10, isolation_level=None)

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _scopes(self, principal: str | None) -> list[tuple[str, int]]:
        scopes = [("global", self.global_limit)]
        if principal:
            scopes.append((f"user:{principal}", self.per_user_limit))
        return scopes

    def used(self, scope: str = "global") -> int:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT calls FROM counters WHERE day = ? AND scope = ?", (self._today(), scope)
            ).fetchone()
        finally:
            conn.close()
        return row[0] if row else 0

    def check(self, calls: int, principal: str | None = None) -> None:
        """Raise BudgetExceeded if ``calls`` more calls would not fit (does not consume)."""
        for scope, limit in self._scopes(principal):
            used = self.used(scope)
            if used + calls > limit:
                raise BudgetExceeded(scope, limit, used)

    def reserve(self, calls: int = 1, principal: str | None = None) -> None:
        """Atomically consume ``calls`` units in every applicable scope, or raise."""
        day = self._today()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                scopes = self._scopes(principal)
                for scope, limit in scopes:
                    row = conn.execute(
                        "SELECT calls FROM counters WHERE day = ? AND scope = ?", (day, scope)
                    ).fetchone()
                    used = row[0] if row else 0
                    if used + calls > limit:
                        raise BudgetExceeded(scope, limit, used)
                for scope, _ in scopes:
                    conn.execute(
                        "INSERT INTO counters (day, scope, calls) VALUES (?, ?, ?) "
                        "ON CONFLICT(day, scope) DO UPDATE SET calls = calls + excluded.calls",
                        (day, scope, calls),
                    )
                conn.execute("DELETE FROM counters WHERE day < ?", (day,))
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()


_budget: DailyBudget | None = None


def get_budget() -> DailyBudget:
    """Process-wide budget configured from the environment."""
    global _budget
    if _budget is None:
        _budget = DailyBudget(
            config.LLM_BUDGET_DB, config.LLM_DAILY_CALL_LIMIT, config.LLM_DAILY_CALL_LIMIT_PER_USER
        )
    return _budget


def reset_budget_for_tests() -> None:
    global _budget
    _budget = None
