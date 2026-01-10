#!/bin/bash
# =============================================================================
# Investment Agent System - Complete Deployment Script
# Run this script from a machine with Docker installed to build and push images
# =============================================================================

set -e

# Configuration
REGISTRY="registry.digitalocean.com/investment-agentregistry"
SERVICES=("api-gateway" "auth-service" "master-control-agent" "workflow-engine" "idea-generation-agent" "due-diligence-agent" "frontend")

echo "=============================================="
echo "Investment Agent System - Complete Deployment"
echo "=============================================="

# Step 1: Authenticate with DigitalOcean Container Registry
echo ""
echo "[1/4] Authenticating with DigitalOcean Container Registry..."
doctl registry login

# Step 2: Build Docker images
echo ""
echo "[2/4] Building Docker images..."

cd "$(dirname "$0")/.."

# Build API Gateway
echo "Building api-gateway..."
docker build -t ${REGISTRY}/api-gateway:latest -f services/api-gateway/Dockerfile .

# Build Auth Service
echo "Building auth-service..."
docker build -t ${REGISTRY}/auth-service:latest -f services/auth-service/Dockerfile .

# Build Master Control Agent
echo "Building master-control-agent..."
docker build -t ${REGISTRY}/master-control-agent:latest -f services/master-control-agent/Dockerfile .

# Build Workflow Engine
echo "Building workflow-engine..."
docker build -t ${REGISTRY}/workflow-engine:latest -f services/workflow-engine/Dockerfile .

# Build Idea Generation Agent
echo "Building idea-generation-agent..."
docker build -t ${REGISTRY}/idea-generation-agent:latest -f services/agents/idea-generation/Dockerfile .

# Build Due Diligence Agent
echo "Building due-diligence-agent..."
docker build -t ${REGISTRY}/due-diligence-agent:latest -f services/agents/due-diligence/Dockerfile .

# Build Frontend
echo "Building frontend..."
docker build -t ${REGISTRY}/frontend:latest -f frontend/Dockerfile ./frontend

# Step 3: Push images to registry
echo ""
echo "[3/4] Pushing images to DigitalOcean Container Registry..."

for service in "${SERVICES[@]}"; do
    echo "Pushing ${service}..."
    docker push ${REGISTRY}/${service}:latest
done

# Step 4: Deploy to Kubernetes
echo ""
echo "[4/4] Deploying to Kubernetes..."

kubectl apply -f k8s/production/namespace-and-secrets.yaml
kubectl apply -f k8s/production/deployments.yaml
kubectl apply -f k8s/production/ingress.yaml

# Wait for deployments
echo ""
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/api-gateway -n investment-agent --timeout=300s
kubectl rollout status deployment/auth-service -n investment-agent --timeout=300s
kubectl rollout status deployment/master-control-agent -n investment-agent --timeout=300s

echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo ""
echo "Load Balancer IP:"
kubectl get svc investment-agent-lb -n investment-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
echo ""
echo "Access the API at: http://$(kubectl get svc investment-agent-lb -n investment-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
echo ""
