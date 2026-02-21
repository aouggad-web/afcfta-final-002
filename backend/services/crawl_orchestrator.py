import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class CrawlJob:
    def __init__(self, job_id: str, country_codes: List[str], options: Optional[Dict] = None):
        self.job_id = job_id
        self.country_codes = country_codes
        self.options = options or {}
        self.status = JobStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.country_results: Dict[str, Dict[str, Any]] = {}
        self.error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    @property
    def summary(self) -> Dict[str, Any]:
        succeeded = sum(1 for r in self.country_results.values() if r.get("success"))
        failed = sum(1 for r in self.country_results.values() if not r.get("success"))
        pending = len(self.country_codes) - len(self.country_results)

        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "total_countries": len(self.country_codes),
            "succeeded": succeeded,
            "failed": failed,
            "pending": pending,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": round(self.duration_seconds, 2) if self.duration_seconds else None,
            "error": self.error,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary,
            "country_codes": self.country_codes,
            "options": self.options,
            "country_results": self.country_results,
        }


class CrawlOrchestrator:
    def __init__(self, db_client=None, notification_manager=None, max_concurrency: int = 5):
        self.db_client = db_client
        self.notification_manager = notification_manager
        self.max_concurrency = max_concurrency
        self.jobs: Dict[str, CrawlJob] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def start_crawl(
        self,
        country_codes: List[str],
        priority: Optional[str] = None,
        region: Optional[str] = None,
        block: Optional[str] = None,
        force_generic: bool = False,
    ) -> CrawlJob:
        from crawlers.scraper_factory import ScraperFactory
        from crawlers.all_countries_registry import (
            AFRICAN_COUNTRIES_REGISTRY,
            get_priority_countries,
            get_countries_by_region,
            get_countries_by_block,
            Priority,
            Region,
            RegionalBlock,
        )

        if country_codes:
            codes = [c.upper() for c in country_codes]
            invalid = [c for c in codes if c not in AFRICAN_COUNTRIES_REGISTRY]
            if invalid:
                raise ValueError(f"Invalid country codes: {invalid}")
        elif priority:
            p = Priority[priority.upper()]
            codes = get_priority_countries(p)
        elif region:
            r = Region[region.upper().replace(" ", "_")]
            codes = get_countries_by_region(r)
        elif block:
            b = RegionalBlock[block.upper()]
            codes = get_countries_by_block(b)
        else:
            codes = list(AFRICAN_COUNTRIES_REGISTRY.keys())

        job_id = str(uuid.uuid4())[:8]
        job = CrawlJob(job_id, codes, {
            "force_generic": force_generic,
            "priority": priority,
            "region": region,
            "block": block,
        })
        self.jobs[job_id] = job

        task = asyncio.create_task(self._run_job(job, force_generic))
        self._running_tasks[job_id] = task

        logger.info(f"Crawl job {job_id} created for {len(codes)} countries")
        return job

    async def _run_job(self, job: CrawlJob, force_generic: bool = False):
        from crawlers.scraper_factory import ScraperFactory

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()

        if self.notification_manager:
            try:
                await self.notification_manager.send_notification(
                    notification_type=self._get_notification_type("started"),
                    severity=self._get_severity("info"),
                    subject=f"Crawl Job {job.job_id} Started",
                    message=f"Starting crawl for {len(job.country_codes)} countries.",
                    metadata={"job_id": job.job_id, "countries": len(job.country_codes)},
                )
            except Exception as e:
                logger.warning(f"Failed to send start notification: {e}")

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def crawl_country(country_code: str):
            async with semaphore:
                try:
                    scraper = ScraperFactory.get_scraper(
                        country_code,
                        db_client=self.db_client,
                        force_generic=force_generic,
                    )
                    async with scraper:
                        result = await scraper.run()

                    job.country_results[country_code] = {
                        "success": result.success,
                        "records_scraped": result.records_scraped,
                        "records_validated": result.records_validated,
                        "records_saved": result.records_saved,
                        "duration_seconds": round(result.duration_seconds, 2) if result.duration_seconds else None,
                        "error": result.error,
                    }
                except Exception as e:
                    logger.error(f"Crawl failed for {country_code}: {e}")
                    job.country_results[country_code] = {
                        "success": False,
                        "error": str(e),
                        "records_scraped": 0,
                    }

        try:
            tasks = [crawl_country(code) for code in job.country_codes]
            await asyncio.gather(*tasks, return_exceptions=True)

            succeeded = sum(1 for r in job.country_results.values() if r.get("success"))
            total = len(job.country_codes)

            if succeeded == total:
                job.status = JobStatus.COMPLETED
            elif succeeded == 0:
                job.status = JobStatus.FAILED
            else:
                job.status = JobStatus.PARTIAL

        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)

        finally:
            job.completed_at = datetime.utcnow()
            self._running_tasks.pop(job.job_id, None)

            if self.notification_manager:
                try:
                    summary = job.summary
                    severity = "info" if job.status == JobStatus.COMPLETED else "error" if job.status == JobStatus.FAILED else "warning"
                    notif_type = "success" if job.status == JobStatus.COMPLETED else "failed"

                    await self.notification_manager.send_notification(
                        notification_type=self._get_notification_type(notif_type),
                        severity=self._get_severity(severity),
                        subject=f"Crawl Job {job.job_id} {job.status.value.title()}",
                        message=(
                            f"Crawl job completed: {summary['succeeded']}/{summary['total_countries']} succeeded, "
                            f"{summary['failed']} failed. Duration: {summary['duration_seconds']}s"
                        ),
                        metadata={
                            "job_id": job.job_id,
                            "status": job.status.value,
                            "succeeded": summary["succeeded"],
                            "failed": summary["failed"],
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to send completion notification: {e}")

        logger.info(f"Job {job.job_id} finished with status: {job.status.value}")
        return job

    def cancel_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING):
            return False

        task = self._running_tasks.get(job_id)
        if task and not task.done():
            task.cancel()

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        self._running_tasks.pop(job_id, None)
        return True

    def get_job(self, job_id: str) -> Optional[CrawlJob]:
        return self.jobs.get(job_id)

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.summary for j in jobs[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.jobs)
        by_status = {}
        for job in self.jobs.values():
            by_status[job.status.value] = by_status.get(job.status.value, 0) + 1

        return {
            "total_jobs": total,
            "by_status": by_status,
            "active_tasks": len(self._running_tasks),
            "max_concurrency": self.max_concurrency,
        }

    def _get_notification_type(self, type_str: str):
        from notifications.base_notifier import NotificationType
        type_map = {
            "started": NotificationType.CRAWL_STARTED,
            "success": NotificationType.CRAWL_SUCCESS,
            "failed": NotificationType.CRAWL_FAILED,
        }
        return type_map.get(type_str, NotificationType.CRAWL_STARTED)

    def _get_severity(self, severity_str: str):
        from notifications.base_notifier import NotificationSeverity
        sev_map = {
            "info": NotificationSeverity.INFO,
            "warning": NotificationSeverity.WARNING,
            "error": NotificationSeverity.ERROR,
        }
        return sev_map.get(severity_str, NotificationSeverity.INFO)


crawl_orchestrator: Optional[CrawlOrchestrator] = None


def get_orchestrator() -> CrawlOrchestrator:
    global crawl_orchestrator
    if crawl_orchestrator is None:
        crawl_orchestrator = CrawlOrchestrator()
    return crawl_orchestrator


def init_orchestrator(db_client=None, notification_manager=None, max_concurrency: int = 5):
    global crawl_orchestrator
    crawl_orchestrator = CrawlOrchestrator(
        db_client=db_client,
        notification_manager=notification_manager,
        max_concurrency=max_concurrency,
    )
    return crawl_orchestrator
