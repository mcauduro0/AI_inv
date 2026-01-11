# Investment Agent System - Deployment Status

## Overview

The Investment Agent System is now fully deployed and operational on DigitalOcean Kubernetes with 10 specialized AI agents.

## Access URLs

| Service | URL | Status |
|---------|-----|--------|
| **Frontend (Web App)** | http://24.144.65.175 | ✅ Running |
| **API Gateway** | http://129.212.197.52 | ✅ Running |
| **API Documentation** | http://129.212.197.52/docs | ✅ Available |

## Infrastructure

### Kubernetes Cluster
- **Name:** investment-agent-k8s-prod
- **Region:** NYC1
- **Node Pools:**
  - Core Pool: 3 nodes (s-2vcpu-4gb)
  - Agent Pool: 2 nodes (s-4vcpu-8gb)

### Services Running

| Service | Replicas | Status | Port |
|---------|----------|--------|------|
| API Gateway | 2 | Running | 8000 |
| Auth Service | 2 | Running | 8001 |
| Master Control Agent | 1 | Running | 8002 |
| Workflow Engine | 1 | Running | 8003 |
| Idea Generation Agent | 2 | Running | 8010 |
| Due Diligence Agent | 2 | Running | 8011 |
| Portfolio Management Agent | 1 | Running | 8012 |
| Macro Analysis Agent | 1 | Running | 8013 |
| Risk Analysis Agent | 1 | Running | 8014 |
| Sentiment Analysis Agent | 1 | Running | 8015 |
| Frontend | 2 | Running | 3000 |

### Database
- **Type:** PostgreSQL (DigitalOcean Managed)
- **Database:** investment_system
- **Tables:** 12 tables including users, prompts, workflows, research documents

### Cache
- **Type:** Redis (DigitalOcean Managed)
- **Purpose:** Session management, task queuing, caching

## Prompt Library

44 investment prompts have been seeded across 7 categories:

| Category | Count | Description |
|----------|-------|-------------|
| Idea Generation | 10 | Thematic screening, 13F analysis, insider signals, trend mapping |
| Due Diligence | 10 | Financial analysis, competitive moats, DCF modeling, risk assessment |
| Portfolio Management | 5 | Risk analysis, position sizing, rebalancing, factor exposure |
| Market Analysis | 5 | Regime classification, earnings analysis, Fed policy, sector momentum |
| Research Synthesis | 5 | Thesis building, bull/bear cases, research notes, earnings previews |
| Monitoring | 4 | Thesis tracking, news sentiment, price alerts, performance reporting |
| Special Situations | 5 | Merger arb, activist situations, distressed debt, IPOs, spinoffs |

## User Accounts

A test admin account has been created:
- **Email:** admin@investmentagent.com
- **Password:** InvestAgent2026!

## Next Steps

1. **Configure OAuth:** Set up Google/GitHub OAuth for social login
2. **Set Up Domain:** Configure DNS for custom domain with SSL
3. **Add More Prompts:** Use `scripts/seed_all_prompts.py` to add additional prompts
4. **Monitor Performance:** Set up Prometheus/Grafana for metrics

## Maintenance

### View Logs
```bash
kubectl logs -n investment-agent -l app=<service-name> --tail=100
```

### Restart Services
```bash
kubectl rollout restart deployment -n investment-agent
```

### Scale Services
```bash
kubectl scale deployment <service-name> --replicas=<count> -n investment-agent
```

### Seed Prompts
```bash
kubectl cp scripts/seed_all_prompts.py investment-agent/<auth-pod>:/tmp/
kubectl exec -n investment-agent <auth-pod> -- python3 /tmp/seed_all_prompts.py
```

## Repository

GitHub: https://github.com/mcauduro0/AI_inv

---
*Last Updated: January 11, 2026*
