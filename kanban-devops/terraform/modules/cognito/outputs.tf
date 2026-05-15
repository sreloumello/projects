output "user_pool_id" {
  description = "cognito user pool id"
  value       = aws_cognito_user_pool.main.id
}

output "client_id" {
  description = "app client id"
  value       = aws_cognito_user_pool_client.spa.id
}
