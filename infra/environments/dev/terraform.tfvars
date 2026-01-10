# =============================================================================
# Development Environment Configuration
# =============================================================================

environment  = "dev"
project_name = "investment-agent"
region       = "nyc3"
spaces_region = "nyc3"

# VPC
vpc_ip_range = "10.10.0.0/16"

# Kubernetes - smaller for dev
k8s_node_size   = "s-2vcpu-4gb"
k8s_node_count  = 2
k8s_min_nodes   = 1
k8s_max_nodes   = 3

agent_node_size   = "s-2vcpu-4gb"
agent_node_count  = 1
agent_min_nodes   = 1
agent_max_nodes   = 3

# Database - smaller for dev
db_size       = "db-s-1vcpu-1gb"
db_node_count = 1

redis_size       = "db-s-1vcpu-1gb"
redis_node_count = 1

# Storage
registry_tier = "starter"
cors_allowed_origins = ["http://localhost:3000", "http://localhost:8000"]

# Monitoring
enable_monitoring = true
enable_logging    = true
