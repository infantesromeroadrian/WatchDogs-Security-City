"""WatchDogs Security City — Entry point."""

import sys


def main() -> None:
    """Launch the WatchDogs OSINT Flask server."""
    from src.backend.app import run_server

    run_server()


if __name__ == "__main__":
    sys.exit(main() or 0)
