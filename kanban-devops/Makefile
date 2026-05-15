# =============================================================================
# Makefile — kanban devops
# =============================================================================

TERRAFORM_DIR = terraform
ANSIBLE_DIR   = ansible
FLOCI_SCRIPT  = floci.sh

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

## db: configure database with ansible (runs inside docker network)
db:
	@echo "$(YELLOW)running ansible inside docker network...$(NC)"
	@docker compose --profile db-setup run --rm ansible
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
