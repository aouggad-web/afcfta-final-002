"""
Exchange rate update scheduler.

Uses a background daemon thread to periodically refresh exchange rates
from the configured provider chain. By default, updates run every 4 hours
with an immediate update on startup.

Daily updates at 06:00 UTC can be achieved by setting ``interval_hours=24``
and deploying with a process manager that starts the server after 06:00 UTC.

Start from server.py startup event:

    from tasks.scheduler import start_scheduler
    start_scheduler()
"""
import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _run_update() -> None:
    """Trigger an exchange rate update and log the outcome."""
    try:
        from exchange_rates.service import get_service

        svc = get_service()
        bundle = svc.update_rates("USD")
        if bundle:
            logger.info(
                "Scheduled rate update completed: %d pairs from %s at %s",
                len(bundle.rates),
                bundle.source,
                bundle.timestamp.isoformat(),
            )
        else:
            logger.warning("Scheduled rate update failed: all providers returned None")
    except Exception as exc:
        logger.error("Unhandled error in scheduled rate update: %s", exc, exc_info=True)


def _scheduler_loop(interval_seconds: int) -> None:
    """Background loop: wake every *interval_seconds* seconds and run update."""
    import time

    logger.info("Exchange rate scheduler started (interval=%ds)", interval_seconds)
    # Run once immediately on start
    _run_update()
    while not _stop_event.is_set():
        _stop_event.wait(timeout=interval_seconds)
        if not _stop_event.is_set():
            _run_update()
    logger.info("Exchange rate scheduler stopped")


def start_scheduler(interval_hours: int = 4) -> None:
    """Start the background scheduler thread.

    Args:
        interval_hours: How often to refresh rates. Defaults to every 4 hours.
            The first update runs immediately on startup.
    """
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.debug("Scheduler already running; skipping start")
        return
    _stop_event.clear()
    interval_seconds = interval_hours * 3600
    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        args=(interval_seconds,),
        name="exchange-rate-scheduler",
        daemon=True,
    )
    _scheduler_thread.start()
    logger.info("Exchange rate scheduler thread started")


def stop_scheduler() -> None:
    """Signal the scheduler thread to stop gracefully."""
    _stop_event.set()
    if _scheduler_thread:
        _scheduler_thread.join(timeout=5)
    logger.info("Exchange rate scheduler stopped")
