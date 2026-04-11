"""
Crawler Manager – Orchestrates DZA tariff crawl sessions.

Responsibilities:
- Launch and track async crawl sessions
- Coordinate the Crawl → Parse → Build → Integrate pipeline
- Expose session status for API layer
- Manage output file lifecycle
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.crawler_config import get_crawler_config, get_quality_config
from services.crawlers.dza_tariff_connector import DZATariffConnector
from services.crawlers.data_validator import DataValidator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

class CrawlSession:
    """Represents a single DZA crawl session."""

    def __init__(self, session_id: str, config_overrides: Optional[Dict[str, Any]] = None) -> None:
        self.session_id = session_id
        self.config_overrides = config_overrides or {}
        self.status: str = "pending"  # pending | running | completed | failed | stopped
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.crawl_stats: Dict[str, Any] = {}
        self.validation_report: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self._connector: Optional[DZATariffConnector] = None

    @property
    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "crawl_stats": self.crawl_stats,
            "validation_passed": self.validation_report.get("passed"),
            "error": self.error,
        }

    def stop(self) -> None:
        if self._connector:
            self._connector.stop()
        self.status = "stopping"


# ---------------------------------------------------------------------------
# Crawler Manager
# ---------------------------------------------------------------------------

class CrawlerManager:
    """
    Singleton manager that orchestrates DZA crawl sessions.
    Exposes start/stop/status operations used by the API layer.
    """

    _instance: Optional[CrawlerManager] = None

    def __new__(cls) -> CrawlerManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: Dict[str, CrawlSession] = {}
            cls._instance._active_task: Optional[asyncio.Task] = None  # type: ignore[assignment]
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(self, config_overrides: Optional[Dict[str, Any]] = None) -> CrawlSession:
        """Create a new crawl session and schedule it for execution."""
        session_id = str(uuid.uuid4())
        session = CrawlSession(session_id=session_id, config_overrides=config_overrides)
        self._sessions[session_id] = session

        # Schedule async pipeline
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self._active_task = loop.create_task(self._run_pipeline(session))
        logger.info(f"DZA crawl session {session_id} scheduled.")
        return session

    def stop_session(self, session_id: str) -> bool:
        """Stop a running session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.stop()
        return True

    def get_session(self, session_id: str) -> Optional[CrawlSession]:
        return self._sessions.get(session_id)

    def get_active_session(self) -> Optional[CrawlSession]:
        """Return the most recently created session."""
        if not self._sessions:
            return None
        return list(self._sessions.values())[-1]

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        return [s.summary for s in self._sessions.values()]

    def get_stats(self) -> Dict[str, Any]:
        sessions = list(self._sessions.values())
        return {
            "total_sessions": len(sessions),
            "running": sum(1 for s in sessions if s.status == "running"),
            "completed": sum(1 for s in sessions if s.status == "completed"),
            "failed": sum(1 for s in sessions if s.status == "failed"),
        }

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    async def _run_pipeline(self, session: CrawlSession) -> None:
        """Execute the full Crawl → Validate pipeline for a session."""
        cfg = get_crawler_config()
        qcfg = get_quality_config()

        # Apply overrides
        for key, val in session.config_overrides.items():
            if hasattr(cfg, key):
                setattr(cfg, key, val)

        session.status = "running"
        session.started_at = datetime.now(timezone.utc).isoformat()

        try:
            # --- Phase 1: Crawl ---
            connector = DZATariffConnector(
                base_url=cfg.base_url,
                max_workers=cfg.max_workers,
                rate_limit_delay=cfg.rate_limit_delay,
                max_retries=cfg.max_retries,
                retry_delay=cfg.retry_delay,
                request_timeout=cfg.request_timeout,
                max_pages=cfg.max_pages,
                output_dir=cfg.raw_dir,
            )
            session._connector = connector
            await connector.run()

            session.crawl_stats = connector.get_stats()
            tariff_lines = connector.get_results()

            # --- Phase 2: Validate ---
            validator = DataValidator(
                min_confidence_score=qcfg.min_confidence_score,
                min_vat_coverage=qcfg.min_vat_coverage,
                min_hs10_coverage=qcfg.min_hs10_coverage,
                strict_mode=qcfg.strict_mode,
            )
            session.validation_report = validator.validate(tariff_lines)

            # --- Phase 3: Build / Publish ---
            if tariff_lines:
                await self._publish(tariff_lines, session, cfg)

            session.status = "completed"

        except Exception as exc:
            logger.exception(f"Pipeline failed for session {session.session_id}: {exc}")
            session.status = "failed"
            session.error = str(exc)
        finally:
            session.finished_at = datetime.now(timezone.utc).isoformat()

    async def _publish(
        self,
        lines: List[Dict[str, Any]],
        session: CrawlSession,
        cfg: Any,
    ) -> None:
        """Write parsed and published datasets."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Parsed output
        parsed_file = cfg.parsed_dir / f"dza_parsed_{ts}.json"
        payload = {
            "session_id": session.session_id,
            "country": "DZA",
            "generated_at": ts,
            "total_lines": len(lines),
            "tariff_lines": lines,
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: parsed_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            ),
        )

        # Published (curated) output – only lines that passed validation
        good_lines = [ln for ln in lines if ln.get("confidence_score", 0) >= 0.5]
        published_file = cfg.published_dir / f"dza_published_{ts}.json"
        pub_payload = {**payload, "tariff_lines": good_lines, "total_lines": len(good_lines)}
        await loop.run_in_executor(
            None,
            lambda: published_file.write_text(
                json.dumps(pub_payload, ensure_ascii=False, indent=2), encoding="utf-8"
            ),
        )
        logger.info(
            f"Session {session.session_id}: published {len(good_lines)}/{len(lines)} lines."
        )


# Singleton accessor
def get_crawler_manager() -> CrawlerManager:
    return CrawlerManager()
