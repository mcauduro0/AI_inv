# =============================================================================
# Investment Agent System - Terraform Outputs
# =============================================================================

# =============================================================================
# Kubernetes Outputs
# =============================================================================

output "kubernetes_cluster_id" {
  description = "ID of the Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.main.id
}

output "kubernetes_cluster_name" {
  description = "Name of the Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.main.name
}

output "kubernetes_endpoint" {
  description = "Endpoint for the Kubernetes API server"
  value       = digitalocean_kubernetes_cluster.main.endpoint
  sensitive   = true
}

output "kubernetes_kubeconfig" {
  description = "Kubeconfig for the Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.main.kube_config[0].raw_config
  sensitive   = true
}

# =============================================================================
# Database Outputs
# =============================================================================

output "postgres_host" {
  description = "PostgreSQL database host"
  value       = digitalocean_database_cluster.postgres.private_host
  sensitive   = true
}

output "postgres_port" {
  description = "PostgreSQL database port"
  value       = digitalocean_database_cluster.postgres.port
}

output "postgres_database" {
  description = "PostgreSQL database name"
  value       = digitalocean_database_db.investment_db.name
}

output "postgres_user" {
  description = "PostgreSQL application user"
  value       = digitalocean_database_user.app_user.name
}

output "postgres_password" {
  description = "PostgreSQL application user password"
  value       = digitalocean_database_user.app_user.password
  sensitive   = true
}

output "postgres_connection_string" {
  description = "PostgreSQL connection string for the application"
  value       = "postgresql://${digitalocean_database_user.app_user.name}:${digitalocean_database_user.app_user.password}@${digitalocean_database_cluster.postgres.private_host}:${digitalocean_database_cluster.postgres.port}/${digitalocean_database_db.investment_db.name}?sslmode=require"
  sensitive   = true
}

# =============================================================================
# Redis Outputs
# =============================================================================

output "redis_host" {
  description = "Redis cache host"
  value       = digitalocean_database_cluster.redis.private_host
  sensitive   = true
}

output "redis_port" {
  description = "Redis cache port"
  value       = digitalocean_database_cluster.redis.port
}

output "redis_password" {
  description = "Redis password"
  value       = digitalocean_database_cluster.redis.password
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "rediss://:${digitalocean_database_cluster.redis.password}@${digitalocean_database_cluster.redis.private_host}:${digitalocean_database_cluster.redis.port}"
  sensitive   = true
}

# =============================================================================
# Storage Outputs (Spaces - requires separate credentials)
# =============================================================================

# Commented out - Spaces bucket not created without credentials
# output "spaces_bucket_name" {
#   description = "Name of the Spaces bucket"
#   value       = digitalocean_spaces_bucket.main.name
# }

output "spaces_bucket_endpoint" {
  description = "Endpoint for the Spaces bucket (when created)"
  value       = "https://${var.spaces_region}.digitaloceanspaces.com"
}

# =============================================================================
# Container Registry Outputs
# =============================================================================

output "registry_endpoint" {
  description = "Container registry endpoint"
  value       = digitalocean_container_registry.main.endpoint
}

output "registry_server_url" {
  description = "Container registry server URL"
  value       = digitalocean_container_registry.main.server_url
}

# =============================================================================
# VPC Outputs
# =============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = digitalocean_vpc.main.id
}

output "vpc_ip_range" {
  description = "IP range of the VPC"
  value       = digitalocean_vpc.main.ip_range
}
