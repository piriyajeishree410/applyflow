import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

NAMESPACE = "ApplyFlow"
REGION = os.getenv("AWS_REGION", "us-east-1")

# Only publish metrics when running in AWS (DATABASE_URL set to Postgres)
_client = None


def _get_client():
    global _client
    if _client is None:
        try:
            import boto3
            _client = boto3.client("cloudwatch", region_name=REGION)
        except Exception as e:
            logger.warning(f"[metrics] CloudWatch client init failed: {e}")
    return _client


def _publish(metric_name: str, value: float, unit: str = "Count"):
    """Publish a single metric to CloudWatch. Silently skips if client unavailable."""
    client = _get_client()
    if client is None:
        return
    try:
        client.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[{
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.now(timezone.utc),
                "Dimensions": [{"Name": "Environment", "Value": "production"}],
            }]
        )
        logger.debug(f"[metrics] published {metric_name}={value}")
    except Exception as e:
        logger.warning(f"[metrics] failed to publish {metric_name}: {e}")


def record_jobs_fetched(count: int):
    _publish("JobsFetched", count)


def record_jobs_saved(count: int):
    _publish("JobsSaved", count)


def record_duplicates_skipped(count: int):
    _publish("DuplicatesSkipped", count)


def record_failures(count: int):
    _publish("IngestionFailures", count)


def record_ingestion_duration(seconds: float):
    _publish("IngestionDurationSeconds", seconds, unit="Seconds")


def record_last_successful_run():
    """Publish a heartbeat metric — used to detect staleness."""
    _publish("LastSuccessfulRun", 1)