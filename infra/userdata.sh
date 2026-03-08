#!/bin/bash
set -e

# Install Docker
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
yum install -y unzip
unzip awscliv2.zip
./aws/install

# Login to ECR and pull image
aws ecr get-login-password --region ${aws_region} | \
  docker login --username AWS --password-stdin ${ecr_url}

docker pull ${ecr_url}:latest

# Write environment file
cat > /etc/applyflow.env << EOF
DATABASE_URL=${database_url}
PYTHONPATH=/app
EOF

# Create systemd service so API restarts automatically on reboot/crash
cat > /etc/systemd/system/applyflow-api.service << 'UNIT'
[Unit]
Description=ApplyFlow FastAPI Service
After=docker.service
Requires=docker.service

[Service]
Restart=always
RestartSec=10
EnvironmentFile=/etc/applyflow.env
ExecStartPre=-/usr/bin/docker stop applyflow-api
ExecStartPre=-/usr/bin/docker rm applyflow-api
ExecStart=/usr/bin/docker run --name applyflow-api \
  --env-file /etc/applyflow.env \
  -p 8000:8000 \
  ${ecr_url}:latest \
  python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
ExecStop=/usr/bin/docker stop applyflow-api

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable applyflow-api
systemctl start applyflow-api