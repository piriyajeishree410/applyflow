resource "aws_scheduler_schedule" "applyflow" {
  name       = "${var.project}-ingestion"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  # Run every 6 hours
  schedule_expression = "rate(6 hours)"

  target {
    arn      = aws_ecs_cluster.applyflow.arn
    role_arn = aws_iam_role.eventbridge.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.applyflow.arn
      launch_type         = "FARGATE"

      network_configuration {
        assign_public_ip = true
        subnets          = data.aws_subnets.default.ids
      }
    }
  }
}