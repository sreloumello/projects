terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
  }

  backend "s3" {
    bucket         = "kanban-tfstate"
    key            = "kanban/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "kanban-tfstate-lock"
    encrypt        = true

    # floci local services
    endpoints = {
      s3       = "http://localhost:4566"
      dynamodb = "http://localhost:4566"
    }

    # skip validations not needed for local emulator
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_region_validation      = true
    force_path_style            = true
  }

}

provider "aws" {
  region     = "us-east-1"

  # floci local services
  endpoints {
    s3             = "http://localhost:4566"
    rds            = "http://localhost:4566"
    cognitoidp     = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    apigateway     = "http://localhost:4566"
    iam            = "http://localhost:4566"
    logs           = "http://localhost:4566"
  }

  # needed for s3 service running on floci
  s3_use_path_style = true

  # ignore local validations
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}
