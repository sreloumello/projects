# Kanban DevOps

Personal project to study and practice DevOps concepts. A kanban board used as a base application to explore different ways of provisioning and operating infrastructure — all as code with Terraform.

The app is not the focus — it is the vehicle. The goal is to understand in practice the differences between infrastructure stacks, deployment strategies, and cloud-native services.

All infrastructure runs locally using [Floci](https://github.com/floci-io/floci), a free open-source AWS emulator. This was a deliberate choice to eliminate cloud costs during development while keeping the infrastructure code identical to what would run on real AWS — the same Terraform modules, the same Cognito auth flow, the same RDS PostgreSQL. A cost estimate for running this stack on AWS is included at the end of this document for reference.

---

## What was built

A full-stack kanban board with authentication, public read access, and protected write access — provisioned entirely as code, running locally with zero cloud cost.

### Features

- public board — anyone can view columns and tasks without logging in
- authentication — register, confirm email, login, logout, session persistence
- protected writes — only authenticated users can create, move, or delete tasks
- drag and drop — tasks can be dragged between columns
- session management — refresh token stored in HttpOnly cookie, access token kept in memory only

### Tech stack

| Layer | Technology |
|---|---|
| Local AWS emulation | Floci |
| Infrastructure as Code | Terraform |
| Configuration management | Ansible |
| Orchestration | Makefile |
| Backend | Python, FastAPI, Mangum, psycopg2 |
| Auth | AWS Cognito, JWT RS256 |
| Database | PostgreSQL 16 |
| Frontend | React 18, Vite, @dnd-kit |
| Containers | Docker, Docker Compose, Nginx |
| CI/CD | GitHub Actions *(coming soon)* |

---

## Architecture

All services run inside a single Docker network. This mirrors production — the database is never directly reachable from outside the network, just like RDS in a private VPC.

```
your machine
│
│  ┌──────────────────────────────────────────────┐
│  │  network: kanban-devops_default              │
│  │                                              │
│  │  kanban-floci        → aws emulation         │
│  │  floci-rds-kanban-db → postgresql            │
│  │  kanban-api          → fastapi               │
│  │  kanban-frontend     → react + nginx         │
│  │                                              │
│  └──────────────────────────────────────────────┘
│
├── localhost:4566  →  floci      (aws cli)
├── localhost:8000  →  api        (rest api)
└── localhost:3000  →  frontend   (kanban board)

floci-rds-kanban-db has no published port
```

### Why not use a TCP proxy?

An earlier approach used a `socat` container to forward port 5432 from the RDS container to the host, so the API could connect via `localhost:5432`. This was replaced because:

- breaks dev/prod parity — in production the database is never reachable from outside the network
- exposes the database to the host — any process on the machine can connect, not just the API
- adds an unnecessary failure point
- masks real connectivity issues that would surface in production

Running everything inside the Docker network means the connectivity model is identical to production from day one.

### Infrastructure provisioned by Terraform

```
Cognito User Pool
  └── App Client (SPA — no client secret)

RDS PostgreSQL 16
  └── db.t3.micro, 20GB
  └── provisioned as a real Docker container by Floci

S3 bucket (remote state)
DynamoDB table (state lock)
```

### Database managed by Ansible

```
ansible/roles/db_setup/
  ├── tasks/main.yml   → ping db, run sql, verify tables and seed
  └── files/init.sql   → creates users, columns, tasks tables + 4 default columns
```

Ansible runs inside the Docker network via `docker compose run`, connecting directly to the RDS container by name.

---

## Authentication flow

```
1. user submits email + password
2. frontend calls POST /auth/login
3. api calls cognito with credentials
4. cognito validates and returns 3 tokens
5. api sets refresh_token as HttpOnly cookie (30 days)
6. api returns access_token + id_token to frontend
7. frontend stores access_token in memory only
8. every api request sends: Authorization: Bearer <access_token>
9. when access_token expires (1h), frontend calls POST /auth/refresh
10. api reads cookie, cognito issues new tokens silently
```

The access token is never written to localStorage or sessionStorage — it lives only in a JavaScript variable and disappears when the tab closes. The refresh token is in an HttpOnly cookie, invisible to JavaScript, protecting against XSS.

---

## API endpoints

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

## Running locally

### Prerequisites

- Docker Desktop
- Terraform >= 1.7
- Ansible
- AWS CLI v2
- Make

### First time setup

```bash
# clone the repo
git clone <repo-url>
cd kanban-devops

# copy and fill in db credentials
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# edit terraform/terraform.tfvars

# create floci.sh with local aws credentials
cat > floci.sh << 'EOF'
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
EOF

# load floci environment
source floci.sh

# create remote state backend (one time only)
aws s3 mb s3://kanban-tfstate
aws dynamodb create-table \
  --table-name kanban-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# full setup
make setup
```

Open `http://localhost:3000`

### Daily workflow

```bash
# start everything
make infra
make api
make frontend

# stop everything (preserves state)
make down

# destroy everything
make destroy
```

### Make targets

| Target | Description |
|---|---|
| `make setup` | full setup — infra + db + api + frontend |
| `make infra` | start floci, provision cognito and rds, wait for rds healthy |
| `make db` | run ansible — create tables and seed default columns |
| `make api` | build and start the api container |
| `make frontend` | build and start the frontend container |
| `make down` | stop all containers, preserve terraform state |
| `make destroy` | destroy all infrastructure and stop containers |
| `make help` | list available targets |

---

## Repository structure

```
.
├── docker-compose.yml
├── floci.sh                       # gitignored — fake aws credentials for floci
├── Makefile
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                # fastapi app + mangum lambda handler
│       ├── config.py              # settings from environment variables
│       ├── database.py            # postgresql connection
│       ├── middleware/auth.py     # jwt validation via cognito jwks
│       ├── schemas/models.py      # pydantic models
│       └── routers/
│           ├── auth.py            # register, login, refresh, logout
│           ├── board.py           # public board read
│           ├── tasks.py           # task crud
│           └── columns.py        # column crud
├── frontend/
│   ├── Dockerfile                 # multi-stage: node build + nginx serve
│   ├── nginx.conf                 # spa routing + gzip + cache headers
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── services/api.js        # all api calls, token management
│       ├── context/AuthContext.jsx
│       ├── hooks/useBoard.js
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   └── BoardPage.jsx
│       └── components/
│           ├── Board.jsx          # dnd context and drag logic
│           ├── Column.jsx         # droppable column
│           ├── TaskCard.jsx       # draggable task
│           └── AddTaskModal.jsx
├── ansible/
│   ├── playbook.yml
│   ├── inventory/local.yml
│   └── roles/db_setup/
│       ├── tasks/main.yml         # ping, run sql, verify
│       └── files/init.sql         # schema + seed
└── terraform/
    ├── provider.tf                # aws provider + s3 backend + floci endpoints
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── terraform.tfvars.example
    └── modules/
        ├── cognito/               # user pool + app client
        └── rds/                   # postgresql instance
```

---

## Floci vs AWS — known differences

| Service | Feature | Floci | AWS |
|---|---|---|---|
| RDS | `AddTagsToResource` | not supported | supported |
| RDS | host resolution | container name via docker dns | managed endpoint |
| RDS | docker socket | must be mounted | not applicable |
| Cognito | `explicit_auth_flows` | not returned after apply | supported |
| Cognito | `access_token_validity` | not returned after apply | supported |
| Cognito | `refresh_token_validity` | not returned after apply | supported |
| Cognito | `id_token_validity` | not returned after apply | supported |
| Cognito | `prevent_user_existence_errors` | not returned after apply | supported |
| Cognito | `AdminConfirmSignUp` | not supported | supported |
| Cognito | token issuer | `http://localhost:4566/{pool_id}` | `https://cognito-idp.{region}.amazonaws.com/{pool_id}` |

---

## AWS cost estimate

If deploying this stack to real AWS, the following services are covered under the free tier:

| Service | Free tier | Cost |
|---|---|---|
| Lambda | 1M req/month | $0 |
| API Gateway HTTP v2 | 1M req/month | $0 |
| S3 | 5 GB + 20K req | $0 |
| CloudFront | 1 TB transfer | $0 |
| RDS t3.micro | 750h/month (first year) | $0 |
| Cognito | 50K MAU/month | $0 |
| Secrets Manager | 1 secret | ~$0.40 |

Total estimated cost: **~$0.40/month** (first year), **~$15/month** after free tier expires (RDS).