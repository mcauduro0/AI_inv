# Investment Agent System

A state-of-the-art agentic AI system for systematic investment research and idea generation. This platform acts as a team of top-tier investment analysts, automating the entire investment research process from idea generation to thesis development.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [API Reference](#api-reference)
- [Agent Library](#agent-library)
- [Prompt Library](#prompt-library)
- [Troubleshooting](#troubleshooting)

## Overview

The Investment Agent System is a comprehensive platform that leverages multiple specialized AI agents to conduct investment research at institutional quality. Built on a microservices architecture, it provides:

- **Automated Idea Generation**: Scan newsletters, SEC filings, social media, and thematic trends
- **Comprehensive Due Diligence**: Business model analysis, financial deep dives, competitive positioning
- **Risk Assessment**: Multi-factor risk analysis with bear case development
- **Valuation Analysis**: DCF, comparable analysis, and scenario modeling
- **Workflow Orchestration**: Prefect-based pipelines for systematic research processes

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React + TypeScript)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                              API Gateway                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                         Master Control Agent                             │
│                    (Orchestration & Task Routing)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Idea Gen     │  │ Due Diligence│  │ Risk         │  │ Valuation    │ │
│  │ Agent        │  │ Agent        │  │ Agent        │  │ Agent        │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│                         Workflow Engine (Prefect)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ PostgreSQL   │  │ Redis        │  │ Qdrant       │  │ S3/Minio     │ │
│  │ (Primary DB) │  │ (Pub/Sub)    │  │ (Vector DB)  │  │ (Documents)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- API Keys (see [Configuration](#configuration))

### 1. Clone the Repository

```bash
git clone https://github.com/mcauduro0/AI_inv.git
cd AI_inv
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 3. Start the System

```bash
# Run the setup script (recommended)
./scripts/setup-local.sh

# Or manually with Docker Compose
docker-compose up -d
```

### 4. Access the System

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web application |
| API Gateway | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Prefect UI | http://localhost:4200 | Workflow management |
| MinIO Console | http://localhost:9001 | Object storage |
| Grafana | http://localhost:3001 | Monitoring dashboards |

## Configuration

### Required API Keys

Add these to your `.env` file:

```bash
# =============================================================================
# LLM Providers (at least one required)
# =============================================================================
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GEMINI_API_KEY=your-gemini-key
SONAR_API_KEY=your-perplexity-key

# Default provider
DEFAULT_LLM_PROVIDER=openai

# =============================================================================
# Financial Data Providers (recommended)
# =============================================================================
POLYGON_API_KEY=your-polygon-key
FMP_API_KEY=your-fmp-key
FRED_API_KEY=your-fred-key

# =============================================================================
# SEC EDGAR (required for regulatory filings)
# =============================================================================
SEC_USER_AGENT=YourName contact@email.com
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres123@postgres:5432/investment_agents` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `QDRANT_URL` | Qdrant vector DB URL | `http://qdrant:6333` |
| `DEFAULT_LLM_PROVIDER` | Default LLM provider | `openai` |
| `JWT_SECRET` | JWT signing secret | (generate a secure value) |
| `AGENT_TASK_TIMEOUT` | Agent task timeout in seconds | `300` |
| `MAX_CONCURRENT_RESEARCH` | Max concurrent research projects | `5` |

## Local Development

### Using the Setup Script

The easiest way to set up local development:

```bash
./scripts/setup-local.sh
```

This script will:
1. Check prerequisites (Docker, Docker Compose)
2. Create required directories
3. Build Docker images
4. Start infrastructure services (PostgreSQL, Redis, Qdrant, MinIO)
5. Initialize the database with schema and seed data
6. Start application services
7. Optionally start monitoring stack

### Manual Setup

```bash
# 1. Start infrastructure only
docker-compose up -d postgres redis qdrant minio

# 2. Wait for services to be ready
sleep 15

# 3. Initialize database
docker-compose exec postgres psql -U postgres -d investment_agents \
    -f /docker-entrypoint-initdb.d/001_create_schema.sql
docker-compose exec postgres psql -U postgres -d investment_agents \
    -f /docker-entrypoint-initdb.d/002_seed_prompts.sql

# 4. Start Prefect
docker-compose up -d prefect-server prefect-agent

# 5. Start application services
docker-compose up -d auth-service master-control-agent api-gateway

# 6. Start agents
docker-compose up -d idea-generation-agent due-diligence-agent workflow-engine

# 7. Start frontend
docker-compose up -d frontend

# 8. View logs
docker-compose logs -f
```

### Development Commands

```bash
# Rebuild a specific service
docker-compose build auth-service
docker-compose up -d auth-service

# View logs for a service
docker-compose logs -f master-control-agent

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d investment_agents

# Access Redis CLI
docker-compose exec redis redis-cli

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Running with Monitoring

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana at http://localhost:3001
# Default credentials: admin / admin123
```

## Production Deployment

### Prerequisites

- DigitalOcean account with API token
- `doctl` CLI installed and authenticated
- `terraform` installed
- `kubectl` installed

### Deploy to DigitalOcean

```bash
# 1. Configure production secrets
cp .env.example .env.production
nano .env.production

# 2. Run deployment script
./scripts/deploy-production.sh production
```

### Manual Deployment Steps

```bash
# 1. Authenticate with DigitalOcean
doctl auth init

# 2. Provision infrastructure with Terraform
cd infra
terraform init
terraform workspace new production
terraform plan -var-file="environments/prod/terraform.tfvars"
terraform apply -var-file="environments/prod/terraform.tfvars"

# 3. Configure kubectl
doctl kubernetes cluster kubeconfig save investment-agents-cluster

# 4. Create namespace and secrets
kubectl create namespace investment-agent-system
kubectl create secret generic investment-secrets \
    --from-env-file=.env.production \
    --namespace=investment-agent-system

# 5. Deploy applications
kubectl apply -k k8s/base/ --namespace=investment-agent-system

# 6. Verify deployment
kubectl get pods --namespace=investment-agent-system
kubectl get svc --namespace=investment-agent-system
```

### Scaling

```bash
# Scale agents horizontally
kubectl scale deployment idea-generation-agent --replicas=3 \
    --namespace=investment-agent-system

# Enable autoscaling
kubectl autoscale deployment idea-generation-agent \
    --min=2 --max=10 --cpu-percent=70 \
    --namespace=investment-agent-system
```

## API Reference

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "email": "user@example.com",
        "password": "password123",
        "full_name": "John Doe"
    }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "user@example.com",
        "password": "password123"
    }'
# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# Use token for authenticated requests
export TOKEN="eyJ..."
```

### Research Projects

```bash
# Create a new research project
curl -X POST http://localhost:8000/api/projects \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "ticker": "AAPL",
        "name": "Apple Deep Dive",
        "research_type": "deep"
    }'

# List all projects
curl http://localhost:8000/api/projects \
    -H "Authorization: Bearer $TOKEN"

# Start company analysis
curl -X POST http://localhost:8000/api/research/analyze \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "ticker": "AAPL",
        "research_type": "standard",
        "focus_areas": ["valuation", "competitive"]
    }'
```

### Investment Ideas

```bash
# Generate thematic ideas
curl -X POST http://localhost:8000/api/research/ideas \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "theme": "AI Infrastructure",
        "type": "thematic",
        "sector": "Technology"
    }'

# Screen stocks
curl -X POST http://localhost:8000/api/research/screen \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "criteria": {
            "market_cap_min": 1000000000,
            "pe_ratio_max": 30,
            "revenue_growth_min": 0.1
        }
    }'
```

### Workflows

```bash
# Create a workflow
curl -X POST http://localhost:8000/api/workflows \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Daily Market Scan",
        "workflow_type": "daily_scan",
        "schedule": "0 6 * * 1-5"
    }'

# Run a workflow
curl -X POST http://localhost:8000/api/workflows/{workflow_id}/run \
    -H "Authorization: Bearer $TOKEN"
```

## Agent Library

| Agent | Description | Prompts |
|-------|-------------|---------|
| **Idea Generation** | Scans sources for investment ideas | 20 |
| **Due Diligence** | Comprehensive company analysis | 36 |
| **Business Analysis** | Business model and competitive analysis | 19 |
| **Macro Analysis** | Macroeconomic environment analysis | 16 |
| **Risk Assessment** | Risk identification and assessment | 12 |
| **Portfolio Management** | Position sizing and portfolio optimization | 8 |
| **Industry Analysis** | Sector-specific analysis | 4 |
| **Reporting** | Report generation and formatting | 3 |

## Prompt Library

The system is powered by **118 specialized prompts** across 9 categories:

### Categories

1. **Investment Idea Generation** (20 prompts)
   - Thematic screening and order effects analysis
   - Newsletter and publication scanning
   - SEC 13F institutional clustering
   - Insider trading pattern analysis
   - Social sentiment scanning

2. **Due Diligence** (36 prompts)
   - Business overview and model analysis
   - Financial statement deep dive
   - Competitive landscape mapping
   - Management quality assessment
   - DCF and valuation analysis
   - Bear case development

3. **Portfolio Management** (19 prompts)
   - Position sizing optimization
   - Portfolio risk analysis
   - Rebalancing recommendations

4. **Macro Analysis** (16 prompts)
   - Economic environment assessment
   - Sector sensitivity analysis
   - Policy impact evaluation

### Using Prompts

```bash
# List available prompts
curl http://localhost:8000/api/prompts \
    -H "Authorization: Bearer $TOKEN"

# Get a specific prompt
curl http://localhost:8000/api/prompts/business_overview_report \
    -H "Authorization: Bearer $TOKEN"

# Execute a prompt
curl -X POST http://localhost:8000/api/prompts/business_overview_report/execute \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ticker": "AAPL"}'
```

## Troubleshooting

### Common Issues

**Docker containers not starting**
```bash
# Check container status
docker-compose ps

# View logs for errors
docker-compose logs

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

**Database connection errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres

# Check database exists
docker-compose exec postgres psql -U postgres -l
```

**API returning 401 Unauthorized**
```bash
# Verify JWT_SECRET is set consistently
grep JWT_SECRET .env

# Check token expiration (default: 60 minutes)
# Re-login to get a new token
```

**Agent tasks failing**
```bash
# Check agent logs
docker-compose logs -f idea-generation-agent

# Verify API keys are set
docker-compose exec master-control-agent env | grep API_KEY

# Check Redis connectivity
docker-compose exec redis redis-cli ping
```

**Prefect workflows not running**
```bash
# Check Prefect server
curl http://localhost:4200/api/health

# Check Prefect agent
docker-compose logs prefect-agent

# Restart Prefect services
docker-compose restart prefect-server prefect-agent
```

### Health Checks

```bash
# Check all service health endpoints
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # Master Control Agent
curl http://localhost:4200/api/health  # Prefect

# Check infrastructure
docker-compose exec postgres pg_isready
docker-compose exec redis redis-cli ping
curl http://localhost:6333/health  # Qdrant
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f master-control-agent

# Access container shell
docker-compose exec master-control-agent /bin/bash

# Check resource usage
docker stats
```

## Project Structure

```
investment-agent-system/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── pages/           # Page components
│   │   └── services/        # API services
│   ├── package.json
│   └── Dockerfile
├── services/
│   ├── shared/              # Shared libraries
│   │   ├── agents/          # Base agent framework
│   │   ├── clients/         # API clients (Polygon, FMP, SEC)
│   │   ├── config/          # Configuration management
│   │   ├── db/              # Database models & repositories
│   │   └── llm/             # LLM provider abstraction
│   ├── auth-service/        # Authentication service
│   ├── api-gateway/         # API Gateway
│   ├── master-control-agent/# Central orchestration
│   ├── workflow-engine/     # Prefect workflows
│   └── agents/
│       ├── idea-generation/ # Idea generation agent
│       └── due-diligence/   # Due diligence agent
├── infra/                   # Terraform infrastructure
│   ├── main.tf
│   ├── variables.tf
│   └── environments/
├── k8s/                     # Kubernetes manifests
│   └── base/
├── sql/                     # Database scripts
│   └── init/
├── monitoring/              # Prometheus & Grafana config
├── scripts/                 # Deployment scripts
│   ├── setup-local.sh
│   └── deploy-production.sh
├── docker-compose.yml
├── .env.example
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:
- Open an issue on GitHub
- Check the [API Docs](http://localhost:8000/docs) for endpoint details
- Review logs with `docker-compose logs -f`

---

Built with ❤️ for systematic investment research
