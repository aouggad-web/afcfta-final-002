"""
Notification Manager

Centralized manager for all notification channels.
Handles sending notifications to multiple channels simultaneously.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_notifier import (
    BaseNotifier,
    NotificationData,
    NotificationType,
    NotificationSeverity,
)
from .email_notifier import EmailNotifier
from .slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Centralized notification manager for the AfCFTA crawler.
    
    Manages multiple notification channels and provides convenient methods
    for common notification scenarios.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize notification manager with all available notifiers.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize all notifiers
        self.notifiers: List[BaseNotifier] = [
            EmailNotifier(config),
            SlackNotifier(config),
        ]
        
        # Filter to enabled notifiers only
        self.enabled_notifiers = [n for n in self.notifiers if n.is_enabled()]
        
        if not self.enabled_notifiers:
            logger.warning("No notification channels are enabled")
        else:
            enabled_names = [n.__class__.__name__ for n in self.enabled_notifiers]
            logger.info(f"Enabled notification channels: {', '.join(enabled_names)}")
        
        # Statistics
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "by_type": {},
            "last_notification": None,
        }
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        severity: NotificationSeverity,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notification to all enabled channels.
        
        Args:
            notification_type: Type of notification
            severity: Severity level
            subject: Notification subject
            message: Notification message
            metadata: Optional metadata dictionary
            
        Returns:
            Dict mapping notifier names to success status
        """
        if not self.enabled_notifiers:
            logger.debug("No enabled notifiers, skipping notification")
            return {}
        
        data = NotificationData(
            notification_type=notification_type,
            severity=severity,
            subject=subject,
            message=message,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
        )
        
        # Send to all notifiers concurrently
        tasks = [
            self._send_to_notifier(notifier, data)
            for notifier in self.enabled_notifiers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        result_map = {}
        for notifier, result in zip(self.enabled_notifiers, results):
            notifier_name = notifier.__class__.__name__
            
            if isinstance(result, Exception):
                logger.error(f"{notifier_name} failed with exception: {result}")
                result_map[notifier_name] = False
                self.stats["total_failed"] += 1
            else:
                result_map[notifier_name] = result
                if result:
                    self.stats["total_sent"] += 1
                else:
                    self.stats["total_failed"] += 1
        
        # Update statistics
        type_key = notification_type.value
        if type_key not in self.stats["by_type"]:
            self.stats["by_type"][type_key] = {"sent": 0, "failed": 0}
        
        success_count = sum(1 for v in result_map.values() if v)
        if success_count > 0:
            self.stats["by_type"][type_key]["sent"] += 1
            self.stats["last_notification"] = datetime.utcnow().isoformat()
        else:
            self.stats["by_type"][type_key]["failed"] += 1
        
        return result_map
    
    async def _send_to_notifier(self, notifier: BaseNotifier, data: NotificationData) -> bool:
        """
        Send notification to a specific notifier with error handling.
        
        Args:
            notifier: The notifier to use
            data: Notification data
            
        Returns:
            bool: Success status
        """
        try:
            return await notifier.send_notification(data)
        except Exception as e:
            logger.error(f"Error sending notification via {notifier.__class__.__name__}: {e}")
            return False
    
    async def notify_crawl_start(
        self,
        job_id: str,
        country_code: str,
        country_name: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Notify that a crawl job has started.
        
        Args:
            job_id: Unique job identifier
            country_code: ISO country code
            country_name: Optional country name
            
        Returns:
            Dict mapping notifier names to success status
        """
        subject = f"Crawl Started: {country_name or country_code}"
        message = f"Data collection has started for {country_name or country_code} ({country_code})."
        
        metadata = {
            "job_id": job_id,
            "country_code": country_code,
            "status": "started",
        }
        if country_name:
            metadata["country_name"] = country_name
        
        return await self.send_notification(
            NotificationType.CRAWL_STARTED,
            NotificationSeverity.INFO,
            subject,
            message,
            metadata,
        )
    
    async def notify_crawl_success(
        self,
        job_id: str,
        country_code: str,
        country_name: Optional[str] = None,
        stats: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[float] = None,
    ) -> Dict[str, bool]:
        """
        Notify that a crawl job completed successfully.
        
        Args:
            job_id: Unique job identifier
            country_code: ISO country code
            country_name: Optional country name
            stats: Optional statistics dictionary
            duration_seconds: Optional duration in seconds
            
        Returns:
            Dict mapping notifier names to success status
        """
        subject = f"Crawl Successful: {country_name or country_code}"
        
        message_parts = [
            f"Data collection completed successfully for {country_name or country_code} ({country_code})."
        ]
        
        if stats:
            if "items_scraped" in stats:
                message_parts.append(f"Items collected: {stats['items_scraped']}")
            if "validation_score" in stats:
                message_parts.append(f"Validation score: {stats['validation_score']}")
        
        if duration_seconds:
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            message_parts.append(f"Duration: {minutes}m {seconds}s")
        
        message = "\n".join(message_parts)
        
        metadata = {
            "job_id": job_id,
            "country_code": country_code,
            "status": "success",
        }
        if country_name:
            metadata["country_name"] = country_name
        if duration_seconds:
            metadata["duration_seconds"] = f"{duration_seconds:.2f}"
        if stats:
            metadata.update(stats)
        
        return await self.send_notification(
            NotificationType.CRAWL_SUCCESS,
            NotificationSeverity.INFO,
            subject,
            message,
            metadata,
        )
    
    async def notify_crawl_failed(
        self,
        job_id: str,
        country_code: str,
        country_name: Optional[str] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> Dict[str, bool]:
        """
        Notify that a crawl job failed.
        
        Args:
            job_id: Unique job identifier
            country_code: ISO country code
            country_name: Optional country name
            error: Optional error message
            error_type: Optional error type/category
            duration_seconds: Optional duration before failure
            
        Returns:
            Dict mapping notifier names to success status
        """
        subject = f"Crawl Failed: {country_name or country_code}"
        
        message_parts = [
            f"Data collection failed for {country_name or country_code} ({country_code})."
        ]
        
        if error_type:
            message_parts.append(f"Error type: {error_type}")
        
        if error:
            message_parts.append(f"Error details: {error}")
        
        message = "\n".join(message_parts)
        
        metadata = {
            "job_id": job_id,
            "country_code": country_code,
            "status": "failed",
        }
        if country_name:
            metadata["country_name"] = country_name
        if error_type:
            metadata["error_type"] = error_type
        if error:
            metadata["error_message"] = error
        if duration_seconds:
            metadata["duration_seconds"] = f"{duration_seconds:.2f}"
        
        return await self.send_notification(
            NotificationType.CRAWL_FAILED,
            NotificationSeverity.ERROR,
            subject,
            message,
            metadata,
        )
    
    async def notify_validation_issues(
        self,
        job_id: str,
        country_code: str,
        country_name: Optional[str] = None,
        issues: Optional[List[str]] = None,
        validation_score: Optional[float] = None,
    ) -> Dict[str, bool]:
        """
        Notify about data validation issues.
        
        Args:
            job_id: Unique job identifier
            country_code: ISO country code
            country_name: Optional country name
            issues: Optional list of validation issues
            validation_score: Optional validation score (0-100)
            
        Returns:
            Dict mapping notifier names to success status
        """
        subject = f"Validation Issues: {country_name or country_code}"
        
        message_parts = [
            f"Data validation issues detected for {country_name or country_code} ({country_code})."
        ]
        
        if validation_score is not None:
            message_parts.append(f"Validation score: {validation_score}/100")
        
        if issues:
            message_parts.append(f"\nIssues found ({len(issues)}):")
            for issue in issues[:10]:  # Limit to first 10
                message_parts.append(f"  • {issue}")
            if len(issues) > 10:
                message_parts.append(f"  ... and {len(issues) - 10} more")
        
        message = "\n".join(message_parts)
        
        metadata = {
            "job_id": job_id,
            "country_code": country_code,
            "status": "validation_issues",
        }
        if country_name:
            metadata["country_name"] = country_name
        if validation_score is not None:
            metadata["validation_score"] = f"{validation_score:.2f}"
        if issues:
            metadata["issue_count"] = len(issues)
        
        return await self.send_notification(
            NotificationType.VALIDATION_ISSUES,
            NotificationSeverity.WARNING,
            subject,
            message,
            metadata,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get notification statistics.
        
        Returns:
            Dictionary containing statistics for all notifiers
        """
        stats = {
            "manager": self.stats.copy(),
            "notifiers": {}
        }
        
        for notifier in self.notifiers:
            notifier_name = notifier.__class__.__name__
            stats["notifiers"][notifier_name] = {
                "enabled": notifier.is_enabled(),
                "stats": notifier.get_stats(),
            }
        
        return stats
    
    def get_enabled_channels(self) -> List[str]:
        """
        Get list of enabled notification channel names.
        
        Returns:
            List of enabled channel names
        """
        return [n.__class__.__name__ for n in self.enabled_notifiers]
