variable "project" {
  description = "project name"
  type        = string
}

variable "db_name" {
  description = "database name"
  type        = string
}

variable "db_username" {
  description = "database master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "database master password"
  type        = string
  sensitive   = true
}
