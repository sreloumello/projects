output "cognito_user_pool_id" {
  description = "cognito user pool id"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "cognito app client id"
  value       = module.cognito.client_id
}

output "db_host" {
  description = "database host"
  value       = module.rds.db_host
}

output "db_port" {
  description = "database port"
  value       = module.rds.db_port
}

output "db_name" {
  description = "database name"
  value       = module.rds.db_name
}
