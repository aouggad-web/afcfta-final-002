"""
Base Notifier Abstract Class

Defines the interface for all notification implementations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class NotificationType(Enum):
    """Types of notifications that can be sent"""
    CRAWL_STARTED = "crawl_started"
    CRAWL_SUCCESS = "crawl_success"
    CRAWL_FAILED = "crawl_failed"
    VALIDATION_ISSUES = "validation_issues"
    SYSTEM_ERROR = "system_error"


class NotificationSeverity(Enum):
    """Severity levels for notifications"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class NotificationData:
    """Data structure for notification content"""
    notification_type: NotificationType
    severity: NotificationSeverity
    subject: str
    message: str
    metadata: Dict[str, Any]
    timestamp: datetime


class BaseNotifier(ABC):
    """
    Abstract base class for all notification implementations.
    
    All notifiers must implement send_notification() and is_enabled().
    """
    
    # Emoji mappings for different notification types
    EMOJI_MAP = {
        NotificationType.CRAWL_STARTED: "🚀",
        NotificationType.CRAWL_SUCCESS: "✅",
        NotificationType.CRAWL_FAILED: "❌",
        NotificationType.VALIDATION_ISSUES: "⚠️",
        NotificationType.SYSTEM_ERROR: "🔥",
    }
    
    # Severity emoji
    SEVERITY_EMOJI = {
        NotificationSeverity.INFO: "ℹ️",
        NotificationSeverity.WARNING: "⚠️",
        NotificationSeverity.ERROR: "❌",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the notifier with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.stats = {
            "sent": 0,
            "failed": 0,
            "last_sent": None,
            "last_error": None,
        }
    
    @abstractmethod
    async def send_notification(self, data: NotificationData) -> bool:
        """
        Send a notification.
        
        Args:
            data: NotificationData object containing all notification details
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if this notifier is enabled.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        pass
    
    def get_emoji(self, notification_type: NotificationType) -> str:
        """Get emoji for notification type"""
        return self.EMOJI_MAP.get(notification_type, "📢")
    
    def get_severity_emoji(self, severity: NotificationSeverity) -> str:
        """Get emoji for severity level"""
        return self.SEVERITY_EMOJI.get(severity, "ℹ️")
    
    def format_subject(self, subject: str, notification_type: NotificationType) -> str:
        """Format notification subject with emoji"""
        emoji = self.get_emoji(notification_type)
        return f"{emoji} {subject}"
    
    def update_stats(self, success: bool, error: Optional[str] = None):
        """Update notifier statistics"""
        if success:
            self.stats["sent"] += 1
            self.stats["last_sent"] = datetime.now().isoformat()
        else:
            self.stats["failed"] += 1
            self.stats["last_error"] = error
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notifier statistics"""
        return self.stats.copy()
