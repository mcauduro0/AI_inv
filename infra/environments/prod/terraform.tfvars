# =============================================================================
# Production Environment Configuration
# =============================================================================
# NOTE: The do_token variable should be set via environment variable:
# export TF_VAR_do_token="your-digitalocean-token"
# Or passed via command line:
# terraform apply -var="do_token=your-token"
# =============================================================================

environment  = "prod"
project_name = "investment-agent"
region       = "nyc1"
spaces_region = "nyc3"

# VPC
vpc_ip_range = "10.20.0.0/16"

# Kubernetes - production-grade sizing
k8s_node_size   = "s-4vcpu-8gb"
k8s_node_count  = 3
k8s_min_nodes   = 3
k8s_max_nodes   = 10

agent_node_size   = "s-2vcpu-4gb"  # Reduced size to fit quota
agent_node_count  = 2
agent_min_nodes   = 1
agent_max_nodes   = 3  # Reduced to fit 15 droplet limit

# Database - production-grade with HA
db_size       = "db-s-2vcpu-4gb"
db_node_count = 2  # Primary + standby for HA

redis_size       = "db-s-2vcpu-4gb"
redis_node_count = 2  # Primary + replica for HA

# Storage
registry_tier = "professional"
cors_allowed_origins = ["https://app.yourdomain.com"]

# Monitoring
enable_monitoring = true
enable_logging    = true

# Domain (set your actual domain)
app_domain = "app.yourdomain.com"
