# =============================================================================
# Makefile — kanban devops
# =============================================================================

TERRAFORM_DIR = terraform
ANSIBLE_DIR   = ansible
FLOCI_SCRIPT  = floci.sh
ENV          ?= local

# colors
GREEN  = \033[0;32m
YELLOW = \033[0;33m
RED    = \033[0;31m
NC     = \033[0m

.PHONY: setup infra db destroy help

## setup: provision infrastructure and configure database
setup: infra db

## infra: provision infrastructure with terraform
infra:
	@echo "$(YELLOW)loading floci environment...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	cd $(TERRAFORM_DIR) && \
	echo "$(YELLOW)initializing terraform...$(NC)" && \
	terraform init -reconfigure && \
	echo "$(YELLOW)planning...$(NC)" && \
	terraform plan -out=tfplan && \
	echo "$(YELLOW)applying...$(NC)" && \
	terraform apply tfplan
	@echo "$(GREEN)infrastructure ready$(NC)"

## db: configure database with ansible (reads terraform outputs)
db:
	@echo "$(YELLOW)reading terraform outputs...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	if [ "$(ENV)" = "aws" ]; then \
		DB_HOST=$$(cd $(TERRAFORM_DIR) && terraform output -raw db_host); \
	else \
		DB_HOST=$$(docker ps --filter "name=floci-rds" --format "{{.Names}}" | head -1); \
		if [ -z "$$DB_HOST" ]; then echo "$(RED)error: rds container not found$(NC)"; exit 1; fi; \
	fi && \
	echo "$(YELLOW)found db host: $$DB_HOST$(NC)" && \
	DB_NAME=$$(cd $(TERRAFORM_DIR) && terraform output -raw db_name) && \
	DB_USER=$$(grep db_username $(TERRAFORM_DIR)/terraform.tfvars | cut -d'"' -f2) && \
	DB_PASSWORD=$$(grep db_password $(TERRAFORM_DIR)/terraform.tfvars | cut -d'"' -f2) && \
	echo "$(YELLOW)running ansible inside docker network...$(NC)" && \
	docker compose --profile db-setup run --rm \
		-e DB_HOST=$$DB_HOST \
		-e DB_PORT=5432 \
		-e DB_NAME=$$DB_NAME \
		-e DB_USER=$$DB_USER \
		-e DB_PASSWORD=$$DB_PASSWORD \
		ansible
	@echo "$(GREEN)database ready$(NC)"

## destroy: destroy all infrastructure
destroy:
	@echo "$(RED)destroying infrastructure...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	cd $(TERRAFORM_DIR) && \
	terraform destroy -auto-approve
	@echo "$(GREEN)done$(NC)"

## help: show available targets
help:
	@echo "available targets:"
	@grep -E '^## ' Makefile | sed 's/## /  /'
