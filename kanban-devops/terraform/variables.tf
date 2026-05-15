variable "project" {
  description = "project name"
  type        = string
  default     = "kanban"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_name" {
  description = "DB name"
  type        = string
}

variable "db_username" {
  description = "master user RDS"
  type        = string
}

variable "db_password" {
  description = "RDS password"
  type        = string
  sensitive   = true
}
