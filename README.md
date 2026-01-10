# Investment Agent System

A state-of-the-art agentic AI system for systematic investment research and idea generation. This platform acts as a team of top-tier investment analysts, automating the entire investment research process from idea generation to thesis development.

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

## Features

### Specialized Agents

| Agent | Capabilities |
|-------|-------------|
| **Idea Generation Agent** | Thematic screening, newsletter scanning, 13F clustering, insider trading analysis, social sentiment |
| **Due Diligence Agent** | Business overview, financial analysis, competitive landscape, management assessment |
| **Risk Agent** | Risk identification, bear case development, regulatory analysis, stress testing |
| **Valuation Agent** | DCF modeling, comparable analysis, sum-of-parts, scenario analysis |
| **Macro Agent** | Economic analysis, sector sensitivity, interest rate impact |
| **Thesis Agent** | Investment thesis synthesis, catalyst identification, position sizing |

### Research Workflows

- **Quick Research**: 15-minute overview for initial screening
- **Standard Research**: 2-hour comprehensive analysis
- **Deep Research**: Full institutional-quality deep dive
- **Thematic Idea Generation**: Theme-based opportunity identification
- **Institutional Clustering**: Smart money following via 13F analysis

### Prompt Library

The system is powered by 118 specialized prompts across 9 categories:
- Investment Idea Generation (20 prompts)
- Due Diligence (36 prompts)
- Portfolio Management (19 prompts)
- Macro Analysis (16 prompts)
- Business Model Understanding (5 prompts)
- Industry Analysis (4 prompts)
- Management Evaluation (3 prompts)
- Risk Identification (3 prompts)
- Other (12 prompts)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/investment-agent-system.git
cd investment-agent-system
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

4. **Initialize the database**
```bash
docker-compose exec auth-service python -c "from shared.db.repository import init_db; import asyncio; asyncio.run(init_db())"
```

5. **Access the application**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Prefect UI: http://localhost:4200

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/investment_agents

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Data Providers
POLYGON_API_KEY=your_polygon_key
FMP_API_KEY=your_fmp_key

# Auth
JWT_SECRET=your_jwt_secret
```

## Project Structure

```
investment-agent-system/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── contexts/        # React contexts
│   └── package.json
├── services/
│   ├── shared/              # Shared libraries
│   │   ├── agents/          # Base agent framework
│   │   ├── clients/         # API clients (Polygon, FMP, SEC)
│   │   ├── config/          # Configuration management
│   │   ├── db/              # Database models & repositories
│   │   └── llm/             # LLM provider abstraction
│   ├── auth-service/        # Authentication service
│   ├── master-control-agent/# Central orchestration
│   ├── workflow-engine/     # Prefect workflows
│   └── agents/
│       ├── idea-generation/ # Idea generation agent
│       └── due-diligence/   # Due diligence agent
├── infra/                   # Infrastructure as Code
│   ├── main.tf              # Terraform configuration
│   ├── variables.tf
│   └── environments/
├── k8s/                     # Kubernetes manifests
│   └── base/
├── docker-compose.yml       # Local development
└── README.md
```

## API Reference

### Research Endpoints

```http
POST /research/start
{
  "ticker": "AAPL",
  "research_type": "standard",  // quick, standard, full, deep
  "focus_areas": ["valuation", "competitive"],
  "custom_questions": []
}

GET /research/{project_id}
```

### Idea Generation Endpoints

```http
POST /ideas/generate
{
  "theme": "AI Infrastructure",
  "sector": "Technology",
  "strategy": "thematic",  // thematic, value, growth, contrarian
  "sources": ["newsletters", "sec_filings"]
}
```

### Workflow Endpoints

```http
POST /workflows
{
  "name": "Daily Market Scan",
  "workflow_type": "daily_scan",
  "schedule": "0 6 * * 1-5"  // Cron expression
}

POST /workflows/{id}/run
```

## Deployment

### DigitalOcean Kubernetes

1. **Provision infrastructure**
```bash
cd infra
terraform init
terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

2. **Deploy to Kubernetes**
```bash
kubectl apply -k k8s/overlays/production
```

3. **Configure secrets**
```bash
kubectl create secret generic api-keys \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=polygon-api-key=$POLYGON_API_KEY
```

### Monitoring

- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and alerting
- **Prefect**: Workflow monitoring

## Development

### Adding a New Agent

1. Create agent directory under `services/agents/`
2. Implement the agent class extending `BaseAgent`
3. Define supported prompts
4. Add Dockerfile and Kubernetes manifests
5. Register with Master Control Agent

### Adding a New Workflow

1. Define workflow in `services/workflow-engine/app/workflows.py`
2. Use `@flow` decorator for main workflow
3. Use `@task` decorator for individual steps
4. Register workflow in the API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions and support, please open an issue on GitHub.
