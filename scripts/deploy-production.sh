#!/bin/bash
# =============================================================================
# Investment Agent System - Production Deployment Script
# =============================================================================
# This script deploys the system to DigitalOcean Kubernetes
# Usage: ./scripts/deploy-production.sh [environment]
# =============================================================================

set -e

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_NAME="investment-agent-system"
REGISTRY="registry.digitalocean.com"
CLUSTER_NAME="investment-agents-cluster"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_msg() { echo -e "${2}${1}${NC}"; }
print_header() { echo ""; echo "============================================================================="; print_msg "$1" "$BLUE"; echo "============================================================================="; }
print_success() { print_msg "✓ $1" "$GREEN"; }
print_warning() { print_msg "⚠ $1" "$YELLOW"; }
print_error() { print_msg "✗ $1" "$RED"; }

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check doctl
    if command -v doctl &> /dev/null; then
        print_success "doctl CLI installed"
    else
        print_error "doctl CLI not installed. Install with: brew install doctl"
        exit 1
    fi
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        print_success "kubectl installed"
    else
        print_error "kubectl not installed"
        exit 1
    fi
    
    # Check Terraform
    if command -v terraform &> /dev/null; then
        TERRAFORM_VERSION=$(terraform version | head -n1)
        print_success "Terraform installed: $TERRAFORM_VERSION"
    else
        print_error "Terraform not installed"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker installed"
    else
        print_error "Docker not installed"
        exit 1
    fi
    
    # Check DigitalOcean authentication
    if doctl account get &> /dev/null; then
        print_success "DigitalOcean authenticated"
    else
        print_error "Not authenticated with DigitalOcean. Run: doctl auth init"
        exit 1
    fi
}

# Provision infrastructure with Terraform
provision_infrastructure() {
    print_header "Provisioning Infrastructure with Terraform"
    
    cd infra
    
    # Initialize Terraform
    print_msg "Initializing Terraform..." "$YELLOW"
    terraform init
    
    # Select workspace
    terraform workspace select $ENVIRONMENT 2>/dev/null || terraform workspace new $ENVIRONMENT
    
    # Plan
    print_msg "Planning infrastructure changes..." "$YELLOW"
    terraform plan -var-file="environments/${ENVIRONMENT}/terraform.tfvars" -out=tfplan
    
    # Ask for confirmation
    echo ""
    read -p "Apply these changes? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    # Apply
    print_msg "Applying infrastructure changes..." "$YELLOW"
    terraform apply tfplan
    
    # Get outputs
    CLUSTER_ID=$(terraform output -raw kubernetes_cluster_id)
    REGISTRY_NAME=$(terraform output -raw container_registry_name)
    DATABASE_URL=$(terraform output -raw database_url)
    REDIS_URL=$(terraform output -raw redis_url)
    
    print_success "Infrastructure provisioned"
    
    cd ..
}

# Configure kubectl
configure_kubectl() {
    print_header "Configuring kubectl"
    
    doctl kubernetes cluster kubeconfig save $CLUSTER_NAME
    
    # Verify connection
    if kubectl cluster-info &> /dev/null; then
        print_success "kubectl configured and connected to cluster"
    else
        print_error "Failed to connect to cluster"
        exit 1
    fi
}

# Build and push Docker images
build_and_push_images() {
    print_header "Building and Pushing Docker Images"
    
    # Login to DigitalOcean Container Registry
    doctl registry login
    
    SERVICES=(
        "auth-service"
        "api-gateway"
        "master-control-agent"
        "idea-generation-agent:services/agents/idea-generation"
        "due-diligence-agent:services/agents/due-diligence"
        "workflow-engine"
        "frontend"
    )
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name path <<< "$service"
        path=${path:-"services/$name"}
        
        print_msg "Building $name..." "$YELLOW"
        
        docker build -t $REGISTRY/$PROJECT_NAME/$name:latest -f $path/Dockerfile .
        docker push $REGISTRY/$PROJECT_NAME/$name:latest
        
        print_success "Pushed $name"
    done
}

# Create Kubernetes secrets
create_secrets() {
    print_header "Creating Kubernetes Secrets"
    
    # Check if secrets file exists
    if [ ! -f ".env.production" ]; then
        print_error ".env.production file not found"
        print_msg "Create .env.production with your production secrets" "$YELLOW"
        exit 1
    fi
    
    # Create namespace if not exists
    kubectl create namespace $PROJECT_NAME --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets from env file
    kubectl create secret generic investment-secrets \
        --from-env-file=.env.production \
        --namespace=$PROJECT_NAME \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Secrets created"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    print_header "Deploying to Kubernetes"
    
    # Apply base configurations
    kubectl apply -k k8s/base/ --namespace=$PROJECT_NAME
    
    # Wait for deployments
    print_msg "Waiting for deployments to be ready..." "$YELLOW"
    
    kubectl rollout status deployment/auth-service --namespace=$PROJECT_NAME --timeout=300s
    kubectl rollout status deployment/api-gateway --namespace=$PROJECT_NAME --timeout=300s
    kubectl rollout status deployment/master-control-agent --namespace=$PROJECT_NAME --timeout=300s
    
    print_success "All deployments ready"
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    # Get a pod to run migrations
    POD=$(kubectl get pods --namespace=$PROJECT_NAME -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
    
    # Run migrations
    kubectl exec -it $POD --namespace=$PROJECT_NAME -- python -c "from app.db import init_db; init_db()"
    
    print_success "Migrations completed"
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    # Get service URLs
    API_URL=$(kubectl get svc api-gateway --namespace=$PROJECT_NAME -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$API_URL" ]; then
        API_URL=$(kubectl get svc api-gateway --namespace=$PROJECT_NAME -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    # Health check
    print_msg "Checking API health..." "$YELLOW"
    
    for i in {1..30}; do
        if curl -s "http://$API_URL/health" | grep -q "healthy"; then
            print_success "API is healthy"
            break
        fi
        echo -n "."
        sleep 5
    done
    
    echo ""
    print_header "Deployment Complete"
    echo ""
    print_msg "API URL: http://$API_URL" "$GREEN"
    print_msg "API Docs: http://$API_URL/docs" "$GREEN"
    echo ""
}

# Rollback deployment
rollback() {
    print_header "Rolling Back Deployment"
    
    kubectl rollout undo deployment/auth-service --namespace=$PROJECT_NAME
    kubectl rollout undo deployment/api-gateway --namespace=$PROJECT_NAME
    kubectl rollout undo deployment/master-control-agent --namespace=$PROJECT_NAME
    
    print_success "Rollback completed"
}

# Main execution
main() {
    print_header "Investment Agent System - Production Deployment"
    print_msg "Environment: $ENVIRONMENT" "$YELLOW"
    
    cd "$(dirname "$0")/.."
    
    echo ""
    print_msg "Select deployment option:" "$YELLOW"
    echo "1) Full deployment (infrastructure + application)"
    echo "2) Application only (skip infrastructure)"
    echo "3) Infrastructure only"
    echo "4) Build and push images only"
    echo "5) Rollback last deployment"
    echo ""
    read -p "Enter option (1-5): " option
    
    check_prerequisites
    
    case $option in
        1)
            provision_infrastructure
            configure_kubectl
            build_and_push_images
            create_secrets
            deploy_kubernetes
            run_migrations
            verify_deployment
            ;;
        2)
            configure_kubectl
            build_and_push_images
            create_secrets
            deploy_kubernetes
            run_migrations
            verify_deployment
            ;;
        3)
            provision_infrastructure
            ;;
        4)
            build_and_push_images
            ;;
        5)
            configure_kubectl
            rollback
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
    
    print_success "Deployment process complete!"
}

main "$@"
