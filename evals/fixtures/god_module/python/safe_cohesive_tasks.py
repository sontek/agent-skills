# coverages/tasks.py
from celery import shared_task


@shared_task
def ingest_coverage_report(upload_id: int) -> None:
    CoverageIngestionService(upload_id).run()


@shared_task
def recompute_coverage_summary(commit_id: int) -> None:
    CoverageQueryService(commit_id).rebuild_summary()


@shared_task
def rollup_daily_coverage(date: str) -> None:
    CoverageRollupService().rollup(date)


@shared_task
def expire_stale_coverage(days: int) -> None:
    CoverageFile.objects.older_than(days).delete()


@shared_task
def backfill_coverage_history(repo_id: int) -> None:
    CoverageBackfillService(repo_id).run()
