variable "aws_region" {
  default = "us-east-1"
}

variable "project" {
  default = "applyflow"
}

variable "db_username" {
  default = "applyflow"
}

variable "db_password" {
  description = "RDS master password"
  sensitive   = true
}

variable "db_name" {
  default = "applyflow"
}