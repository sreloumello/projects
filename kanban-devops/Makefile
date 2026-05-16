# =============================================================================
# Makefile — kanban devops
# =============================================================================

TERRAFORM_DIR   = terraform
FLOCI_SCRIPT    = floci.sh
FLOCI_CONTAINER = kanban-floci
FLOCI_ENDPOINT  = http://$\(FLOCI_CONTAINER\):4566

# suppress docker compose warnings about unset variables
COMPOSE = docker compose --env-file /dev/null

# colors
GREEN  = \033[0;32m
YELLOW = \033[0;33m
RED    = \033[0;31m
BLUE   = \033[0;34m
NC     = \033[0m

.PHONY: setup infra db api down destroy help

## setup: full setup — infra + db + api
setup: infra db api

## infra: start floci and provision infrastructure with terraform
infra:
	@echo "$(BLUE)==> starting floci...$(NC)"
	@source $(FLOCI_SCRIPT) && $(COMPOSE) up -d floci
	@echo "$(YELLOW)waiting for floci to be healthy...$(NC)"
	@until $(COMPOSE) ps floci | grep -q "healthy"; do sleep 2; done
	@echo "$(GREEN)floci ready$(NC)"

	@echo "$(BLUE)==> provisioning infrastructure...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	cd $(TERRAFORM_DIR) && \
	terraform init -reconfigure -input=false && \
	terraform plan -out=tfplan -input=false && \
	terraform apply tfplan
	@echo "$(GREEN)infrastructure provisioned$(NC)"

	@echo "$(BLUE)==> waiting for rds to be ready...$(NC)"
	@until docker ps --filter "name=floci-rds" --format "{{.Names}}" | grep -q "floci-rds"; do \
		echo "$(YELLOW)waiting for rds container to start...$(NC)"; \
		sleep 5; \
	done
	@RDS_CONTAINER=$$(docker ps --filter "name=floci-rds" --format "{{.Names}}" | head -1) && \
	echo "$(YELLOW)waiting for postgres in $$RDS_CONTAINER to accept connections...$(NC)" && \
	until docker exec $$RDS_CONTAINER pg_isready -U dbadmin -d kanbandb > /dev/null 2>&1; do \
		sleep 3; \
	done
	@echo "$(GREEN)rds ready$(NC)"

## db: configure database with ansible
db:
	@echo "$(BLUE)==> configuring database...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	RDS_CONTAINER=$$(docker ps --filter "name=floci-rds" --format "{{.Names}}" | head -1) && \
	if [ -z "$$RDS_CONTAINER" ]; then \
		echo "$(RED)error: rds container not found — run make infra first$(NC)"; exit 1; \
	fi && \
	DB_NAME=$$(cd $(TERRAFORM_DIR) && terraform output -raw db_name) && \
	DB_USER=$$(grep db_username $(TERRAFORM_DIR)/terraform.tfvars | cut -d'"' -f2) && \
	DB_PASSWORD=$$(grep db_password $(TERRAFORM_DIR)/terraform.tfvars | cut -d'"' -f2) && \
	$(COMPOSE) --profile db-setup run --rm \
		-e DB_HOST=$$RDS_CONTAINER \
		-e DB_PORT=5432 \
		-e DB_NAME=$$DB_NAME \
		-e DB_USER=$$DB_USER \
		-e DB_PASSWORD=$$DB_PASSWORD \
		ansible
	@echo "$(GREEN)database ready$(NC)"

## api: build and start the api
api:
	@echo "$(BLUE)==> starting api...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	export DB_HOST=$$(docker ps --filter "name=floci-rds" --format "{{.Names}}" | head -1) && \
	if [ -z "$$DB_HOST" ]; then \
		echo "$(RED)error: rds container not found — run make infra first$(NC)"; exit 1; \
	fi && \
	export DB_NAME=$$(cd $(TERRAFORM_DIR) && terraform output -raw db_name) && \
	export DB_USER=$$(grep db_username $(TERRAFORM_DIR)/terraform.tfvars | cut -d'"' -f2) && \
	export DB_PASSWORD=$$(grep db_password $(TERRAFORM_DIR)/terraform.tfvars | cut -d'"' -f2) && \
	export COGNITO_USER_POOL_ID=$$(cd $(TERRAFORM_DIR) && terraform output -raw cognito_user_pool_id) && \
	export COGNITO_CLIENT_ID=$$(cd $(TERRAFORM_DIR) && terraform output -raw cognito_client_id) && \
	export AWS_ENDPOINT_URL=$(FLOCI_ENDPOINT) && \
	$(COMPOSE) up -d --build api
	@echo "$(GREEN)api ready — http://localhost:8000$(NC)"
	@echo "$(GREEN)docs   — http://localhost:8000/docs$(NC)"

## down: stop all services (preserves terraform state and floci data)
down:
	@echo "$(YELLOW)stopping services...$(NC)"
	@$(COMPOSE) down
	@echo "$(GREEN)done$(NC)"

## destroy: destroy all infrastructure and stop services
destroy:
	@echo "$(RED)==> starting floci to run terraform destroy...$(NC)"
	@source $(FLOCI_SCRIPT) && $(COMPOSE) up -d floci
	@until $(COMPOSE) ps floci | grep -q "healthy"; do sleep 2; done

	@echo "$(RED)==> destroying infrastructure...$(NC)"
	@source $(FLOCI_SCRIPT) && \
	cd $(TERRAFORM_DIR) && \
	terraform destroy -auto-approve

	@echo "$(RED)==> stopping all services...$(NC)"
	@$(COMPOSE) down
	@echo "$(GREEN)done$(NC)"

## help: show available targets
help:
	@echo ""
	@echo "  usage: make <target>"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  /'
	@echo ""
