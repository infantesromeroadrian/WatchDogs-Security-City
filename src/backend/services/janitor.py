"""
Background janitor: enforces "nothing is kept longer than needed".

Expiry used to happen only as a side effect of new requests, so an idle server kept uploaded
videos on disk and frames in RAM indefinitely. This thread runs every minute and removes expired
sessions (frames, chat history), cached results and uploaded videos. It is started lazily from the
first request in each process (threads do not survive gunicorn's ``--preload`` fork).
"""

from __future__ import annotations

import logging
import os
import threading

from .. import config
from ..utils.cache_utils import purge_expired as purge_cache
from .session_store import session_store
from .video_service import VideoService

logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 60
_started_pid: int | None = None
_lock = threading.Lock()


def run_once() -> dict[str, int]:
    """One cleanup pass; returns counts (also used by tests)."""
    return {
        "videos": VideoService.cleanup_old_videos(config.VIDEO_RETENTION_HOURS),
        "sessions": session_store.purge_expired(),
        "cache": purge_cache(),
    }


def _loop(stop: threading.Event) -> None:
    while not stop.wait(INTERVAL_SECONDS):
        try:
            run_once()
        except Exception:  # noqa: BLE001 - the janitor must never die
            logger.exception("Janitor pass failed")


def ensure_started() -> None:
    """Start the janitor once per process (fork-safe: keyed by PID)."""
    global _started_pid
    with _lock:
        if _started_pid == os.getpid():
            return
        _started_pid = os.getpid()
        run_once()  # also clears leftovers from a previous run at start-up
        threading.Thread(target=_loop, args=(threading.Event(),), name="janitor", daemon=True).start()
        logger.info("Janitor started (retention: videos %s min)", config.VIDEO_RETENTION_MINUTES)
