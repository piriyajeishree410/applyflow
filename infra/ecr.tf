resource "aws_ecr_repository" "applyflow" {
  name                 = var.project
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep only last 5 images — saves storage cost
resource "aws_ecr_lifecycle_policy" "applyflow" {
  repository = aws_ecr_repository.applyflow.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}