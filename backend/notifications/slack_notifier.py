"""
Slack Notifier

Sends notifications to Slack via webhooks using Slack Block Kit formatting.
"""

import os
import logging
from typing import Dict, Any, Optional, List

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .base_notifier import (
    BaseNotifier,
    NotificationData,
    NotificationType,
    NotificationSeverity,
)

logger = logging.getLogger(__name__)


class SlackNotifier(BaseNotifier):
    """
    Slack notification implementation using webhooks.
    
    Configuration via environment variables:
    - SLACK_NOTIFICATIONS_ENABLED: Enable/disable Slack notifications
    - SLACK_WEBHOOK_URL: Slack webhook URL
    - SLACK_CHANNEL: Optional channel override (default: webhook default)
    - SLACK_USERNAME: Optional username (default: "AfCFTA Crawler")
    - SLACK_ICON_EMOJI: Optional icon emoji (default: ":robot_face:")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        self.enabled = os.getenv("SLACK_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.channel = os.getenv("SLACK_CHANNEL", "")
        self.username = os.getenv("SLACK_USERNAME", "AfCFTA Crawler")
        self.icon_emoji = os.getenv("SLACK_ICON_EMOJI", ":robot_face:")
        
        if not HTTPX_AVAILABLE and self.enabled:
            logger.warning("httpx not installed. Slack notifications will be disabled.")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Slack notifications are enabled and configured"""
        return self.enabled and bool(self.webhook_url) and HTTPX_AVAILABLE
    
    async def send_notification(self, data: NotificationData) -> bool:
        """
        Send Slack notification using Block Kit.
        
        Args:
            data: NotificationData object
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_enabled():
            logger.debug("Slack notifications are disabled")
            return False
        
        try:
            payload = self._create_slack_payload(data)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
            
            logger.info(f"Slack notification sent: {data.subject}")
            self.update_stats(True)
            return True
            
        except Exception as e:
            error_msg = f"Failed to send Slack notification: {str(e)}"
            logger.error(error_msg)
            self.update_stats(False, error_msg)
            return False
    
    def _create_slack_payload(self, data: NotificationData) -> Dict[str, Any]:
        """Create Slack message payload with Block Kit formatting"""
        
        # Color coding by severity
        color_map = {
            NotificationSeverity.INFO: "#36a64f",  # Green
            NotificationSeverity.WARNING: "#ff9800",  # Orange/Yellow
            NotificationSeverity.ERROR: "#d32f2f",  # Red
        }
        color = color_map.get(data.severity, "#607d8b")
        
        emoji = self.get_emoji(data.notification_type)
        
        # Build blocks
        blocks: List[Dict[str, Any]] = []
        
        # Header block
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {data.subject}",
                "emoji": True
            }
        })
        
        # Context block with severity and timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Severity:* {data.severity.value.upper()} {self.get_severity_emoji(data.severity)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:* {data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })
        
        # Divider
        blocks.append({"type": "divider"})
        
        # Message section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": data.message
            }
        })
        
        # Metadata section
        if data.metadata:
            fields = []
            for key, value in data.metadata.items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key.replace('_', ' ').title()}:*\n{value}"
                })
            
            # Add fields in chunks of 10 (Slack limit)
            for i in range(0, len(fields), 10):
                blocks.append({
                    "type": "section",
                    "fields": fields[i:i+10]
                })
        
        # Build payload
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "footer": "AfCFTA Crawler System",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(data.timestamp.timestamp())
                }
            ]
        }
        
        # Add channel override if specified
        if self.channel:
            payload["channel"] = self.channel
        
        return payload
