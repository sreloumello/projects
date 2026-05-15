# Kanban DevOps

Personal project to study and practice DevOps concepts. The application itself is a simple kanban board (to-do CRUD), used as a base to explore different ways of provisioning and operating infrastructure, all as code with Terraform.

The app is not the focus: it is the excuse. The goal is to understand in practice the differences in cost, complexity, and operation between different infrastructure stacks.

---

## The application

A kanban board with authentication, public read access, and protected write access.

- **Frontend:** static HTML/CSS/JS served via S3 + CloudFront
- **Backend:** Python + FastAPI running on Lambda via Mangum adapter
- **Database:** PostgreSQL via RDS
- **Auth:** AWS Cognito (user pool + JWT tokens)
- **Infrastructure:** 100% provisioned with Terraform

### Access model

| Action | Authentication required |
|---|---|
| View the board | no — public read |
| Create / edit / move / delete tasks | yes — must be logged in |

---

## Authentication — how it works

Authentication is handled by **AWS Cognito**, a managed identity service. It stores users, validates passwords, and issues JWT tokens. Your API never touches raw passwords.

### Cognito concepts

**User Pool** — the user database. Stores email, hashed password, name, and any custom attributes. Handles email verification, password policies, and brute-force protection automatically.

**App Client** — the entry point for your frontend to interact with the User Pool. Defines which auth flows are allowed and how long tokens last. A SPA (Single Page Application) client never has a `client_secret` because anything in browser JavaScript is visible to anyone who opens DevTools.

### What is a SPA?

A Single Page Application loads HTML/CSS/JS once in the browser and then handles all navigation in JavaScript — no full page reloads. Examples: Gmail, Figma, Trello. Your kanban frontend is a SPA.

Because SPAs run entirely in the browser, any secret embedded in the code is exposed. This is why the Cognito App Client has `generate_secret = false`.

### Token flow

```
1. user fills in email + password on the frontend
2. frontend calls POST /auth/login on the API (Lambda)
3. Lambda calls Cognito with email + password
4. Cognito validates and returns 3 tokens:
   ├── access_token  — "what you can do"    (1h, in memory)
   ├── id_token      — "who you are"        (1h, in memory)
   └── refresh_token — "renew the session"  (1 day, HttpOnly cookie)
5. Lambda returns access_token + id_token to frontend
   and sets refresh_token as an HttpOnly cookie
6. frontend stores access_token in memory only (not localStorage)
   and sends it on every request: Authorization: Bearer <access_token>
7. when access_token expires (1h), frontend calls POST /auth/refresh
   Lambda reads the cookie and silently issues new tokens
```

### Why HttpOnly cookie for the refresh token?

An `HttpOnly` cookie cannot be read by JavaScript — only the browser sends it automatically with requests. This protects against **XSS (Cross-Site Scripting)** attacks where malicious scripts try to steal tokens.

Storing the `access_token` in `localStorage` is a common antipattern because any XSS vulnerability exposes it immediately. Keeping it in memory means it disappears when the tab closes, and a stolen XSS script cannot access it.

### Security practices applied

- passwords never touch your API — Cognito validates them directly
- `refresh_token` in `HttpOnly` cookie — JavaScript cannot read it
- `access_token` in memory only — not persisted in the browser
- no `client_secret` on the frontend — correct for SPAs
- `prevent_user_existence_errors = ENABLED` — prevents email enumeration attacks (without this, an attacker can tell which emails are registered by the error message)

---

## Infrastructure stacks

The project is built progressively through multiple infrastructure patterns, all provisioned from scratch with Terraform.

### Stack 1 — Lambda + API Gateway + RDS + S3 + CloudFront (current)

```
user
 │
 ▼
CloudFront (CDN)
 ├── /          →  S3 (static frontend)
 └── /api/*     →  API Gateway HTTP v2
                        │
                   Lambda (FastAPI + Mangum)
                        │
                   RDS PostgreSQL
                   (Cognito for auth)
```

### Stack 2 — EC2 Multi-AZ *(coming soon)*
### Stack 3 — EKS *(coming soon)*
### Stack 4 — Kind (local Kubernetes, free) *(coming soon)*

---

## Local development with Floci

[Floci](https://github.com/floci-io/floci) is a free, open-source local AWS emulator — a drop-in replacement for LocalStack (which required auth tokens since March 2026). It runs as a single Docker container and emulates 41 AWS services on port `4566`.

```bash
docker run --rm -p 4566:4566 floci/floci:latest
```

### Why Floci instead of real AWS for development?

| | Floci | AWS |
|---|---|---|
| cost | free forever | pay per use |
| startup | ~24ms | — |
| RDS | real Docker container | managed service |
| Lambda | real Docker container | managed service |
| Cognito | in-process emulation | managed service |
| internet required | no | yes |

### How Floci integrates with Terraform

The same Terraform code runs locally (Floci) and in production (AWS). The only difference is the provider configuration — local uses fake credentials and points all endpoints to `localhost:4566`.

```hcl
# local (Floci)
provider "aws" {
  access_key = "test"
  secret_key = "test"
  endpoints {
    s3    = "http://localhost:4566"
    rds   = "http://localhost:4566"
    ...
  }
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

# production (AWS) — just a normal provider, no overrides
provider "aws" {
  region = "us-east-1"
}
```

### Remote state with Floci

Terraform state is stored remotely in S3 with DynamoDB locking — the same pattern used in production teams. Locally, both services are emulated by Floci.

```
terraform apply
      │
      ▼
saves state to S3 (Floci)  →  kanban-tfstate bucket
      │
      ▼
acquires lock in DynamoDB (Floci)  →  kanban-tfstate-lock table
      │
      ▼
releases lock after apply completes
```

To set up the backend infrastructure before the first `terraform init`:

```bash
source floci.sh

aws s3 mb s3://kanban-tfstate
aws dynamodb create-table \
  --table-name kanban-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Important: source vs ./

When loading environment variables from a script, always use `source` — not `./`:

```bash
# wrong — variables are created in a child process and disappear
./floci.sh

# correct — variables are created in the current shell
source ./floci.sh
```

`./script.sh` spawns a child process. When it finishes, everything it created is gone. `source` executes the script in the current shell, so exports persist.

---

## Floci vs AWS — known differences and workarounds

These are incompatibilities discovered during development. Each section documents what works differently in Floci and what change is needed.

### 1. RDS — `AddTagsToResource` not supported

**Error:**
```
operation error RDS: AddTagsToResource: UnsupportedOperation
```

**Cause:** Floci does not implement the `AddTagsToResource` operation for RDS instances.

**Workaround:** remove `tags` from `aws_db_instance` in the local Terraform config. Tags work normally in real AWS.

```hcl
# floci — no tags on rds
resource "aws_db_instance" "main" {
  ...
  # tags block removed
}

# aws production — tags work fine
resource "aws_db_instance" "main" {
  ...
  tags = { Project = var.project }
}
```

---

### 2. Cognito User Pool Client — token validity fields not returned after apply

**Error:**
```
Provider produced inconsistent result after apply
.access_token_validity: was cty.NumberIntVal(1), but now cty.NumberIntVal(0)
.refresh_token_validity: was cty.NumberIntVal(30), but now cty.NumberIntVal(0)
.id_token_validity: was cty.NumberIntVal(1), but now cty.NumberIntVal(0)
.token_validity_units: block count changed from 1 to 0
```

**Cause:** Floci creates the User Pool Client successfully but does not return the token validity fields in the response. The Terraform AWS provider compares what it set with what was returned, finds zeros, and throws an inconsistency error.

**Workaround:** remove `access_token_validity`, `id_token_validity`, `refresh_token_validity`, and `token_validity_units` from the `aws_cognito_user_pool_client` resource when targeting Floci.

```hcl
# floci — simplified client without token validity fields
resource "aws_cognito_user_pool_client" "spa" {
  name            = "${var.project}-spa-client"
  user_pool_id    = aws_cognito_user_pool.main.id
  generate_secret = false
}

# aws production — full configuration
resource "aws_cognito_user_pool_client" "spa" {
  name            = "${var.project}-spa-client"
  user_pool_id    = aws_cognito_user_pool.main.id
  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  prevent_user_existence_errors = "ENABLED"
}
```

---

### 3. Cognito User Pool Client — `explicit_auth_flows` not returned after apply

**Error:**
```
.explicit_auth_flows: planned set element cty.StringVal("ALLOW_USER_PASSWORD_AUTH")
does not correlate with any element in actual.
```

**Cause:** same root cause as above — Floci does not return `explicit_auth_flows` in the create response.

**Workaround:** remove `explicit_auth_flows` from the client resource when targeting Floci (included in workaround #2 above).

---

### 4. Cognito User Pool Client — `prevent_user_existence_errors` not returned

**Error:**
```
.prevent_user_existence_errors: was cty.StringVal("ENABLED"), but now cty.StringVal("")
```

**Cause:** same pattern — field is not returned in the Floci response.

**Workaround:** remove `prevent_user_existence_errors` when targeting Floci (included in workaround #2 above).

---

### 5. RDS — Docker socket must be mounted

**Error in Floci logs:**
```
Caused by: java.net.SocketException: No such file or directory
  at UnixDomainSockets.connect0 ...
  at com.github.dockerjava.transport.UnixSocket
```

**Cause:** Floci spins up RDS as a real Docker container. To do this, it needs access to the host Docker Engine via the Unix socket. If the socket is not mounted, Floci cannot create any container-based service (RDS, Lambda, ElastiCache, ECS).

**Fix:** mount the Docker socket in `docker-compose.yml`:

```yaml
services:
  floci:
    image: floci/floci:latest
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock  # required for rds, lambda, ecs
```

---

### Summary table

| Service | Feature | Floci | AWS |
|---|---|---|---|
| RDS | `AddTagsToResource` | ❌ not supported | ✅ |
| RDS | container spin-up | needs Docker socket mounted | managed |
| Cognito Client | `explicit_auth_flows` | ❌ not returned after apply | ✅ |
| Cognito Client | `access_token_validity` | ❌ not returned after apply | ✅ |
| Cognito Client | `refresh_token_validity` | ❌ not returned after apply | ✅ |
| Cognito Client | `id_token_validity` | ❌ not returned after apply | ✅ |
| Cognito Client | `token_validity_units` | ❌ not returned after apply | ✅ |
| Cognito Client | `prevent_user_existence_errors` | ❌ not returned after apply | ✅ |
| S3 | basic operations | ✅ | ✅ |
| DynamoDB | basic operations | ✅ | ✅ |
| Cognito | user pool CRUD | ✅ | ✅ |

---

## Repository structure

```
.
├── docker-compose.yml              # floci + local environment
├── floci.sh                        # env vars for aws cli → floci
├── .gitignore
├── backend/
│   └── app/
│       ├── routers/                # auth, board, tasks, columns
│       ├── middleware/             # jwt validation
│       └── schemas/                # pydantic models
├── frontend/                       # static SPA
├── terraform/
│   ├── provider.tf                 # aws provider + floci endpoints + s3 backend
│   ├── variables.tf
│   ├── main.tf                     # module orchestration
│   ├── outputs.tf
│   ├── terraform.tfvars            # secret values — never commit
│   ├── terraform.tfvars.example    # reference for new contributors
│   └── modules/
│       ├── cognito/                # user pool + app client
│       ├── rds/                    # postgresql instance
│       ├── lambda/                 # function + iam role
│       └── s3/                     # frontend bucket + cloudfront
└── .github/
    └── workflows/
        └── deploy.yml              # ci/cd pipeline
```

---

## Getting started

### prerequisites

- Docker Desktop
- Python 3.12
- AWS CLI v2
- Terraform >= 1.7

### run locally

```bash
# 1. start floci
docker compose up -d

# 2. load aws cli env vars
source floci.sh

# 3. create remote state backend (first time only)
aws s3 mb s3://kanban-tfstate
aws dynamodb create-table \
  --table-name kanban-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 4. provision infrastructure
cd terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your values
terraform init
terraform apply
```

---

*project in progress — new stacks and features being added incrementally.*