resource "aws_cognito_user_pool" "main" {
  name = "${var.project}-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_numbers   = true
    require_lowercase = true
    require_uppercase = false
    require_symbols   = false
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    mutable             = true
    required            = true
    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }
}

resource "aws_cognito_user_pool_client" "spa" {
  name         = "${var.project}-spa-client"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false
}
