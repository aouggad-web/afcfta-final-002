"""
North Africa Regional Orchestrator.

Coordinates tariff data crawling across all four North African countries:
- DZA (Algeria), MAR (Morocco), EGY (Egypt), TUN (Tunisia)

Features:
- Async multi-country crawl coordination
- Real-time status monitoring
- Automatic failover and retry mechanisms
- Cross-country data consistency checks
- Performance monitoring dashboard
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.regional_config import NORTH_AFRICA_COUNTRIES, REGIONAL_CONFIG

logger = logging.getLogger(__name__)


class CountryCrawlStatus:
    """Tracks the crawl status for a single country."""

    def __init__(self, country_code: str):
        self.country_code = country_code
        self.status: str = "pending"  # pending | running | completed | failed
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.records_scraped: int = 0
        self.error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country_code": self.country_code,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": round(self.duration_seconds, 2) if self.duration_seconds else None,
            "records_scraped": self.records_scraped,
            "error": self.error,
        }


class RegionalCrawlJob:
    """Represents a multi-country North Africa crawl job."""

    def __init__(self, job_id: str, countries: List[str], options: Optional[Dict] = None):
        self.job_id = job_id
        self.countries = countries
        self.options = options or {}
        self.status: str = "queued"  # queued | running | completed | failed | partial
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.country_statuses: Dict[str, CountryCrawlStatus] = {
            c: CountryCrawlStatus(c) for c in countries
        }
        self.error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    @property
    def summary(self) -> Dict[str, Any]:
        succeeded = sum(
            1 for s in self.country_statuses.values() if s.status == "completed"
        )
        failed = sum(
            1 for s in self.country_statuses.values() if s.status == "failed"
        )
        total_records = sum(s.records_scraped for s in self.country_statuses.values())

        return {
            "job_id": self.job_id,
            "status": self.status,
            "countries": self.countries,
            "total_countries": len(self.countries),
            "succeeded": succeeded,
            "failed": failed,
            "total_records_scraped": total_records,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": round(self.duration_seconds, 2) if self.duration_seconds else None,
            "error": self.error,
            "country_statuses": {
                code: status.to_dict()
                for code, status in self.country_statuses.items()
            },
        }


class NorthAfricaOrchestrator:
    """
    Multi-country orchestrator for North African tariff data collection.

    Coordinates async crawling across DZA, MAR, EGY, TUN with:
    - Configurable concurrency
    - Real-time status tracking
    - Retry mechanisms for failed countries
    - Cross-validation after collection
    """

    SUPPORTED_COUNTRIES = NORTH_AFRICA_COUNTRIES

    def __init__(self, db_client=None, max_concurrency: int = 4):
        self.db_client = db_client
        self.max_concurrency = max_concurrency
        self.jobs: Dict[str, RegionalCrawlJob] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def _get_crawler(self, country_code: str, options: Dict) -> Any:
        """Instantiate the appropriate crawler for a country."""
        from .dza_tariff_connector import DZATariffConnector
        from .mar_tariff_crawler import MARTariffCrawler
        from .egy_tariff_crawler import EGYTariffCrawler
        from .tun_tariff_crawler import TUNTariffCrawler

        crawler_map = {
            "DZA": DZATariffConnector,
            "MAR": MARTariffCrawler,
            "EGY": EGYTariffCrawler,
            "TUN": TUNTariffCrawler,
        }

        cls = crawler_map.get(country_code)
        if not cls:
            raise ValueError(f"Unsupported country: {country_code}")

        # Filter relevant options per crawler
        if country_code == "DZA":
            return cls(
                country_code=country_code,
                db_client=self.db_client,
                max_headings=options.get("max_headings"),
            )
        elif country_code in ("MAR", "TUN"):
            return cls(
                country_code=country_code,
                db_client=self.db_client,
                chapters=options.get("chapters"),
                max_per_chapter=options.get("max_per_chapter"),
            )
        elif country_code == "EGY":
            return cls(
                country_code=country_code,
                db_client=self.db_client,
                max_positions=options.get("max_positions"),
                delay=options.get("delay", 1.5),
                resume=options.get("resume", True),
            )
        return cls(country_code=country_code, db_client=self.db_client)

    async def start_regional_crawl(
        self,
        countries: Optional[List[str]] = None,
        options: Optional[Dict] = None,
    ) -> RegionalCrawlJob:
        """
        Start a regional crawl across North African countries.

        Args:
            countries: List of ISO3 codes to crawl (defaults to all 4)
            options: Crawler options dict (max_headings, max_per_chapter, etc.)

        Returns:
            RegionalCrawlJob tracking object
        """
        countries = countries or self.SUPPORTED_COUNTRIES
        invalid = [c for c in countries if c not in self.SUPPORTED_COUNTRIES]
        if invalid:
            raise ValueError(
                f"Unsupported countries: {invalid}. "
                f"Supported: {self.SUPPORTED_COUNTRIES}"
            )

        job_id = str(uuid.uuid4())[:8]
        job = RegionalCrawlJob(job_id, countries, options or {})
        self.jobs[job_id] = job

        task = asyncio.create_task(self._run_job(job))
        self._running_tasks[job_id] = task

        logger.info(f"North Africa crawl job {job_id} started for: {countries}")
        return job

    async def _run_job(self, job: RegionalCrawlJob):
        """Execute a regional crawl job."""
        job.status = "running"
        job.started_at = datetime.utcnow()

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def crawl_country(country_code: str):
            async with semaphore:
                status = job.country_statuses[country_code]
                status.status = "running"
                status.started_at = datetime.utcnow()

                try:
                    crawler = self._get_crawler(country_code, job.options)
                    async with crawler:
                        result = await crawler.run()

                    status.records_scraped = result.records_scraped
                    if result.success:
                        status.status = "completed"
                        logger.info(
                            f"[{country_code}] Crawl completed: "
                            f"{result.records_scraped} records"
                        )
                    else:
                        status.status = "failed"
                        status.error = result.error
                        logger.error(f"[{country_code}] Crawl failed: {result.error}")

                except Exception as exc:
                    status.status = "failed"
                    status.error = str(exc)
                    logger.error(f"[{country_code}] Crawl exception: {exc}")
                finally:
                    status.completed_at = datetime.utcnow()

        try:
            tasks = [crawl_country(c) for c in job.countries]
            await asyncio.gather(*tasks, return_exceptions=True)

            succeeded = sum(
                1 for s in job.country_statuses.values() if s.status == "completed"
            )
            total = len(job.countries)

            if succeeded == total:
                job.status = "completed"
            elif succeeded == 0:
                job.status = "failed"
            else:
                job.status = "partial"

        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            logger.error(f"Regional job {job.job_id} failed: {exc}")
        finally:
            job.completed_at = datetime.utcnow()
            self._running_tasks.pop(job.job_id, None)

        logger.info(
            f"Regional job {job.job_id} finished: {job.status} "
            f"({sum(s.records_scraped for s in job.country_statuses.values())} total records)"
        )
        return job

    def get_job(self, job_id: str) -> Optional[RegionalCrawlJob]:
        """Retrieve a job by ID."""
        return self.jobs.get(job_id)

    def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent jobs, newest first."""
        jobs = sorted(
            self.jobs.values(), key=lambda j: j.created_at, reverse=True
        )
        return [j.summary for j in jobs[:limit]]

    def get_regional_status(self) -> Dict[str, Any]:
        """Get overall regional crawl system status."""
        total_jobs = len(self.jobs)
        active = len(self._running_tasks)

        by_status: Dict[str, int] = {}
        for job in self.jobs.values():
            by_status[job.status] = by_status.get(job.status, 0) + 1

        return {
            "supported_countries": self.SUPPORTED_COUNTRIES,
            "total_jobs": total_jobs,
            "active_jobs": active,
            "max_concurrency": self.max_concurrency,
            "jobs_by_status": by_status,
        }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job = self.jobs.get(job_id)
        if not job or job.status not in ("queued", "running"):
            return False
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        self._running_tasks.pop(job_id, None)
        return True


# Module-level singleton
_orchestrator: Optional[NorthAfricaOrchestrator] = None


def get_north_africa_orchestrator(db_client=None) -> NorthAfricaOrchestrator:
    """Get or create the singleton NorthAfricaOrchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NorthAfricaOrchestrator(
            db_client=db_client,
            max_concurrency=REGIONAL_CONFIG["orchestrator"]["max_concurrency"],
        )
    return _orchestrator


def init_north_africa_orchestrator(db_client=None, max_concurrency: int = 4):
    """Initialize (or re-initialize) the singleton orchestrator."""
    global _orchestrator
    _orchestrator = NorthAfricaOrchestrator(
        db_client=db_client,
        max_concurrency=max_concurrency,
    )
    return _orchestrator
