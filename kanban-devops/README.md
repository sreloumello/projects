# Kanban DevOps

Personal project to study and practice DevOps concepts. A kanban board used as a base application to explore different ways of provisioning and operating infrastructure — all as code with Terraform.

The app is not the focus — it is the vehicle. The goal is to understand in practice the differences between infrastructure stacks, deployment strategies, and cloud-native services.

---

## The application

A kanban board with authentication, public read access, and protected write access.

- **Frontend:** static SPA served via S3 + CloudFront
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Auth:** AWS Cognito

### Access model

| Action | Auth required |
|---|---|
| View the board | no — public |
| Create / edit / move / delete tasks | yes |
| Create / edit / delete columns | yes |

### API endpoints

| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/health` | no | health check |
| GET | `/board` | no | full board with columns and tasks |
| POST | `/auth/register` | no | create account |
| POST | `/auth/confirm` | no | confirm email with code |
| POST | `/auth/login` | no | returns jwt tokens |
| POST | `/auth/refresh` | no | renew session via cookie |
| POST | `/auth/logout` | no | revoke session |
| POST | `/tasks` | yes | create task |
| PUT | `/tasks/{id}` | yes | update task |
| POST | `/tasks/{id}/move` | yes | move task to another column |
| DELETE | `/tasks/{id}` | yes | delete task |
| POST | `/columns` | yes | create column |
| PUT | `/columns/{id}` | yes | update column |
| DELETE | `/columns/{id}` | yes | delete column |

---

## Infrastructure stacks

Each stack provisions the same application with a different architecture, all via Terraform.

### Stack 1 — Lambda + API Gateway + RDS + S3 + CloudFront

```
user
 │
 ▼
CloudFront
 ├── /        →  S3 (static frontend)
 └── /api/*   →  API Gateway HTTP v2
                      │
                 Lambda (FastAPI + Mangum)
                      │
                 RDS PostgreSQL
                 Cognito (auth)
```

### Stack 2 — EC2 Multi-AZ *(coming soon)*

### Stack 3 — EKS *(coming soon)*

---

## Running locally — Floci

[Floci](https://github.com/floci-io/floci) emulates AWS services locally in a single Docker container. No account, no cost, no internet required.

```bash
# start floci
docker compose up -d

# load aws cli environment
source floci.sh

# provision infrastructure
make infra

# configure database
make db

# start api
cd backend
set -a && source .env.dev && set +a
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`
Docs available at `http://localhost:8000/docs`

### Floci vs AWS — known differences

These are incompatibilities found during development. Each one requires a code or configuration change when switching between environments.

| Service | Feature | Floci | AWS |
|---|---|---|---|
| RDS | `AddTagsToResource` | not supported | supported |
| RDS | access from host | requires socat proxy | direct endpoint |
| RDS | Docker socket | must be mounted in compose | not applicable |
| Cognito | `explicit_auth_flows` | not returned after apply | supported |
| Cognito | `access_token_validity` | not returned after apply | supported |
| Cognito | `refresh_token_validity` | not returned after apply | supported |
| Cognito | `id_token_validity` | not returned after apply | supported |
| Cognito | `prevent_user_existence_errors` | not returned after apply | supported |
| Cognito | `AdminConfirmSignUp` | not supported | supported |
| Cognito | token issuer | `http://localhost:4566/{pool_id}` | `https://cognito-idp.{region}.amazonaws.com/{pool_id}` |

---

## Running on AWS

```bash
# configure aws credentials
aws configure

# provision infrastructure
make infra ENV=aws

# configure database
make db ENV=aws

# build and deploy lambda
./build_lambda.sh
aws lambda update-function-code \
  --function-name kanban-api \
  --zip-file fileb://lambda_package.zip

# deploy frontend to s3
aws s3 sync frontend/ s3://$(cd terraform && terraform output -raw s3_bucket_name)/
aws cloudfront create-invalidation \
  --distribution-id $(cd terraform && terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Estimated cost — AWS free tier (first year)

| Service | Free tier | Cost |
|---|---|---|
| Lambda | 1M req/month | $0 |
| API Gateway | 1M req/month | $0 |
| S3 | 5 GB + 20K req | $0 |
| CloudFront | 1 TB transfer | $0 |
| RDS t3.micro | 750h/month | $0 |
| Cognito | 50K MAU/month | $0 |
| Secrets Manager | 1 secret | ~$0.40 |

---

## Repository structure

```
.
├── docker-compose.yml        # floci + db proxy + ansible
├── floci.sh                  # aws cli env vars for floci
├── Makefile                  # infra, db, destroy
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # fastapi app + lambda handler
│       ├── config.py         # settings via env vars
│       ├── database.py       # postgresql connection
│       ├── middleware/
│       │   └── auth.py       # jwt validation
│       ├── schemas/
│       │   └── models.py     # pydantic models
│       └── routers/
│           ├── auth.py       # register, login, refresh, logout
│           ├── board.py      # public board read
│           ├── tasks.py      # task crud
│           └── columns.py    # column crud
├── frontend/                 # static SPA (coming soon)
├── ansible/
│   ├── playbook.yml
│   ├── inventory/
│   └── roles/
│       └── db_setup/         # creates tables and seed data
└── terraform/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── provider.tf
    └── modules/
        ├── cognito/
        ├── rds/
        ├── lambda/           # coming soon
        └── s3/               # coming soon
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Cloud | AWS (Lambda, API Gateway, RDS, Cognito, S3, CloudFront) |
| Local emulation | Floci |
| IaC | Terraform |
| Configuration | Ansible |
| Orchestration | Makefile |
| Backend | Python, FastAPI, Mangum, psycopg2 |
| Auth | AWS Cognito, JWT (RS256) |
| Database | PostgreSQL 16 |
| CI/CD | GitHub Actions *(coming soon)* |