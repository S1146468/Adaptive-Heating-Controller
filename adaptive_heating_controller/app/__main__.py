"""Idle until stopped: this foundation deliberately has no external I/O."""

import logging
import signal
import threading

from app import __version__


def main() -> None:
    """Log lifecycle events and wait without polling or heartbeat messages."""
    stopped = threading.Event()

    def stop(_signum: int, _frame: object) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("Adaptive Heating Controller %s started (mode=read-only)", __version__)
    stopped.wait()
    logging.info("Adaptive Heating Controller %s stopped gracefully (mode=read-only)", __version__)


if __name__ == "__main__":
    main()
