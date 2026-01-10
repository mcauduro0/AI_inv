# Investment Agent System - Deployment Guide

This guide provides step-by-step instructions for deploying the Investment Agent System to DigitalOcean.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deploy (Automated)](#quick-deploy-automated)
3. [Manual Deployment](#manual-deployment)
4. [CI/CD Setup](#cicd-setup)
5. [Post-Deployment Configuration](#post-deployment-configuration)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install doctl (DigitalOcean CLI)
# macOS
brew install doctl

# Linux
sudo snap install doctl

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### Required Credentials

- DigitalOcean Personal Access Token
- All API keys configured in `.env.local`

---

## Quick Deploy (Automated)

The fastest way to deploy is using the automated script:

```bash
# 1. Clone the repository
git clone https://github.com/mcauduro0/AI_inv.git
cd AI_inv

# 2. Authenticate with DigitalOcean
doctl auth init
# Enter your DigitalOcean Personal Access Token

# 3. Get Kubernetes credentials
doctl kubernetes cluster kubeconfig save investment-agent-cluster

# 4. Run the build and deploy script
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh
```

---

## Manual Deployment

### Step 1: Authenticate with DigitalOcean

```bash
# Initialize doctl
doctl auth init

# Login to container registry
doctl registry login
```

### Step 2: Build Docker Images

```bash
cd AI_inv

# Build shared base image
docker build -t registry.digitalocean.com/investment-agentregistry/shared-base:latest \
  -f services/shared/Dockerfile.base services/shared/

# Build API Gateway
docker build -t registry.digitalocean.com/investment-agentregistry/api-gateway:latest \
  -f services/api-gateway/Dockerfile services/

# Build Auth Service
docker build -t registry.digitalocean.com/investment-agentregistry/auth-service:latest \
  -f services/auth-service/Dockerfile services/

# Build Master Control Agent
docker build -t registry.digitalocean.com/investment-agentregistry/master-control-agent:latest \
  -f services/master-control-agent/Dockerfile services/

# Build Workflow Engine
docker build -t registry.digitalocean.com/investment-agentregistry/workflow-engine:latest \
  -f services/workflow-engine/Dockerfile services/

# Build Idea Generation Agent
docker build -t registry.digitalocean.com/investment-agentregistry/idea-generation-agent:latest \
  -f services/agents/idea-generation/Dockerfile services/

# Build Due Diligence Agent
docker build -t registry.digitalocean.com/investment-agentregistry/due-diligence-agent:latest \
  -f services/agents/due-diligence/Dockerfile services/

# Build Frontend
docker build -t registry.digitalocean.com/investment-agentregistry/frontend:latest \
  -f frontend/Dockerfile frontend/
```

### Step 3: Push Images to Registry

```bash
docker push registry.digitalocean.com/investment-agentregistry/shared-base:latest
docker push registry.digitalocean.com/investment-agentregistry/api-gateway:latest
docker push registry.digitalocean.com/investment-agentregistry/auth-service:latest
docker push registry.digitalocean.com/investment-agentregistry/master-control-agent:latest
docker push registry.digitalocean.com/investment-agentregistry/workflow-engine:latest
docker push registry.digitalocean.com/investment-agentregistry/idea-generation-agent:latest
docker push registry.digitalocean.com/investment-agentregistry/due-diligence-agent:latest
docker push registry.digitalocean.com/investment-agentregistry/frontend:latest
```

### Step 4: Configure Kubernetes

```bash
# Get kubeconfig
doctl kubernetes cluster kubeconfig save investment-agent-cluster

# Verify connection
kubectl cluster-info

# Apply deployments
kubectl apply -f k8s/production/namespace-and-secrets.yaml
kubectl apply -f k8s/production/deployments.yaml
kubectl apply -f k8s/production/ingress.yaml
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n investment-agent

# Check services
kubectl get svc -n investment-agent

# Check logs
kubectl logs -f deployment/api-gateway -n investment-agent
```

---

## CI/CD Setup

### GitHub Actions (Recommended)

1. **Add Repository Secrets** in GitHub:
   - Go to Settings → Secrets and variables → Actions
   - Add `DIGITALOCEAN_ACCESS_TOKEN`: Your DO token

2. **Push to main branch** to trigger deployment:
   ```bash
   git add -A
   git commit -m "Deploy to production"
   git push origin main
   ```

3. **Monitor deployment** in GitHub Actions tab

### Manual Trigger

You can also trigger the workflow manually:
1. Go to Actions tab in GitHub
2. Select "Build and Deploy to DigitalOcean"
3. Click "Run workflow"

---

## Post-Deployment Configuration

### Initialize Database

The database schema is automatically applied when the PostgreSQL container starts. To manually run migrations:

```bash
# Connect to database pod
kubectl exec -it deployment/postgres -n investment-agent -- psql -U postgres -d investment_agent

# Or run SQL files directly
kubectl exec -i deployment/postgres -n investment-agent -- psql -U postgres -d investment_agent < sql/init/001_create_schema.sql
kubectl exec -i deployment/postgres -n investment-agent -- psql -U postgres -d investment_agent < sql/init/003_seed_complete_prompts.sql
```

### Configure DNS (Optional)

To use a custom domain:

1. Get the Load Balancer IP:
   ```bash
   kubectl get svc investment-agent-lb -n investment-agent
   ```

2. Add DNS A record pointing to the Load Balancer IP

3. Update the Ingress with your domain:
   ```yaml
   spec:
     rules:
     - host: your-domain.com
   ```

### Enable SSL (Optional)

Install cert-manager for automatic SSL:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

---

## Troubleshooting

### Pods in ImagePullBackOff

```bash
# Check if registry credentials are correct
kubectl get secret registry-credentials -n investment-agent -o yaml

# Recreate registry credentials
kubectl delete secret registry-credentials -n investment-agent
kubectl create secret docker-registry registry-credentials \
  --docker-server=registry.digitalocean.com \
  --docker-username=YOUR_DO_TOKEN \
  --docker-password=YOUR_DO_TOKEN \
  -n investment-agent
```

### Pods in CrashLoopBackOff

```bash
# Check logs
kubectl logs deployment/api-gateway -n investment-agent --previous

# Check events
kubectl describe pod <pod-name> -n investment-agent
```

### Database Connection Issues

```bash
# Verify database is running
kubectl get pods -n investment-agent | grep postgres

# Check database logs
kubectl logs deployment/postgres -n investment-agent

# Test connection from another pod
kubectl exec -it deployment/api-gateway -n investment-agent -- nc -zv postgres 5432
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n investment-agent

# Check ingress
kubectl describe ingress -n investment-agent

# Port forward for local testing
kubectl port-forward svc/api-gateway 8000:80 -n investment-agent
```

---

## Access Points

After successful deployment:

| Service | URL |
|---------|-----|
| Frontend | http://129.212.197.52 |
| API Gateway | http://129.212.197.52/api |
| API Docs | http://129.212.197.52/api/docs |

---

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/mcauduro0/AI_inv/issues)
- Review logs with `kubectl logs`
- Contact support
