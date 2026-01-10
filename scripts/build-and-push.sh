#!/bin/bash
#
# Investment Agent System - Docker Build and Push Script
# This script builds all Docker images and pushes them to DigitalOcean Container Registry
#

set -e

# =============================================================================
# Configuration
# =============================================================================

REGISTRY="registry.digitalocean.com/investment-agentregistry"
VERSION="${VERSION:-latest}"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check doctl
    if ! command -v doctl &> /dev/null; then
        log_warning "doctl is not installed. Installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install doctl
        else
            sudo snap install doctl
        fi
    fi
    
    log_success "Pre-flight checks passed"
}

# =============================================================================
# Authentication
# =============================================================================

authenticate() {
    log_info "Authenticating with DigitalOcean..."
    
    # Check if already authenticated
    if doctl account get &> /dev/null; then
        log_success "Already authenticated with DigitalOcean"
    else
        log_info "Please authenticate with DigitalOcean..."
        doctl auth init
    fi
    
    # Login to container registry
    log_info "Logging into container registry..."
    doctl registry login
    
    log_success "Authentication complete"
}

# =============================================================================
# Build Images
# =============================================================================

build_image() {
    local service_name=$1
    local dockerfile_path=$2
    local context_path=$3
    local image_tag="${REGISTRY}/${service_name}:${VERSION}"
    
    log_info "Building ${service_name}..."
    
    docker build \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VERSION="${VERSION}" \
        -t "${image_tag}" \
        -f "${dockerfile_path}" \
        "${context_path}"
    
    log_success "Built ${image_tag}"
}

build_all_images() {
    log_info "Building all Docker images..."
    
    cd "$(dirname "$0")/.."
    
    # Build shared base image first
    log_info "Building shared base image..."
    docker build \
        -t "${REGISTRY}/shared-base:${VERSION}" \
        -f services/shared/Dockerfile.base \
        services/shared/
    
    # Build API Gateway
    build_image "api-gateway" \
        "services/api-gateway/Dockerfile" \
        "services/"
    
    # Build Auth Service
    build_image "auth-service" \
        "services/auth-service/Dockerfile" \
        "services/"
    
    # Build Master Control Agent
    build_image "master-control-agent" \
        "services/master-control-agent/Dockerfile" \
        "services/"
    
    # Build Workflow Engine
    build_image "workflow-engine" \
        "services/workflow-engine/Dockerfile" \
        "services/"
    
    # Build Idea Generation Agent
    build_image "idea-generation-agent" \
        "services/agents/idea-generation/Dockerfile" \
        "services/"
    
    # Build Due Diligence Agent
    build_image "due-diligence-agent" \
        "services/agents/due-diligence/Dockerfile" \
        "services/"
    
    # Build Frontend
    build_image "frontend" \
        "frontend/Dockerfile" \
        "frontend/"
    
    log_success "All images built successfully"
}

# =============================================================================
# Push Images
# =============================================================================

push_image() {
    local service_name=$1
    local image_tag="${REGISTRY}/${service_name}:${VERSION}"
    
    log_info "Pushing ${service_name}..."
    docker push "${image_tag}"
    log_success "Pushed ${image_tag}"
}

push_all_images() {
    log_info "Pushing all Docker images to registry..."
    
    push_image "shared-base"
    push_image "api-gateway"
    push_image "auth-service"
    push_image "master-control-agent"
    push_image "workflow-engine"
    push_image "idea-generation-agent"
    push_image "due-diligence-agent"
    push_image "frontend"
    
    log_success "All images pushed successfully"
}

# =============================================================================
# Update Kubernetes Deployments
# =============================================================================

update_k8s_deployments() {
    log_info "Updating Kubernetes deployments with new images..."
    
    # Check if kubectl is configured
    if ! kubectl cluster-info &> /dev/null; then
        log_warning "kubectl not configured. Skipping deployment update."
        return
    fi
    
    # Update deployments
    kubectl set image deployment/api-gateway \
        api-gateway="${REGISTRY}/api-gateway:${VERSION}" \
        -n investment-agent || true
    
    kubectl set image deployment/auth-service \
        auth-service="${REGISTRY}/auth-service:${VERSION}" \
        -n investment-agent || true
    
    kubectl set image deployment/master-control-agent \
        master-control-agent="${REGISTRY}/master-control-agent:${VERSION}" \
        -n investment-agent || true
    
    kubectl set image deployment/workflow-engine \
        workflow-engine="${REGISTRY}/workflow-engine:${VERSION}" \
        -n investment-agent || true
    
    kubectl set image deployment/idea-generation-agent \
        idea-generation-agent="${REGISTRY}/idea-generation-agent:${VERSION}" \
        -n investment-agent || true
    
    kubectl set image deployment/due-diligence-agent \
        due-diligence-agent="${REGISTRY}/due-diligence-agent:${VERSION}" \
        -n investment-agent || true
    
    kubectl set image deployment/frontend \
        frontend="${REGISTRY}/frontend:${VERSION}" \
        -n investment-agent || true
    
    log_success "Kubernetes deployments updated"
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    echo "=============================================="
    echo "  Investment Agent System - Build & Deploy"
    echo "=============================================="
    echo ""
    
    preflight_checks
    authenticate
    build_all_images
    push_all_images
    update_k8s_deployments
    
    echo ""
    log_success "Build and push complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify images in registry: doctl registry repository list-v2"
    echo "  2. Check deployment status: kubectl get pods -n investment-agent"
    echo "  3. View logs: kubectl logs -f deployment/api-gateway -n investment-agent"
    echo ""
}

# Parse arguments
case "${1:-}" in
    build)
        preflight_checks
        build_all_images
        ;;
    push)
        authenticate
        push_all_images
        ;;
    deploy)
        update_k8s_deployments
        ;;
    *)
        main
        ;;
esac
