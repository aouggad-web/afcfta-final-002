"""
Tests for AfCFTA Notification System

Run with: python -m pytest backend/notifications/test_notifications.py -v
Or directly: python backend/notifications/test_notifications.py
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from backend.notifications import (
    NotificationManager,
    EmailNotifier,
    SlackNotifier,
    NotificationType,
    NotificationSeverity,
    NotificationData,
)


class TestBaseNotifier:
    """Tests for base notifier functionality"""
    
    def test_emoji_mapping(self):
        """Test emoji mapping for notification types"""
        from backend.notifications.base_notifier import BaseNotifier
        
        # Can't instantiate abstract class, so check class attributes
        assert NotificationType.CRAWL_STARTED in BaseNotifier.EMOJI_MAP
        assert NotificationType.CRAWL_SUCCESS in BaseNotifier.EMOJI_MAP
        assert NotificationType.CRAWL_FAILED in BaseNotifier.EMOJI_MAP
        
    def test_severity_emoji(self):
        """Test emoji mapping for severity levels"""
        from backend.notifications.base_notifier import BaseNotifier
        
        assert NotificationSeverity.INFO in BaseNotifier.SEVERITY_EMOJI
        assert NotificationSeverity.WARNING in BaseNotifier.SEVERITY_EMOJI
        assert NotificationSeverity.ERROR in BaseNotifier.SEVERITY_EMOJI


class TestEmailNotifier:
    """Tests for email notifier"""
    
    def test_initialization_disabled(self):
        """Test email notifier initializes as disabled by default"""
        notifier = EmailNotifier()
        assert not notifier.is_enabled()
    
    @patch.dict('os.environ', {
        'EMAIL_NOTIFICATIONS_ENABLED': 'true',
        'EMAIL_SMTP_HOST': 'smtp.example.com',
        'EMAIL_SMTP_USER': 'user@example.com',
        'EMAIL_TO': 'recipient@example.com'
    })
    def test_initialization_with_env_vars(self):
        """Test email notifier reads environment variables"""
        notifier = EmailNotifier()
        assert notifier.smtp_host == 'smtp.example.com'
        assert notifier.smtp_user == 'user@example.com'
        assert 'recipient@example.com' in notifier.to_emails
    
    def test_multiple_recipients(self):
        """Test parsing multiple email recipients"""
        with patch.dict('os.environ', {'EMAIL_TO': 'user1@example.com, user2@example.com'}):
            notifier = EmailNotifier()
            assert len(notifier.to_emails) == 2
            assert 'user1@example.com' in notifier.to_emails
            assert 'user2@example.com' in notifier.to_emails


class TestSlackNotifier:
    """Tests for slack notifier"""
    
    def test_initialization_disabled(self):
        """Test slack notifier initializes as disabled by default"""
        notifier = SlackNotifier()
        assert not notifier.is_enabled()
    
    @patch.dict('os.environ', {
        'SLACK_NOTIFICATIONS_ENABLED': 'true',
        'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'
    })
    def test_initialization_with_env_vars(self):
        """Test slack notifier reads environment variables"""
        notifier = SlackNotifier()
        assert notifier.webhook_url == 'https://hooks.slack.com/test'
    
    def test_slack_payload_structure(self):
        """Test Slack payload has correct structure"""
        notifier = SlackNotifier()
        notifier.enabled = True
        notifier.webhook_url = "https://hooks.slack.com/test"
        
        data = NotificationData(
            notification_type=NotificationType.CRAWL_SUCCESS,
            severity=NotificationSeverity.INFO,
            subject="Test",
            message="Test message",
            metadata={"key": "value"},
            timestamp=datetime.utcnow()
        )
        
        payload = notifier._create_slack_payload(data)
        
        assert "blocks" in payload
        assert "username" in payload
        assert "attachments" in payload
        assert len(payload["blocks"]) > 0


class TestNotificationManager:
    """Tests for notification manager"""
    
    def test_initialization(self):
        """Test manager initializes with notifiers"""
        manager = NotificationManager()
        assert len(manager.notifiers) == 2  # Email and Slack
        assert isinstance(manager.notifiers[0], (EmailNotifier, SlackNotifier))
        assert isinstance(manager.notifiers[1], (EmailNotifier, SlackNotifier))
    
    def test_no_enabled_channels(self):
        """Test manager works with no enabled channels"""
        manager = NotificationManager()
        assert len(manager.get_enabled_channels()) == 0
    
    @pytest.mark.asyncio
    async def test_notify_crawl_start(self):
        """Test crawl start notification"""
        manager = NotificationManager()
        
        # Should not fail even with no enabled channels
        results = await manager.notify_crawl_start(
            job_id="test-001",
            country_code="KE",
            country_name="Kenya"
        )
        
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_notify_crawl_success(self):
        """Test crawl success notification"""
        manager = NotificationManager()
        
        results = await manager.notify_crawl_success(
            job_id="test-001",
            country_code="KE",
            country_name="Kenya",
            stats={"items_scraped": 100},
            duration_seconds=60.0
        )
        
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_notify_crawl_failed(self):
        """Test crawl failed notification"""
        manager = NotificationManager()
        
        results = await manager.notify_crawl_failed(
            job_id="test-001",
            country_code="KE",
            country_name="Kenya",
            error="Test error",
            error_type="TestError"
        )
        
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_notify_validation_issues(self):
        """Test validation issues notification"""
        manager = NotificationManager()
        
        results = await manager.notify_validation_issues(
            job_id="test-001",
            country_code="KE",
            country_name="Kenya",
            issues=["Issue 1", "Issue 2"],
            validation_score=85.5
        )
        
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self):
        """Test that statistics are tracked"""
        manager = NotificationManager()
        
        # Send a notification
        await manager.notify_crawl_start(
            job_id="test-001",
            country_code="KE"
        )
        
        # Check stats
        stats = manager.get_stats()
        assert "manager" in stats
        assert "notifiers" in stats
        assert "total_sent" in stats["manager"]
        assert "by_type" in stats["manager"]
    
    @pytest.mark.asyncio
    async def test_custom_notification(self):
        """Test custom notification sending"""
        manager = NotificationManager()
        
        results = await manager.send_notification(
            notification_type=NotificationType.SYSTEM_ERROR,
            severity=NotificationSeverity.ERROR,
            subject="Test Error",
            message="This is a test error message",
            metadata={"error_code": "TEST001"}
        )
        
        assert isinstance(results, dict)


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_crawl_lifecycle(self):
        """Test complete crawl lifecycle with notifications"""
        manager = NotificationManager()
        
        job_id = "integration-test-001"
        country_code = "KE"
        
        # Start
        await manager.notify_crawl_start(
            job_id=job_id,
            country_code=country_code
        )
        
        # Simulate work
        await asyncio.sleep(0.1)
        
        # Success
        await manager.notify_crawl_success(
            job_id=job_id,
            country_code=country_code,
            stats={"items_scraped": 500},
            duration_seconds=10.0
        )
        
        # Verify stats
        stats = manager.get_stats()
        assert stats["manager"]["by_type"].get("crawl_started") is not None
        assert stats["manager"]["by_type"].get("crawl_success") is not None


# Simple test runner for when pytest is not available
def run_simple_tests():
    """Run basic tests without pytest"""
    print("Running basic notification system tests...\n")
    
    # Test 1: Imports
    print("✓ Test 1: Imports successful")
    
    # Test 2: Manager initialization
    manager = NotificationManager()
    print("✓ Test 2: NotificationManager initialized")
    
    # Test 3: Notifiers exist
    assert len(manager.notifiers) == 2
    print("✓ Test 3: Both notifiers registered")
    
    # Test 4: Email notifier
    email = EmailNotifier()
    assert not email.is_enabled()  # Should be disabled by default
    print("✓ Test 4: EmailNotifier disabled by default")
    
    # Test 5: Slack notifier
    slack = SlackNotifier()
    assert not slack.is_enabled()  # Should be disabled by default
    print("✓ Test 5: SlackNotifier disabled by default")
    
    # Test 6: Stats structure
    stats = manager.get_stats()
    assert "manager" in stats
    assert "notifiers" in stats
    print("✓ Test 6: Statistics structure correct")
    
    # Test 7: Async notification (basic)
    async def test_async():
        results = await manager.notify_crawl_start(
            job_id="test",
            country_code="TEST"
        )
        return isinstance(results, dict)
    
    result = asyncio.run(test_async())
    assert result
    print("✓ Test 7: Async notification works")
    
    print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    # Try to use pytest if available, otherwise run simple tests
    try:
        import pytest
        import sys
        sys.exit(pytest.main([__file__, "-v"]))
    except ImportError:
        run_simple_tests()
