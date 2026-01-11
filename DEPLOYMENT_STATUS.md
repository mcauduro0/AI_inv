# Investment Agent System - Deployment Status

## Overview

The Investment Agent System is now fully deployed and operational on DigitalOcean Kubernetes.

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
| Frontend | 2 | Running | 3000 |

### Database
- **Type:** PostgreSQL (DigitalOcean Managed)
- **Database:** investment_system
- **Tables:** 12 tables including users, prompts, workflows, research documents

### Cache
- **Type:** Redis (DigitalOcean Managed)
- **Purpose:** Session management, task queuing, caching

## Prompt Library

10 investment prompts have been seeded across categories:
- Idea Generation (3 prompts)
- Due Diligence (3 prompts)
- Portfolio Management (1 prompt)
- Market Analysis (1 prompt)
- Research Synthesis (1 prompt)
- Monitoring (1 prompt)

## Next Steps

1. **Create User Accounts:** Use the "Create one" link on the login page
2. **Configure OAuth:** Set up Google/GitHub OAuth for social login
3. **Add More Prompts:** Run the seed script with DATABASE_URL environment variable
4. **Set Up Domain:** Configure DNS for custom domain with SSL

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

## Repository

GitHub: https://github.com/mcauduro0/AI_inv

---
*Last Updated: January 10, 2026*
