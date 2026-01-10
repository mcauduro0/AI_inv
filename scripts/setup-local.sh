#!/bin/bash
# =============================================================================
# Investment Agent System - Local Development Setup Script
# =============================================================================
# This script sets up the complete local development environment
# Usage: ./scripts/setup-local.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo ""
    echo "============================================================================="
    print_msg "$1" "$BLUE"
    echo "============================================================================="
}

print_success() {
    print_msg "✓ $1" "$GREEN"
}

print_warning() {
    print_msg "⚠ $1" "$YELLOW"
}

print_error() {
    print_msg "✗ $1" "$RED"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker installed: $DOCKER_VERSION"
    else
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | cut -d',' -f1)
        print_success "Docker Compose installed: $COMPOSE_VERSION"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# Setup environment file
setup_environment() {
    print_header "Setting Up Environment"
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please edit .env and add your API keys before continuing"
        else
            print_error ".env.example not found. Please create it first."
            exit 1
        fi
    else
        print_success ".env file already exists"
    fi
}

# Create required directories
create_directories() {
    print_header "Creating Required Directories"
    
    directories=(
        "data/postgres"
        "data/redis"
        "data/qdrant"
        "data/minio"
        "logs"
        "models"
        "reports"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_success "Created directory: $dir"
    done
}

# Build Docker images
build_images() {
    print_header "Building Docker Images"
    
    print_msg "This may take several minutes..." "$YELLOW"
    
    docker-compose build --parallel
    
    print_success "All Docker images built successfully"
}

# Start infrastructure services
start_infrastructure() {
    print_header "Starting Infrastructure Services"
    
    # Start core infrastructure first
    docker-compose up -d postgres redis qdrant minio
    
    print_msg "Waiting for services to be healthy..." "$YELLOW"
    
    # Wait for PostgreSQL
    echo -n "Waiting for PostgreSQL..."
    until docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    echo -n "Waiting for Redis..."
    until docker-compose exec -T redis redis-cli ping &> /dev/null; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Redis is ready"
    
    print_success "Infrastructure services are running"
}

# Initialize database
initialize_database() {
    print_header "Initializing Database"
    
    # Check if database is already initialized
    TABLES_EXIST=$(docker-compose exec -T postgres psql -U postgres -d investment_agents -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" -t 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$TABLES_EXIST" -gt "0" ]; then
        print_warning "Database already initialized ($TABLES_EXIST tables found)"
        read -p "Do you want to reinitialize? This will DROP all data! (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            print_msg "Skipping database initialization" "$YELLOW"
            return
        fi
    fi
    
    # Run initialization scripts
    for sql_file in sql/init/*.sql; do
        if [ -f "$sql_file" ]; then
            print_msg "Running $sql_file..." "$YELLOW"
            docker-compose exec -T postgres psql -U postgres -d investment_agents -f "/docker-entrypoint-initdb.d/$(basename $sql_file)"
            print_success "Executed $sql_file"
        fi
    done
    
    print_success "Database initialized successfully"
}

# Start application services
start_application() {
    print_header "Starting Application Services"
    
    docker-compose up -d prefect-server
    
    print_msg "Waiting for Prefect server..." "$YELLOW"
    sleep 10
    
    docker-compose up -d auth-service master-control-agent
    
    print_msg "Waiting for core services..." "$YELLOW"
    sleep 10
    
    docker-compose up -d api-gateway idea-generation-agent due-diligence-agent workflow-engine
    
    print_success "Application services started"
}

# Start frontend
start_frontend() {
    print_header "Starting Frontend"
    
    docker-compose up -d frontend
    
    print_success "Frontend started"
}

# Start monitoring (optional)
start_monitoring() {
    print_header "Starting Monitoring Stack"
    
    docker-compose --profile monitoring up -d
    
    print_success "Monitoring stack started"
}

# Display status
display_status() {
    print_header "System Status"
    
    docker-compose ps
    
    echo ""
    print_header "Access URLs"
    echo ""
    print_msg "Frontend:        http://localhost:3000" "$GREEN"
    print_msg "API Gateway:     http://localhost:8000" "$GREEN"
    print_msg "API Docs:        http://localhost:8000/docs" "$GREEN"
    print_msg "Auth Service:    http://localhost:8001" "$GREEN"
    print_msg "MCA Service:     http://localhost:8002" "$GREEN"
    print_msg "Prefect UI:      http://localhost:4200" "$GREEN"
    print_msg "MinIO Console:   http://localhost:9001" "$GREEN"
    print_msg "Qdrant Dashboard: http://localhost:6333/dashboard" "$GREEN"
    echo ""
    print_msg "Monitoring (if enabled):" "$YELLOW"
    print_msg "Prometheus:      http://localhost:9090" "$GREEN"
    print_msg "Grafana:         http://localhost:3001 (admin/admin123)" "$GREEN"
    echo ""
}

# Main execution
main() {
    print_header "Investment Agent System - Local Setup"
    
    # Change to project root directory
    cd "$(dirname "$0")/.."
    
    check_prerequisites
    setup_environment
    create_directories
    
    # Ask user what to do
    echo ""
    print_msg "Select setup option:" "$YELLOW"
    echo "1) Full setup (build + start all services)"
    echo "2) Quick start (use existing images)"
    echo "3) Infrastructure only (databases + queues)"
    echo "4) Rebuild and restart"
    echo "5) Stop all services"
    echo ""
    read -p "Enter option (1-5): " option
    
    case $option in
        1)
            build_images
            start_infrastructure
            initialize_database
            start_application
            start_frontend
            read -p "Start monitoring stack? (y/N): " monitor
            if [ "$monitor" = "y" ] || [ "$monitor" = "Y" ]; then
                start_monitoring
            fi
            display_status
            ;;
        2)
            start_infrastructure
            start_application
            start_frontend
            display_status
            ;;
        3)
            start_infrastructure
            initialize_database
            display_status
            ;;
        4)
            docker-compose down
            build_images
            start_infrastructure
            start_application
            start_frontend
            display_status
            ;;
        5)
            docker-compose down
            print_success "All services stopped"
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "Setup complete!"
}

# Run main function
main "$@"
