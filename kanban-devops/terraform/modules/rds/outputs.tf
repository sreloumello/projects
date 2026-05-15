output "db_host" {
  description = "database host endpoint"
  value       = aws_db_instance.main.address
}

output "db_port" {
  description = "database port"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "database name"
  value       = aws_db_instance.main.db_name
}
