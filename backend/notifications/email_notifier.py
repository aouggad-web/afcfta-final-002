"""
Email Notifier

Sends notifications via email using SMTP (aiosmtplib for async support).
"""

import os
import logging
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False

from .base_notifier import (
    BaseNotifier,
    NotificationData,
    NotificationType,
    NotificationSeverity,
)

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """
    Email notification implementation using SMTP.
    
    Configuration via environment variables:
    - EMAIL_NOTIFICATIONS_ENABLED: Enable/disable email notifications
    - EMAIL_SMTP_HOST: SMTP server hostname
    - EMAIL_SMTP_PORT: SMTP server port (default: 587)
    - EMAIL_SMTP_USER: SMTP username
    - EMAIL_SMTP_PASSWORD: SMTP password
    - EMAIL_FROM: Sender email address
    - EMAIL_TO: Recipient email address(es), comma-separated
    - EMAIL_USE_TLS: Use TLS (default: true)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        self.smtp_host = os.getenv("EMAIL_SMTP_HOST", "")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("EMAIL_SMTP_USER", "")
        self.smtp_password = os.getenv("EMAIL_SMTP_PASSWORD", "")
        self.from_email = os.getenv("EMAIL_FROM", "noreply@afcfta-crawler.com")
        self.to_emails = [
            email.strip() 
            for email in os.getenv("EMAIL_TO", "").split(",") 
            if email.strip()
        ]
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        
        if not AIOSMTPLIB_AVAILABLE and self.enabled:
            logger.warning("aiosmtplib not installed. Email notifications will be disabled.")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if email notifications are enabled and configured"""
        return (
            self.enabled 
            and bool(self.smtp_host) 
            and bool(self.smtp_user) 
            and bool(self.to_emails)
            and AIOSMTPLIB_AVAILABLE
        )
    
    async def send_notification(self, data: NotificationData) -> bool:
        """
        Send email notification.
        
        Args:
            data: NotificationData object
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_enabled():
            logger.debug("Email notifications are disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[AfCFTA Crawler] {self.format_subject(data.subject, data.notification_type)}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            
            # Create plain text and HTML versions
            text_content = self._create_text_email(data)
            html_content = self._create_html_email(data)
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.use_tls,
            )
            
            logger.info(f"Email notification sent: {data.subject}")
            self.update_stats(True)
            return True
            
        except Exception as e:
            error_msg = f"Failed to send email notification: {str(e)}"
            logger.error(error_msg)
            self.update_stats(False, error_msg)
            return False
    
    def _create_text_email(self, data: NotificationData) -> str:
        """Create plain text email content"""
        lines = [
            f"AfCFTA Crawler Notification",
            f"=" * 50,
            f"",
            f"Type: {data.notification_type.value}",
            f"Severity: {data.severity.value}",
            f"Time: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"",
            f"{data.message}",
            f"",
        ]
        
        if data.metadata:
            lines.append("Details:")
            lines.append("-" * 50)
            for key, value in data.metadata.items():
                lines.append(f"{key}: {value}")
            lines.append("")
        
        lines.append("-" * 50)
        lines.append("AfCFTA Crawler System")
        
        return "\n".join(lines)
    
    def _create_html_email(self, data: NotificationData) -> str:
        """Create HTML email content"""
        
        # Color coding by severity
        color_map = {
            NotificationSeverity.INFO: "#17a2b8",
            NotificationSeverity.WARNING: "#ffc107",
            NotificationSeverity.ERROR: "#dc3545",
        }
        color = color_map.get(data.severity, "#6c757d")
        
        emoji = self.get_emoji(data.notification_type)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: {color};
            color: white;
            padding: 20px;
            border-radius: 5px 5px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            background-color: #f8f9fa;
            padding: 20px;
            border: 1px solid #dee2e6;
            border-top: none;
        }}
        .message {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .metadata {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .metadata table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .metadata td {{
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
        }}
        .metadata td:first-child {{
            font-weight: bold;
            width: 40%;
            color: #666;
        }}
        .footer {{
            background-color: #343a40;
            color: white;
            padding: 15px;
            border-radius: 0 0 5px 5px;
            text-align: center;
            font-size: 12px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin: 5px 0;
        }}
        .badge-info {{ background-color: #17a2b8; color: white; }}
        .badge-warning {{ background-color: #ffc107; color: #000; }}
        .badge-error {{ background-color: #dc3545; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{emoji} {data.subject}</h1>
    </div>
    <div class="content">
        <div style="margin-bottom: 10px;">
            <span class="badge badge-{data.severity.value}">{data.severity.value.upper()}</span>
            <span style="color: #666; font-size: 14px; margin-left: 10px;">
                {data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
            </span>
        </div>
        
        <div class="message">
            {data.message.replace(chr(10), '<br>')}
        </div>
"""
        
        if data.metadata:
            html += """
        <div class="metadata">
            <h3 style="margin-top: 0; color: #333;">Details</h3>
            <table>
"""
            for key, value in data.metadata.items():
                html += f"""
                <tr>
                    <td>{key.replace('_', ' ').title()}</td>
                    <td>{value}</td>
                </tr>
"""
            html += """
            </table>
        </div>
"""
        
        html += """
    </div>
    <div class="footer">
        <p style="margin: 0;">AfCFTA Crawler System</p>
        <p style="margin: 5px 0 0 0; color: #adb5bd;">Automated Notification</p>
    </div>
</body>
</html>
"""
        return html
