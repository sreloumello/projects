# Kanban DevOps

Personal project to study and practice DevOps concepts. A kanban board used as a base application to explore different ways of provisioning and operating infrastructure — all as code with Terraform.

The app is not the focus — it is the vehicle. The goal is to understand in practice the differences between infrastructure stacks, deployment strategies, and cloud-native services.

All infrastructure runs locally using [Floci](https://github.com/floci-io/floci), a free open-source AWS emulator. This was a deliberate choice to eliminate cloud costs during development while keeping the infrastructure code identical to what would run on real AWS — the same Terraform modules, the same Cognito auth flow, the same RDS PostgreSQL. A cost estimate for running this stack on AWS is included at the end of this document for reference.

---

## The application

A kanban board with authentication, public read access, and protected write access.

- **Frontend:** static SPA *(coming soon)*
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL via RDS
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

### Stack 1 — Lambda + API Gateway + RDS + S3 + CloudFront *(coming soon)*

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

## Local development with Floci

[Floci](https://github.com/floci-io/floci) emulates AWS services locally in a single Docker container. No account, no cost, no internet required.

### Prerequisites

- Docker Desktop
- Terraform >= 1.7
- Ansible
- AWS CLI v2
- Make

### Quick start

```bash
# 1. clone the repo
git clone <repo-url>
cd kanban-devops

# 2. copy and fill in credentials
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# edit terraform/terraform.tfvars with your db credentials

# 3. load floci environment
source floci.sh

# 4. create remote state backend (first time only)
aws s3 mb s3://kanban-tfstate
aws dynamodb create-table \
  --table-name kanban-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 5. full setup
make setup
```

### Make targets

| Target | Description |
|---|---|
| `make setup` | full setup — infra + db + api |
| `make infra` | start floci + provision cognito and rds via terraform + wait for rds healthy |
| `make db` | configure tables and seed data via ansible |
| `make api` | build and start the api container |
| `make down` | stop all services |
| `make destroy` | stop services and destroy all infrastructure |
| `make help` | list available targets |

### Running step by step

```bash
# provision infrastructure
make infra

# configure database
make db

# start api
make api
```

API available at `http://localhost:8000`
Docs available at `http://localhost:8000/docs`

---

## Docker network architecture

All services run inside a single Docker network (`kanban-devops_default`). This is a deliberate choice — not a workaround.

```
your machine (host)
│
│  ┌─────────────────────────────────────────────────┐
│  │  network: kanban-devops_default                 │
│  │                                                 │
│  │  kanban-floci          → aws emulation          │
│  │  floci-rds-kanban-db   → postgresql             │
│  │  kanban-api            → fastapi                │
│  │                                                 │
│  └─────────────────────────────────────────────────┘
│
├── localhost:4566  →  kanban-floci  (aws cli access)
└── localhost:8000  →  kanban-api    (api access)

floci-rds-kanban-db has no published port — only reachable inside the network
```

Inside the network, containers communicate by name. Docker has an internal DNS that resolves `floci-rds-kanban-db` to the correct IP automatically — the same pattern used in production where Lambda connects to RDS via DNS endpoint, never by IP.

### Why not use a TCP proxy (socat)?

An earlier approach used a `socat` container to forward port `5432` from the RDS container to the host, allowing the API to run locally and connect via `localhost:5432`.

This was replaced because:

- **breaks dev/prod parity** — in production the database is never directly reachable from outside the network. The proxy hides this boundary.
- **exposes the database to the host** — any process on your machine can connect to port 5432, not just the API
- **adds an unnecessary failure point** — one more container that can crash or misbehave
- **masks real connectivity issues** — if something breaks in production because the DB is unreachable inside the network, the proxy would have hidden that problem during development

Running the API inside the Docker network means the connectivity model is identical to production from day one.

---

## Credentials and secrets

No credentials are stored in the repository or in `docker-compose.yml`. All sensitive values are injected at runtime by the Makefile:

| Value | Source |
|---|---|
| `DB_NAME` | `terraform output` |
| `DB_USER` | `terraform.tfvars` (gitignored) |
| `DB_PASSWORD` | `terraform.tfvars` (gitignored) |
| `DB_HOST` | `docker ps` — resolved dynamically from the running rds container name |
| `COGNITO_USER_POOL_ID` | `terraform output` |
| `COGNITO_CLIENT_ID` | `terraform output` |
| `AWS_ACCESS_KEY_ID` | `floci.sh` (gitignored) |
| `AWS_SECRET_ACCESS_KEY` | `floci.sh` (gitignored) |
| `AWS_ENDPOINT_URL` | `floci.sh` (gitignored) |

`floci.sh` uses fake credentials (`test`/`test`) accepted by Floci. It is gitignored to establish the habit of never committing credential files, even fake ones.

---

## Floci vs AWS — known differences

These are incompatibilities found during development. Each one requires a code or configuration change when switching between local and production.

| Service | Feature | Floci | AWS |
|---|---|---|---|
| RDS | `AddTagsToResource` | not supported | supported |
| RDS | host resolution | container name via docker dns | managed endpoint |
| RDS | docker socket | must be mounted in compose | not applicable |
| Cognito | `explicit_auth_flows` | not returned after apply | supported |
| Cognito | `access_token_validity` | not returned after apply | supported |
| Cognito | `refresh_token_validity` | not returned after apply | supported |
| Cognito | `id_token_validity` | not returned after apply | supported |
| Cognito | `prevent_user_existence_errors` | not returned after apply | supported |
| Cognito | `AdminConfirmSignUp` | not supported | supported |
| Cognito | token issuer | `http://localhost:4566/{pool_id}` | `https://cognito-idp.{region}.amazonaws.com/{pool_id}` |

### AWS free tier reference

If deploying to AWS, the following services are covered by the free tier:

| Service | Free tier | Estimated cost |
|---|---|---|
| Lambda | 1M req/month | $0 |
| API Gateway | 1M req/month | $0 |
| S3 | 5 GB + 20K req | $0 |
| CloudFront | 1 TB transfer | $0 |
| RDS t3.micro | 750h/month (first year) | $0 |
| Cognito | 50K MAU/month | $0 |
| Secrets Manager | 1 secret | ~$0.40 |

---

## Repository structure

```
.
├── docker-compose.yml        # floci + api + ansible
├── floci.sh                  # aws cli env vars — gitignored
├── Makefile                  # infra, db, api, down, destroy
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # fastapi app + lambda handler
│       ├── config.py         # settings via env vars
│       ├── database.py       # postgresql connection
│       ├── middleware/
│       │   └── auth.py       # jwt validation via cognito jwks
│       ├── schemas/
│       │   └── models.py     # pydantic models
│       └── routers/
│           ├── auth.py       # register, login, refresh, logout
│           ├── board.py      # public board read
│           ├── tasks.py      # task crud
│           └── columns.py    # column crud
├── frontend/                 # static SPA (coming soon)
├── ansible/
│   ├── ansible.cfg
│   ├── playbook.yml
│   ├── inventory/
│   │   └── local.yml
│   └── roles/
│       └── db_setup/
│           ├── tasks/main.yml
│           └── files/init.sql
└── terraform/
    ├── provider.tf           # aws provider + s3 backend + floci endpoints
    ├── main.tf               # module orchestration
    ├── variables.tf
    ├── outputs.tf
    ├── terraform.tfvars.example
    └── modules/
        ├── cognito/          # user pool + app client
        ├── rds/              # postgresql instance
        ├── lambda/           # coming soon
        └── s3/               # coming soon
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Local emulation | Floci |
| IaC | Terraform |
| Configuration | Ansible |
| Orchestration | Makefile |
| Backend | Python, FastAPI, Mangum, psycopg2 |
| Auth | AWS Cognito, JWT (RS256) |
| Database | PostgreSQL 16 |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions *(coming soon)* |