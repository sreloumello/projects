module "cognito" {
  source  = "./modules/cognito"
  project = var.project
}

module "rds" {
  source      = "./modules/rds"
  project     = var.project
  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password
}
