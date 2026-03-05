# Security group for the API service
resource "aws_security_group" "api" {
  name        = "${var.project}-api-sg"
  description = "Allow inbound HTTP to FastAPI"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Task definition for FastAPI service
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "${var.project}-api"
    image = "${aws_ecr_repository.applyflow.repository_url}:latest"

    command = [
      "python", "-m", "uvicorn", "api.main:app",
      "--host", "0.0.0.0",
      "--port", "8000"
    ]

    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]

    environment = [{
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.applyflow.address}:5432/${var.db_name}"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.applyflow.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
  }])
}

# ECS service — keeps the API always running
resource "aws_ecs_service" "api" {
  name            = "${var.project}-api"
  cluster         = aws_ecs_cluster.applyflow.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }

  # Allow deploy without downtime
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
}

output "api_service_name" {
  value = aws_ecs_service.api.name
}