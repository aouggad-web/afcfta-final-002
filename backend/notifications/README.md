# AfCFTA Notification System

A comprehensive, production-ready notification system for the AfCFTA crawling system with support for multiple notification channels.

## Features

- **Multiple Channels**: Email (SMTP) and Slack (webhooks)
- **Async/Await**: Full async support for non-blocking notifications
- **Type Safety**: Complete type hints for Python 3.9+
- **Rich Formatting**: HTML emails and Slack Block Kit messages
- **Error Handling**: Graceful degradation if notifications fail
- **Statistics Tracking**: Monitor notification delivery
- **Configurable**: Environment variable-based configuration

## Architecture

```
backend/notifications/
├── __init__.py                  # Package exports
├── base_notifier.py            # Abstract base class
├── email_notifier.py           # Email via SMTP
├── slack_notifier.py           # Slack via webhooks
└── notification_manager.py     # Centralized manager
```

## Quick Start

### Basic Usage

```python
from backend.notifications import NotificationManager

# Initialize manager
manager = NotificationManager()

# Send notifications
await manager.notify_crawl_start(
    job_id="crawl-001",
    country_code="KE",
    country_name="Kenya"
)

await manager.notify_crawl_success(
    job_id="crawl-001",
    country_code="KE",
    country_name="Kenya",
    stats={
        "items_scraped": 1250,
        "validation_score": 95.5
    },
    duration_seconds=120.5
)
```

## Configuration

### Email Notifications

Set these environment variables to enable email notifications:

```bash
# Enable email notifications
EMAIL_NOTIFICATIONS_ENABLED=true

# SMTP configuration
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_USE_TLS=true

# Email addresses
EMAIL_FROM=noreply@afcfta-crawler.com
EMAIL_TO=admin@example.com,team@example.com
```

**Note**: Requires `aiosmtplib` package:
```bash
pip install aiosmtplib
```

### Slack Notifications

Set these environment variables to enable Slack notifications:

```bash
# Enable Slack notifications
SLACK_NOTIFICATIONS_ENABLED=true

# Webhook configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional overrides
SLACK_CHANNEL=#crawler-alerts
SLACK_USERNAME=AfCFTA Crawler
SLACK_ICON_EMOJI=:robot_face:
```

**Note**: Requires `httpx` package:
```bash
pip install httpx
```

## Notification Types

### 1. Crawl Started
```python
await manager.notify_crawl_start(
    job_id="crawl-001",
    country_code="KE",
    country_name="Kenya"
)
```

### 2. Crawl Success
```python
await manager.notify_crawl_success(
    job_id="crawl-001",
    country_code="KE",
    country_name="Kenya",
    stats={
        "items_scraped": 1250,
        "validation_score": 95.5,
        "data_quality": "excellent"
    },
    duration_seconds=120.5
)
```

### 3. Crawl Failed
```python
await manager.notify_crawl_failed(
    job_id="crawl-001",
    country_code="KE",
    country_name="Kenya",
    error="Connection timeout after 3 retries",
    error_type="NetworkError",
    duration_seconds=45.0
)
```

### 4. Validation Issues
```python
await manager.notify_validation_issues(
    job_id="crawl-001",
    country_code="KE",
    country_name="Kenya",
    issues=[
        "Missing GDP data for 2023",
        "Trade balance value out of expected range",
        "Population data inconsistent with previous year"
    ],
    validation_score=78.5
)
```

## Custom Notifications

For custom notification scenarios:

```python
from backend.notifications import NotificationType, NotificationSeverity

await manager.send_notification(
    notification_type=NotificationType.SYSTEM_ERROR,
    severity=NotificationSeverity.ERROR,
    subject="Database Connection Lost",
    message="Unable to connect to primary database. Failing over to replica.",
    metadata={
        "error": "Connection refused",
        "database": "primary-db-01",
        "action": "failover"
    }
)
```

## Statistics

Track notification delivery:

```python
# Get comprehensive statistics
stats = manager.get_stats()
print(f"Total sent: {stats['manager']['total_sent']}")
print(f"Total failed: {stats['manager']['total_failed']}")

# Check enabled channels
channels = manager.get_enabled_channels()
print(f"Enabled channels: {', '.join(channels)}")

# Per-notifier stats
for name, info in stats['notifiers'].items():
    print(f"{name}: enabled={info['enabled']}, sent={info['stats']['sent']}")
```

## Advanced Usage

### Custom Configuration

```python
from backend.notifications import NotificationManager

config = {
    "email": {
        "timeout": 30,
        "retry_count": 3
    },
    "slack": {
        "timeout": 10
    }
}

manager = NotificationManager(config=config)
```

### Individual Notifiers

Use notifiers directly if needed:

```python
from backend.notifications import EmailNotifier, NotificationData, NotificationType, NotificationSeverity
from datetime import datetime

notifier = EmailNotifier()

if notifier.is_enabled():
    data = NotificationData(
        notification_type=NotificationType.CRAWL_SUCCESS,
        severity=NotificationSeverity.INFO,
        subject="Test Notification",
        message="This is a test",
        metadata={"test": "value"},
        timestamp=datetime.utcnow()
    )
    
    success = await notifier.send_notification(data)
    print(f"Notification sent: {success}")
```

## Error Handling

The notification system is designed to fail gracefully:

- If a notification channel fails, other channels continue
- Errors are logged but don't raise exceptions
- Statistics track successes and failures
- No notifications are sent if no channels are enabled

```python
# This will not raise an exception even if all channels fail
results = await manager.notify_crawl_success(...)

# Check individual channel results
for channel, success in results.items():
    if not success:
        print(f"Warning: {channel} notification failed")
```

## Testing

### Test Email Configuration

```python
from backend.notifications import EmailNotifier

notifier = EmailNotifier()
print(f"Email enabled: {notifier.is_enabled()}")
print(f"SMTP host: {notifier.smtp_host}")
print(f"Recipients: {notifier.to_emails}")
```

### Test Slack Configuration

```python
from backend.notifications import SlackNotifier

notifier = SlackNotifier()
print(f"Slack enabled: {notifier.is_enabled()}")
print(f"Webhook configured: {'Yes' if notifier.webhook_url else 'No'}")
```

### Send Test Notification

```python
import asyncio
from backend.notifications import NotificationManager

async def test():
    manager = NotificationManager()
    await manager.notify_crawl_success(
        job_id="test-001",
        country_code="TEST",
        country_name="Test Country",
        stats={"items_scraped": 100},
        duration_seconds=10.0
    )

asyncio.run(test())
```

## Dependencies

Required packages:
- Python 3.9+
- `aiosmtplib` (for email notifications)
- `httpx` (for Slack notifications)

Install dependencies:
```bash
pip install aiosmtplib httpx
```

## Security Notes

1. **Never commit credentials**: Use environment variables
2. **Use app passwords**: For Gmail, use app-specific passwords
3. **Secure webhooks**: Keep Slack webhook URLs private
4. **TLS/SSL**: Always use encrypted connections
5. **Rate limiting**: Be mindful of API rate limits

## Troubleshooting

### Email notifications not working

1. Check `EMAIL_NOTIFICATIONS_ENABLED=true`
2. Verify SMTP credentials
3. Check firewall/network settings
4. For Gmail: Enable "Less secure app access" or use App Password
5. Check logs for detailed error messages

### Slack notifications not working

1. Check `SLACK_NOTIFICATIONS_ENABLED=true`
2. Verify webhook URL is correct and active
3. Check Slack workspace permissions
4. Verify httpx is installed
5. Check logs for detailed error messages

### No notifications at all

```python
manager = NotificationManager()
print(f"Enabled channels: {manager.get_enabled_channels()}")

# Should show ['EmailNotifier', 'SlackNotifier'] or similar
# Empty list means no channels are configured
```

## Integration Examples

### With Crawl System

```python
from backend.notifications import NotificationManager

class CrawlJob:
    def __init__(self):
        self.notifier = NotificationManager()
    
    async def run(self, country_code: str):
        job_id = generate_job_id()
        
        # Notify start
        await self.notifier.notify_crawl_start(
            job_id=job_id,
            country_code=country_code
        )
        
        try:
            # Run crawl
            result = await self.crawl_country(country_code)
            
            # Notify success
            await self.notifier.notify_crawl_success(
                job_id=job_id,
                country_code=country_code,
                stats=result.stats,
                duration_seconds=result.duration
            )
        except Exception as e:
            # Notify failure
            await self.notifier.notify_crawl_failed(
                job_id=job_id,
                country_code=country_code,
                error=str(e),
                error_type=type(e).__name__
            )
```

## License

Part of the AfCFTA Crawler project.
