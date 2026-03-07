# ApplyFlow

> **A production-grade, cloud-native job application pipeline for SRE/DevOps/Cloud roles.**

[![CI](https://github.com/piriyajeishree410/applyflow/actions/workflows/ci.yml/badge.svg)](https://github.com/piriyajeishree410/applyflow/actions/workflows/ci.yml)
[![Deploy](https://github.com/piriyajeishree410/applyflow/actions/workflows/deploy.yml/badge.svg)](https://github.com/piriyajeishree410/applyflow/actions/workflows/deploy.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Terraform](https://img.shields.io/badge/terraform-1.14-purple.svg)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-ECS%20%7C%20RDS%20%7C%20S3-orange.svg)](https://aws.amazon.com/)

---

## Overview

ApplyFlow is an end-to-end automated job discovery and application tracking platform built for early-career SRE, DevOps, and Cloud Infrastructure candidates. It ingests job postings from multiple sources, scores them against a candidate's resume using NLP-based matching, tracks application outcomes, and surfaces analytics to optimize job search strategy.

The system is engineered at production grade - containerized microservices on AWS ECS Fargate, infrastructure provisioned via Terraform, CI/CD automated through GitHub Actions, and full observability through CloudWatch structured logging and custom metric alarms.

**Live Demo:** [applyflow.streamlit.app](https://applyflow.streamlit.app)  
**API Docs:** [http://3.236.21.187:8000/docs](http://3.236.21.187:8000/docs)

---

## Why This Exists

Existing job search tools (Teal, Huntr, Kickresume) cost $10–30/month and offer limited customization. For students and early-career candidates who most need structured tracking and feedback loops, the cost is prohibitive and the tooling is generic.

ApplyFlow solves this by being:
- **Free to run** - near-zero AWS cost via scheduled Fargate tasks and free-tier RDS
- **Configurable** - each user defines their own role keywords, tech stack, and experience level
- **Feedback-driven** - application outcomes feed back into analytics to improve strategy over time
- **Self-demonstrating** - the system itself demonstrates the SRE/DevOps/Cloud skills it helps you find jobs for

---

## Architecture

### System Overview

```mermaid
graph TB
    subgraph Sources["Job Sources"]
        GH[Greenhouse API]
        LV[Lever API]
        RSS[RSS Feeds]
    end

    subgraph AWS["AWS Cloud"]
        subgraph ECS["ECS Fargate"]
            W[Ingestion Worker<br/>Scheduled Task]
            API[FastAPI Service<br/>Always-on]
        end
        RDS[(RDS PostgreSQL)]
        S3[(S3 Bucket<br/>Embeddings & Artifacts)]
        ECR[ECR<br/>Container Registry]
        CW[CloudWatch<br/>Logs & Metrics]
        SNS[SNS<br/>Alert Notifications]
        EB[EventBridge<br/>Scheduler]
    end

    subgraph CI["CI/CD"]
        GHA[GitHub Actions<br/>Test → Build → Deploy]
    end

    subgraph UI["User Interface"]
        ST[Streamlit Dashboard<br/>applyflow.streamlit.app]
    end

    GH --> W
    LV --> W
    RSS --> W
    EB -->|every 6 hours| W
    W --> RDS
    W --> S3
    W --> CW
    CW --> SNS
    GHA --> ECR
    ECR --> W
    ECR --> API
    API --> RDS
    ST --> API
```

### Layered Application Architecture

```mermaid
graph TD
    A[UI Layer<br/>Streamlit Dashboard] -->|HTTP| B[API Layer<br/>FastAPI]
    B --> C[Domain Layer<br/>Job · Resume · Scoring · Profile]
    C --> D[Services Layer<br/>Collectors · Parser · Embeddings]
    C --> E[Infrastructure Layer<br/>Repositories · DB · AWS Clients]
    E --> F[(PostgreSQL<br/>RDS / SQLite)]
    D --> G[External APIs<br/>Greenhouse · Lever · RSS]
```

### CI/CD Pipeline

```mermaid
graph LR
    PR[Pull Request] --> CI{CI Workflow}
    CI -->|lint| R[ruff check]
    CI -->|test| T[pytest unit tests]
    T -->|pass| M[Merge to main]
    M --> CD{Deploy Workflow}
    CD --> B[Docker Build]
    B --> P[Push to ECR]
    P --> W[Update Worker<br/>Task Definition]
    P --> A[Update API<br/>Task Definition]
    A --> S[ECS Service<br/>Rolling Deploy]
```

### Ingestion Pipeline Flow

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant W as Ingestion Worker
    participant GH as Greenhouse API
    participant P as Parser
    participant SC as Scoring Engine
    participant DB as RDS PostgreSQL
    participant CW as CloudWatch

    EB->>W: Trigger (every 6 hours)
    W->>GH: Fetch job listings
    GH-->>W: Raw job titles + locations
    W->>GH: Fetch full descriptions (per relevant job)
    GH-->>W: HTML job descriptions
    W->>P: Extract skills + YOE
    P-->>W: Structured features
    W->>SC: Score against resume profile
    SC-->>W: ScoreResult (0-100, missing skills)
    W->>DB: Save job + application (dedup check)
    W->>CW: Publish metrics (fetched, saved, failures, duration)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.13 |
| **API Framework** | FastAPI + Uvicorn |
| **Dashboard** | Streamlit |
| **ORM / DB** | psycopg2 + SQLite (local dev) |
| **Database** | PostgreSQL 16 (AWS RDS t3.micro) |
| **Compute** | AWS ECS Fargate |
| **Container Registry** | AWS ECR |
| **Object Storage** | AWS S3 |
| **Scheduling** | AWS EventBridge Scheduler |
| **Monitoring** | AWS CloudWatch (logs + custom metrics) |
| **Alerting** | AWS SNS + Email |
| **IaC** | Terraform 1.14 |
| **CI/CD** | GitHub Actions |
| **Secrets** | AWS Secrets Manager |
| **Package Manager** | uv |
| **Linting** | ruff |

---

## Repository Structure

```
applyflow/
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint + test on every PR and push
│       └── deploy.yml          # Build → ECR → ECS deploy on merge to main
│
├── api/                        # FastAPI application
│   ├── main.py                 # App entrypoint, health endpoint
│   └── routes/
│       ├── jobs.py             # GET /jobs, POST /jobs/ingest
│       ├── applications.py     # GET /applications, PATCH /applications/{id}
│       ├── analytics.py        # GET /analytics/conversion, /skills-gap
│       └── profiles.py         # GET/POST /profiles
│
├── app/
│   └── dashboard.py            # Streamlit UI - calls API only, no DB access
│
├── domain/                     # Pure business logic - no external dependencies
│   ├── job.py                  # Job dataclass
│   ├── resume.py               # ResumeProfile dataclass
│   ├── application.py          # Application dataclass + ApplicationStatus enum
│   ├── scoring.py              # ScoringEngine + ScoreResult
│   └── profile.py              # SearchProfile + ExperienceLevel + LocationPref
│
├── services/                   # External interactions
│   ├── collectors/
│   │   ├── base.py             # Abstract JobCollector interface
│   │   ├── greenhouse.py       # Greenhouse public API collector
│   │   └── lever.py            # Lever public API collector
│   ├── embedding_service.py    # Embedding abstraction
│   └── parser.py               # JD parsing - skills + YOE extraction
│
├── infrastructure/             # DB and persistence layer
│   ├── database.py             # Connection management (Postgres + SQLite)
│   ├── models.py               # Table definitions
│   └── repositories.py         # JobRepo, ApplicationRepo, ProfileRepo
│
├── workers/
│   └── ingestion_worker.py     # Full pipeline orchestration
│
├── monitoring/
│   └── metrics.py              # CloudWatch custom metric publishers
│
├── infra/                      # Terraform - all AWS resources
│   ├── main.tf                 # Provider + VPC data sources
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Resource outputs
│   ├── ecr.tf                  # Container registry + lifecycle policy
│   ├── rds.tf                  # PostgreSQL + security group
│   ├── s3.tf                   # Artifacts bucket
│   ├── iam.tf                  # ECS execution + task + EventBridge roles
│   ├── ecs.tf                  # Cluster + worker task definition
│   ├── api_service.tf          # FastAPI ECS service (always-on)
│   ├── eventbridge.tf          # Scheduled ingestion trigger
│   └── monitoring.tf           # CloudWatch alarms + SNS topic
│
├── tests/
│   ├── unit/
│   │   ├── test_scoring.py     # ScoringEngine unit tests
│   │   └── test_parser.py      # Parser unit tests
│   └── integration/            # End-to-end pipeline tests
│
├── config/
│   └── config.yaml             # Scoring weights, source toggles
│
├── .streamlit/
│   └── requirements.txt        # Streamlit Cloud dependencies
│
├── Dockerfile                  # Lean production image (~300MB)
├── docker-compose.yml          # Local dev stack (API + dashboard + Postgres)
├── main.py                     # Worker entrypoint
├── pyproject.toml              # Python project config + dependencies
└── CONTEXT.md                  # Build context for session continuity
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker Desktop
- AWS CLI configured (`aws configure`)
- Terraform 1.14+

### Local Development

```bash
# Clone the repository
git clone https://github.com/piriyajeishree410/applyflow.git
cd applyflow

# Install dependencies
uv sync

# Start local Postgres
docker compose up -d

# Run the ingestion pipeline
DATABASE_URL='postgresql://applyflow:applyflow@localhost:5432/applyflow' \
python3 main.py

# Start the API
DATABASE_URL='postgresql://applyflow:applyflow@localhost:5432/applyflow' \
PYTHONPATH=$(pwd) uvicorn api.main:app --reload --port 8000

# Start the dashboard (separate terminal)
PYTHONPATH=$(pwd) streamlit run app/dashboard.py
```

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Lint
uv run ruff check .
```

---

## AWS Infrastructure

### Provisioning

```bash
cd infra
terraform init
terraform plan -var="db_password=<password>" -var="alert_email=<email>"
terraform apply -var="db_password=<password>" -var="alert_email=<email>"
```

### Resources Created (16 core + 6 monitoring)

| Resource | Service | Purpose |
|---|---|---|
| ECS Cluster | Fargate | Runs worker + API containers |
| Worker Task | Fargate Scheduled | Ingestion pipeline - runs every 6 hours, exits |
| API Service | Fargate Always-on | FastAPI - serves dashboard and external clients |
| PostgreSQL | RDS t3.micro | Persistent storage - jobs, applications, profiles |
| Container Registry | ECR | Docker image storage with lifecycle policy |
| Object Storage | S3 | Job embeddings and pipeline artifacts |
| Scheduler | EventBridge | Triggers ingestion worker every 6 hours |
| Log Groups | CloudWatch | Structured JSON logs from all services |
| Custom Metrics | CloudWatch | JobsFetched, JobsSaved, Failures, Duration |
| Alarms | CloudWatch | Failure count, ingestion staleness, task health |
| Alerts | SNS + Email | Notifies on alarm state transitions |
| Secrets | IAM Roles | Least-privilege task execution and access |

### Estimated Monthly Cost

| Resource | Cost |
|---|---|
| ECS Fargate (worker, ~2hrs/day) | ~$1–2 |
| ECS Fargate (API, always-on, 256 CPU) | ~$3–4 |
| RDS t3.micro (Free Tier, 12 months) | $0 |
| S3 (<1GB) | ~$0.02 |
| CloudWatch (within free tier) | $0 |
| ECR, EventBridge, SNS | ~$0 |
| **Total** | **~$4–6/month** |

---

## API Reference

Base URL: `http://3.236.21.187:8000`  
Interactive docs: `http://3.236.21.187:8000/docs`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health - DB status, job counts, timestamp |
| `GET` | `/jobs` | List scored jobs - filterable by company, status, score |
| `POST` | `/jobs/ingest` | Manually trigger ingestion pipeline |
| `GET` | `/applications` | List all applications with scores |
| `PATCH` | `/applications/{job_id}` | Update application status |
| `GET` | `/analytics/conversion` | Interview and offer conversion rates |
| `GET` | `/analytics/skills-gap` | Top 10 missing skills across all jobs |
| `GET` | `/profiles` | List all active search profiles |
| `POST` | `/profiles` | Create a new user search profile |
| `GET` | `/profiles/{user_id}` | Get a specific user's profile |

### Example: Health Check

```bash
curl http://3.236.21.187:8000/health
```

```json
{
    "status": "ok",
    "db": "connected",
    "timestamp": "2026-03-05T04:50:00.586538",
    "total_jobs": 145,
    "total_applications": 145
}
```

### Example: Skills Gap Analysis

```bash
curl http://3.236.21.187:8000/analytics/skills-gap
```

```json
{
    "top_missing_skills": [
        {"skill": "go", "count": 133},
        {"skill": "dns", "count": 89},
        {"skill": "kubernetes", "count": 45}
    ]
}
```

---

## Observability

### CloudWatch Custom Metrics (Namespace: `ApplyFlow`)

| Metric | Description | Alert Threshold |
|---|---|---|
| `JobsFetched` | Total jobs collected per run | — |
| `JobsSaved` | New jobs persisted per run | — |
| `DuplicatesSkipped` | Deduplication count per run | — |
| `IngestionFailures` | Collector-level failures | ≥ 1 → SNS alert |
| `IngestionDurationSeconds` | Total worker run time | — |
| `LastSuccessfulRun` | Heartbeat — published on clean runs | Missing for 9h → SNS alert |

### Structured Log Format

All services emit JSON-structured logs to CloudWatch Logs (`/ecs/applyflow`):

```json
{
  "timestamp": "2026-03-05T04:48:27Z",
  "service": "ingestion_worker",
  "level": "INFO",
  "event": "cycle_complete",
  "saved": 142,
  "skipped_dup": 17,
  "failed": 0,
  "duration_seconds": 132.4
}
```

---

## Build History (Vertical Slices)

| Slice | What Was Built | Key Technical Decisions |
|---|---|---|
| **1** | Local pipeline - Greenhouse collector, keyword scorer, SQLite, Streamlit | Validate core loop before adding complexity |
| **2** | Full JD descriptions, Postgres, ingestion worker abstraction | Repository pattern - DB swap without touching domain |
| **3** | Docker, AWS ECS + RDS + S3, Terraform, EventBridge scheduler | Scheduled Fargate tasks - zero idle cost |
| **4** | GitHub Actions CI/CD, FastAPI, health endpoint, unit tests | Every push auto-deploys - no manual steps |
| **5** | CloudWatch metrics + alarms, SNS alerts, multi-user profiles, public deployment | Observable, alertable, generalizable |

---

## Security

- All secrets in AWS Secrets Manager - never in code or environment variables
- RDS accessible only via VPC security group - not publicly exposed at DB level
- ECS task IAM roles scoped to minimum required permissions (least privilege)
- S3 bucket: private ACL, all public access blocked
- No auto-apply functionality - all submissions require explicit user action
- All data collection from public APIs only - no ToS violations

---

## Testing

```
tests/
├── unit/
│   ├── test_scoring.py     # 7 tests - ScoringEngine logic
│   └── test_parser.py      # 8 tests - skill + YOE extraction
└── integration/            # End-to-end pipeline tests
```

All unit tests run on every pull request via GitHub Actions. Merges to `main` are blocked on test failure.

---

## Roadmap

- [ ] Lever + RSS collectors (Slice 2 extension)
- [ ] Semantic embedding scoring (sentence-transformers)
- [ ] Application Load Balancer for stable API URL
- [ ] Multi-user authentication (JWT)
- [ ] Interview prep module - auto-generate questions from JD
- [ ] Market trend dashboard - skill demand over time
- [ ] Terraform remote state (S3 backend)

---

## Author

**Piriyajeishree Murali Naidu**  
MS Computer Science, Northeastern University  
Seeking 2026 Co-op - SRE / DevOps / Cloud Infrastructure

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/piriyajeishree)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/piriyajeishree410)

---

## License

MIT License - see [LICENSE](LICENSE) for details.