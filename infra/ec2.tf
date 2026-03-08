# Security group for EC2 API server
resource "aws_security_group" "ec2_api" {
  name        = "${var.project}-ec2-api-sg"
  description = "Allow HTTP to FastAPI on EC2"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # tighten to your IP later
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM instance profile — allows EC2 to pull from ECR
resource "aws_iam_role" "ec2_api" {
  name = "${var.project}-ec2-api"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ecr" {
  role       = aws_iam_role.ec2_api.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "ec2_api" {
  name = "${var.project}-ec2-api"
  role = aws_iam_role.ec2_api.name
}

# Latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# EC2 instance — t2.micro free tier
resource "aws_instance" "api" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  iam_instance_profile   = aws_iam_instance_profile.ec2_api.name
  vpc_security_group_ids = [aws_security_group.ec2_api.id]
  key_name               = var.ec2_key_name

  user_data = base64encode(templatefile("${path.module}/userdata.sh", {
    aws_region     = var.aws_region
    ecr_url        = aws_ecr_repository.applyflow.repository_url
    database_url   = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.applyflow.address}:5432/${var.db_name}"
  }))

  tags = {
    Name    = "${var.project}-api"
    Project = var.project
  }
}

# Elastic IP — stable public IP that survives restarts
resource "aws_eip" "api" {
  instance = aws_instance.api.id
  domain   = "vpc"
}

output "api_public_ip" {
  value = aws_eip.api.public_ip
}

output "api_url" {
  value = "http://${aws_eip.api.public_ip}:8000"
}