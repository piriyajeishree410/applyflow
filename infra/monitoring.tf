variable "alert_email" {
  description = "Email address to receive CloudWatch alerts"
}

# ── SNS Topic ─────────────────────────────────────────────────────────────────
resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ── Alarm: ingestion failures ─────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "ingestion_failures" {
  alarm_name          = "${var.project}-ingestion-failures"
  alarm_description   = "Ingestion worker reported failures"
  namespace           = "ApplyFlow"
  metric_name         = "IngestionFailures"
  statistic           = "Sum"
  period              = 3600       # 1 hour
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Environment = "production"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# ── Alarm: ingestion staleness ────────────────────────────────────────────────
# Fires if LastSuccessfulRun hasn't been published in 9 hours
resource "aws_cloudwatch_metric_alarm" "ingestion_stale" {
  alarm_name          = "${var.project}-ingestion-stale"
  alarm_description   = "Ingestion worker has not run successfully in 9 hours"
  namespace           = "ApplyFlow"
  metric_name         = "LastSuccessfulRun"
  statistic           = "Sum"
  period              = 32400      # 9 hours
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"  # no data = alarm

  dimensions = {
    Environment = "production"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# ── Alarm: high API error rate ────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "${var.project}-api-errors"
  alarm_description   = "ECS task failures detected"
  namespace           = "AWS/ECS"
  metric_name         = "RunningTaskCount"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 0
  comparison_operator = "LessThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.applyflow.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}