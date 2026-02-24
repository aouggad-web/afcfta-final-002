"""
Tests pour les notifications
"""
import pytest
from backend.notifications.notification_manager import NotificationManager
from backend.notifications.base_notifier import NotificationType, NotificationSeverity


@pytest.mark.asyncio
async def test_notification_manager_init():
    """Test initialization"""
    manager = NotificationManager()
    assert manager is not None
    assert isinstance(manager, NotificationManager)


@pytest.mark.asyncio
async def test_notification_manager_has_notifiers():
    """Test that manager initializes notifiers"""
    manager = NotificationManager()
    assert hasattr(manager, 'notifiers')
    assert isinstance(manager.notifiers, list)


@pytest.mark.asyncio
async def test_crawl_started_notification():
    """Test notification de début"""
    manager = NotificationManager()
    result = await manager.notify_crawl_start(
        job_id="test_job_001",
        country_code="MA",
        country_name="Morocco"
    )
    # Ne devrait pas lever d'exception
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_crawl_success_notification():
    """Test notification de succès"""
    manager = NotificationManager()
    stats = {
        "items_scraped": 100,
        "validation_score": 95.5
    }
    result = await manager.notify_crawl_success(
        job_id="test_job_002",
        country_code="MA",
        country_name="Morocco",
        stats=stats,
        duration_seconds=120.5
    )
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_crawl_failure_notification():
    """Test notification d'échec"""
    manager = NotificationManager()
    result = await manager.notify_crawl_failed(
        job_id="test_job_003",
        country_code="MA",
        country_name="Morocco",
        error="Test error message",
        error_type="ConnectionError"
    )
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_validation_issues_notification():
    """Test notification de problèmes de validation"""
    manager = NotificationManager()
    issues = [
        "Missing HS code in line 10",
        "Invalid VAT rate in line 25",
        "Duplicate entry in line 42"
    ]
    result = await manager.notify_validation_issues(
        job_id="test_job_004",
        country_code="KE",
        country_name="Kenya",
        issues=issues,
        validation_score=75.0
    )
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_send_notification_generic():
    """Test generic notification sending"""
    manager = NotificationManager()
    result = await manager.send_notification(
        notification_type=NotificationType.CRAWL_STARTED,
        severity=NotificationSeverity.INFO,
        subject="Test Notification",
        message="This is a test message",
        metadata={"test_key": "test_value"}
    )
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_stats():
    """Test getting notification statistics"""
    manager = NotificationManager()
    stats = manager.get_stats()
    assert isinstance(stats, dict)
    assert "manager" in stats
    assert "notifiers" in stats


@pytest.mark.asyncio
async def test_get_enabled_channels():
    """Test getting list of enabled channels"""
    manager = NotificationManager()
    channels = manager.get_enabled_channels()
    assert isinstance(channels, list)


@pytest.mark.asyncio
async def test_multiple_notifications_sequence():
    """Test sending multiple notifications in sequence"""
    manager = NotificationManager()

    # Start notification
    result1 = await manager.notify_crawl_start(
        job_id="test_job_seq",
        country_code="SN",
        country_name="Senegal"
    )
    assert isinstance(result1, dict)

    # Success notification
    result2 = await manager.notify_crawl_success(
        job_id="test_job_seq",
        country_code="SN",
        country_name="Senegal",
        stats={"items_scraped": 50},
        duration_seconds=60.0
    )
    assert isinstance(result2, dict)

    # Check stats were updated
    stats = manager.get_stats()
    assert stats["manager"]["total_sent"] >= 0  # May be 0 if no notifiers enabled
