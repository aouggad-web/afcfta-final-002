"""
Example Usage of AfCFTA Notification System

This script demonstrates how to use the notification system in various scenarios.
"""

import asyncio
import logging
from datetime import datetime
from backend.notifications import NotificationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def example_crawl_lifecycle():
    """Example: Complete crawl job lifecycle with notifications"""
    print("\n=== Example 1: Complete Crawl Lifecycle ===\n")
    
    manager = NotificationManager()
    
    job_id = f"crawl-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    country_code = "KE"
    country_name = "Kenya"
    
    # 1. Start notification
    print("Sending crawl start notification...")
    await manager.notify_crawl_start(
        job_id=job_id,
        country_code=country_code,
        country_name=country_name
    )
    
    # Simulate crawl work
    await asyncio.sleep(2)
    
    # 2. Success notification
    print("Sending crawl success notification...")
    await manager.notify_crawl_success(
        job_id=job_id,
        country_code=country_code,
        country_name=country_name,
        stats={
            "items_scraped": 1250,
            "validation_score": 95.5,
            "data_quality": "excellent",
            "sources_accessed": 8
        },
        duration_seconds=120.5
    )


async def example_crawl_failure():
    """Example: Handling crawl failure"""
    print("\n=== Example 2: Crawl Failure ===\n")
    
    manager = NotificationManager()
    
    job_id = f"crawl-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("Sending crawl failure notification...")
    await manager.notify_crawl_failed(
        job_id=job_id,
        country_code="NG",
        country_name="Nigeria",
        error="Connection timeout after 3 retries to central bank API",
        error_type="NetworkTimeoutError",
        duration_seconds=45.0
    )


async def example_validation_issues():
    """Example: Data validation issues"""
    print("\n=== Example 3: Validation Issues ===\n")
    
    manager = NotificationManager()
    
    job_id = f"crawl-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("Sending validation issues notification...")
    await manager.notify_validation_issues(
        job_id=job_id,
        country_code="ZA",
        country_name="South Africa",
        issues=[
            "Missing GDP growth rate for Q4 2023",
            "Trade balance value exceeds expected range by 15%",
            "Population data inconsistent with UN estimates",
            "Exchange rate data incomplete for December 2023",
            "Inflation rate missing for latest quarter"
        ],
        validation_score=78.5
    )


async def example_custom_notification():
    """Example: Custom notification using base method"""
    print("\n=== Example 4: Custom Notification ===\n")
    
    from backend.notifications import NotificationType, NotificationSeverity
    
    manager = NotificationManager()
    
    print("Sending custom notification...")
    await manager.send_notification(
        notification_type=NotificationType.SYSTEM_ERROR,
        severity=NotificationSeverity.ERROR,
        subject="Database Connection Lost",
        message="Unable to connect to primary database server. System automatically failed over to replica.\n\nInvestigating root cause. All crawl jobs are paused until connection is restored.",
        metadata={
            "database_host": "primary-db-01.afcfta.internal",
            "error_code": "CONN_REFUSED",
            "failover_target": "replica-db-02.afcfta.internal",
            "affected_jobs": 3,
            "action_taken": "Automatic failover to replica"
        }
    )


async def example_batch_notifications():
    """Example: Sending multiple notifications for batch processing"""
    print("\n=== Example 5: Batch Processing ===\n")
    
    manager = NotificationManager()
    
    countries = [
        ("KE", "Kenya"),
        ("NG", "Nigeria"),
        ("ZA", "South Africa"),
        ("EG", "Egypt"),
        ("GH", "Ghana")
    ]
    
    print(f"Processing {len(countries)} countries...")
    
    for code, name in countries:
        job_id = f"batch-{datetime.now().strftime('%Y%m%d')}-{code}"
        
        # Start notification
        await manager.notify_crawl_start(
            job_id=job_id,
            country_code=code,
            country_name=name
        )
        
        # Simulate processing
        await asyncio.sleep(0.5)
        
        # Success notification
        await manager.notify_crawl_success(
            job_id=job_id,
            country_code=code,
            country_name=name,
            stats={"items_scraped": 500},
            duration_seconds=30.0
        )
        
        print(f"  ✓ Completed {name}")


async def example_statistics():
    """Example: Viewing notification statistics"""
    print("\n=== Example 6: Statistics ===\n")
    
    manager = NotificationManager()
    
    # Send a few notifications
    job_id = f"stats-test-{datetime.now().strftime('%H%M%S')}"
    
    await manager.notify_crawl_start(job_id=job_id, country_code="TZ", country_name="Tanzania")
    await manager.notify_crawl_success(
        job_id=job_id,
        country_code="TZ",
        country_name="Tanzania",
        stats={"items_scraped": 800},
        duration_seconds=60.0
    )
    
    # Get statistics
    stats = manager.get_stats()
    
    print("Notification Statistics:")
    print("-" * 50)
    print(f"Total sent: {stats['manager']['total_sent']}")
    print(f"Total failed: {stats['manager']['total_failed']}")
    print(f"Last notification: {stats['manager']['last_notification']}")
    
    print("\nBy notification type:")
    for ntype, counts in stats['manager']['by_type'].items():
        print(f"  {ntype}: {counts['sent']} sent, {counts['failed']} failed")
    
    print("\nEnabled channels:")
    channels = manager.get_enabled_channels()
    if channels:
        for channel in channels:
            print(f"  ✓ {channel}")
    else:
        print("  ⚠ No channels enabled (check environment variables)")
    
    print("\nPer-channel statistics:")
    for name, info in stats['notifiers'].items():
        enabled = "✓" if info['enabled'] else "✗"
        print(f"  {enabled} {name}:")
        print(f"      Sent: {info['stats']['sent']}")
        print(f"      Failed: {info['stats']['failed']}")
        if info['stats']['last_sent']:
            print(f"      Last sent: {info['stats']['last_sent']}")


async def example_error_handling():
    """Example: Graceful error handling"""
    print("\n=== Example 7: Error Handling ===\n")
    
    manager = NotificationManager()
    
    print("Attempting to send notification...")
    print("(Will succeed with configured channels, fail gracefully if none)")
    
    results = await manager.notify_crawl_success(
        job_id="test-001",
        country_code="TEST",
        country_name="Test Country",
        stats={"items_scraped": 100},
        duration_seconds=10.0
    )
    
    print("\nResults by channel:")
    if results:
        for channel, success in results.items():
            status = "✓ Success" if success else "✗ Failed"
            print(f"  {channel}: {status}")
    else:
        print("  No channels are enabled")
    
    print("\nNote: Application continues running even if notifications fail")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AfCFTA Notification System - Usage Examples")
    print("=" * 60)
    
    # Check if any channels are enabled
    manager = NotificationManager()
    enabled = manager.get_enabled_channels()
    
    if not enabled:
        print("\n⚠️  WARNING: No notification channels are enabled!")
        print("\nTo enable notifications, set environment variables:")
        print("\nFor Email:")
        print("  export EMAIL_NOTIFICATIONS_ENABLED=true")
        print("  export EMAIL_SMTP_HOST=smtp.gmail.com")
        print("  export EMAIL_SMTP_USER=your-email@gmail.com")
        print("  export EMAIL_SMTP_PASSWORD=your-password")
        print("  export EMAIL_TO=recipient@example.com")
        print("\nFor Slack:")
        print("  export SLACK_NOTIFICATIONS_ENABLED=true")
        print("  export SLACK_WEBHOOK_URL=https://hooks.slack.com/...")
        print("\nExamples will run but notifications won't be sent.")
        print("\n" + "=" * 60 + "\n")
    else:
        print(f"\n✓ Enabled channels: {', '.join(enabled)}\n")
        print("=" * 60 + "\n")
    
    # Run examples
    try:
        await example_crawl_lifecycle()
        await asyncio.sleep(1)
        
        await example_crawl_failure()
        await asyncio.sleep(1)
        
        await example_validation_issues()
        await asyncio.sleep(1)
        
        await example_custom_notification()
        await asyncio.sleep(1)
        
        await example_batch_notifications()
        await asyncio.sleep(1)
        
        await example_statistics()
        await asyncio.sleep(1)
        
        await example_error_handling()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
