from services.crawl_orchestrator import CrawlJob


def test_crawl_job_exposes_country_progress_steps():
    job = CrawlJob("job123", ["DZA", "MAR"])

    initial = job.to_dict()
    assert initial["progress_pct"] == 0.0
    assert initial["current_country"] is None
    assert [s["iso3"] for s in initial["progress_steps"]] == ["DZA", "MAR"]
    assert [s["status"] for s in initial["progress_steps"]] == ["pending", "pending"]

    job.current_country = "DZA"
    job.country_results["DZA"] = {"success": True}
    job.country_progress["DZA"].update({"status": "done", "records_saved": 42})

    updated = job.to_dict()
    assert updated["progress_pct"] == 50.0
    assert updated["current_country"] == "DZA"
    assert updated["succeeded"] == 1
    assert updated["pending"] == 1
    assert updated["progress_steps"][0]["records_saved"] == 42
