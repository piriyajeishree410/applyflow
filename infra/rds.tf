# Security group — allow Postgres from within the default VPC only
resource "aws_security_group" "rds" {
  name        = "${var.project}-rds-sg"
  description = "Allow Postgres from ECS tasks"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # tightened to ECS sg in Slice 4
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "applyflow" {
  identifier        = var.project
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"   # free tier eligible
  allocated_storage = 20

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true    # needed to run pipeline locally against RDS
  skip_final_snapshot    = true    # fine for dev

  # Free tier — no multi-AZ, no encryption overhead
  multi_az            = false
  storage_encrypted   = false

  tags = {
    Project = var.project
  }
}