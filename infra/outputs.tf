output "ecr_repository_url" {
  value = aws_ecr_repository.applyflow.repository_url
}

output "rds_endpoint" {
  value = aws_db_instance.applyflow.endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.applyflow.bucket
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.applyflow.name
}