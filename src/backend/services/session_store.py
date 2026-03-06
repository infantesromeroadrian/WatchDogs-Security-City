"""
Session Image Store - Server-side image persistence per session.

Single Responsibility: Store and retrieve images by session_id so that
the frontend only needs to send the image once (on initial analysis),
then reference it by session_id in subsequent chat messages.

Thread-safe, TTL-based expiration, bounded memory usage.
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_TTL_SECONDS = 3600  # 1 hour
DEFAULT_MAX_SESSIONS = 100
DEFAULT_MAX_IMAGES_PER_SESSION = 20


@dataclass
class SessionImage:
    """A single stored image within a session."""

    image_base64: str
    description: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionData:
    """All data associated with a session."""

    session_id: str
    thread_id: str
    images: dict[str, SessionImage] = field(default_factory=dict)
    analysis_results: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def touch(self) -> None:
        """Update last_accessed timestamp."""
        self.last_accessed = time.time()

    @property
    def is_expired(self) -> bool:
        """Check if session has expired based on TTL."""
        return (time.time() - self.last_accessed) > DEFAULT_TTL_SECONDS


class SessionImageStore:
    """
    Thread-safe in-memory store for session images.

    Stores base64 images per session so they don't need to be
    re-transmitted on every chat message. Includes TTL-based
    expiration and bounded memory usage.

    Usage:
        store = SessionImageStore()

        # On initial analysis — store the image
        session_id = store.create_session()
        image_id = store.store_image(session_id, base64_data, "Frame from video")

        # On subsequent chat — retrieve without re-sending
        image = store.get_image(session_id, image_id)
        all_images = store.get_session_images(session_id)
    """

    def __init__(
        self,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        max_images_per_session: int = DEFAULT_MAX_IMAGES_PER_SESSION,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """
        Initialize the session store.

        Args:
            max_sessions: Maximum concurrent sessions before evicting oldest.
            max_images_per_session: Maximum images stored per session.
            ttl_seconds: Time-to-live for inactive sessions in seconds.
        """
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.Lock()
        self._max_sessions = max_sessions
        self._max_images_per_session = max_images_per_session
        self._ttl_seconds = ttl_seconds

        logger.info(
            "SessionImageStore initialized (max_sessions=%s, max_images=%s, ttl=%ss)",
            max_sessions,
            max_images_per_session,
            ttl_seconds,
        )

    def create_session(self, thread_id: str | None = None) -> str:
        """
        Create a new session and return its ID.

        Args:
            thread_id: Optional LangGraph thread_id to associate.
                If None, generates one matching the session_id.

        Returns:
            The new session_id string.
        """
        session_id = str(uuid.uuid4())
        if thread_id is None:
            thread_id = session_id

        with self._lock:
            self._evict_expired()
            self._evict_if_full()

            self._sessions[session_id] = SessionData(
                session_id=session_id,
                thread_id=thread_id,
            )

        logger.info("Session created: %s (thread=%s)", session_id[:8], thread_id[:8])
        return session_id

    def store_image(
        self,
        session_id: str,
        image_base64: str,
        description: str = "",
    ) -> str:
        """
        Store an image in the session and return its image_id.

        Args:
            session_id: The session to store the image in.
            image_base64: Base64 encoded image data.
            description: Optional description for the image.

        Returns:
            The image_id string for later retrieval.

        Raises:
            KeyError: If session_id does not exist.
            ValueError: If session has reached max images.
        """
        image_id = str(uuid.uuid4())

        with self._lock:
            session = self._get_session_or_raise(session_id)

            if len(session.images) >= self._max_images_per_session:
                msg = (
                    f"Session {session_id[:8]} has reached max images "
                    f"({self._max_images_per_session})"
                )
                raise ValueError(msg)

            session.images[image_id] = SessionImage(
                image_base64=image_base64,
                description=description,
            )
            session.touch()

        logger.info(
            "Image stored: %s in session %s (%s bytes)",
            image_id[:8],
            session_id[:8],
            len(image_base64),
        )
        return image_id

    def get_image(self, session_id: str, image_id: str) -> SessionImage:
        """
        Retrieve a specific image from a session.

        Args:
            session_id: The session containing the image.
            image_id: The image to retrieve.

        Returns:
            The SessionImage object.

        Raises:
            KeyError: If session or image does not exist.
        """
        with self._lock:
            session = self._get_session_or_raise(session_id)
            session.touch()

            if image_id not in session.images:
                msg = f"Image {image_id[:8]} not found in session {session_id[:8]}"
                raise KeyError(msg)

            return session.images[image_id]

    def get_session_images(self, session_id: str) -> dict[str, SessionImage]:
        """
        Retrieve all images in a session.

        Args:
            session_id: The session to query.

        Returns:
            Dict mapping image_id to SessionImage.

        Raises:
            KeyError: If session does not exist.
        """
        with self._lock:
            session = self._get_session_or_raise(session_id)
            session.touch()
            return dict(session.images)

    def get_session(self, session_id: str) -> SessionData:
        """
        Retrieve the full session data.

        Args:
            session_id: The session to query.

        Returns:
            The SessionData object.

        Raises:
            KeyError: If session does not exist.
        """
        with self._lock:
            session = self._get_session_or_raise(session_id)
            session.touch()
            return session

    def get_thread_id(self, session_id: str) -> str:
        """
        Get the LangGraph thread_id associated with a session.

        Args:
            session_id: The session to query.

        Returns:
            The thread_id string.

        Raises:
            KeyError: If session does not exist.
        """
        with self._lock:
            session = self._get_session_or_raise(session_id)
            session.touch()
            return session.thread_id

    def store_analysis_result(
        self,
        session_id: str,
        result: dict[str, Any],
        key: str = "latest",
    ) -> None:
        """
        Store an analysis result in the session for later reference.

        Args:
            session_id: The session to store in.
            result: The analysis result dict.
            key: Storage key (e.g. "latest", "frame_1").

        Raises:
            KeyError: If session does not exist.
        """
        with self._lock:
            session = self._get_session_or_raise(session_id)
            session.analysis_results[key] = result
            session.touch()

    def get_analysis_result(self, session_id: str, key: str = "latest") -> dict[str, Any] | None:
        """
        Retrieve a stored analysis result.

        Args:
            session_id: The session to query.
            key: The result key to retrieve.

        Returns:
            The analysis result dict, or None if not found.

        Raises:
            KeyError: If session does not exist.
        """
        with self._lock:
            session = self._get_session_or_raise(session_id)
            session.touch()
            return session.analysis_results.get(key)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists and is not expired."""
        with self._lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            if session.is_expired:
                del self._sessions[session_id]
                return False
            return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its data.

        Args:
            session_id: The session to delete.

        Returns:
            True if session was deleted, False if not found.
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info("Session deleted: %s", session_id[:8])
                return True
            return False

    @property
    def active_session_count(self) -> int:
        """Return the number of active (non-expired) sessions."""
        with self._lock:
            self._evict_expired()
            return len(self._sessions)

    # --- Private helpers (must be called under lock) ---

    def _get_session_or_raise(self, session_id: str) -> SessionData:
        """Get session or raise KeyError. Caller must hold lock."""
        if session_id not in self._sessions:
            msg = f"Session {session_id[:8]} not found"
            raise KeyError(msg)

        session = self._sessions[session_id]
        if session.is_expired:
            del self._sessions[session_id]
            msg = f"Session {session_id[:8]} has expired"
            raise KeyError(msg)

        return session

    def _evict_expired(self) -> None:
        """Remove all expired sessions. Caller must hold lock."""
        expired = [
            sid
            for sid, session in self._sessions.items()
            if (time.time() - session.last_accessed) > self._ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug("Evicted expired session: %s", sid[:8])

    def _evict_if_full(self) -> None:
        """Evict oldest session if at capacity. Caller must hold lock."""
        while len(self._sessions) >= self._max_sessions:
            # Evict least recently accessed
            oldest_sid = min(
                self._sessions,
                key=lambda sid: self._sessions[sid].last_accessed,
            )
            del self._sessions[oldest_sid]
            logger.info("Evicted oldest session: %s (at capacity)", oldest_sid[:8])


# Module-level singleton for use across the application
session_store = SessionImageStore()
