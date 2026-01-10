# =============================================================================
# Investment Agent System - Terraform Variables
# =============================================================================

# =============================================================================
# Core Configuration
# =============================================================================

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "investment-agent"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "region" {
  description = "DigitalOcean region for resources"
  type        = string
  default     = "nyc3"
}

variable "spaces_region" {
  description = "DigitalOcean Spaces region (may differ from main region)"
  type        = string
  default     = "nyc3"
}

# =============================================================================
# VPC Configuration
# =============================================================================

variable "vpc_ip_range" {
  description = "IP range for the VPC"
  type        = string
  default     = "10.10.0.0/16"
}

# =============================================================================
# Kubernetes Configuration
# =============================================================================

variable "k8s_node_size" {
  description = "Size of Kubernetes nodes for core services"
  type        = string
  default     = "s-2vcpu-4gb"
}

variable "k8s_node_count" {
  description = "Initial number of nodes in the core pool"
  type        = number
  default     = 2
}

variable "k8s_min_nodes" {
  description = "Minimum number of nodes for autoscaling"
  type        = number
  default     = 2
}

variable "k8s_max_nodes" {
  description = "Maximum number of nodes for autoscaling"
  type        = number
  default     = 5
}

variable "agent_node_size" {
  description = "Size of Kubernetes nodes for agent workloads"
  type        = string
  default     = "s-4vcpu-8gb"
}

variable "agent_node_count" {
  description = "Initial number of nodes in the agent pool"
  type        = number
  default     = 2
}

variable "agent_min_nodes" {
  description = "Minimum number of agent nodes for autoscaling"
  type        = number
  default     = 1
}

variable "agent_max_nodes" {
  description = "Maximum number of agent nodes for autoscaling"
  type        = number
  default     = 10
}

# =============================================================================
# Database Configuration
# =============================================================================

variable "db_size" {
  description = "Size of the PostgreSQL database cluster"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "db_node_count" {
  description = "Number of nodes in the PostgreSQL cluster"
  type        = number
  default     = 1
}

variable "redis_size" {
  description = "Size of the Redis cache cluster"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "redis_node_count" {
  description = "Number of nodes in the Redis cluster"
  type        = number
  default     = 1
}

# =============================================================================
# Storage Configuration
# =============================================================================

variable "cors_allowed_origins" {
  description = "Allowed origins for CORS on Spaces bucket"
  type        = list(string)
  default     = ["*"]
}

variable "registry_tier" {
  description = "Container registry subscription tier"
  type        = string
  default     = "starter"
}

# =============================================================================
# Application Configuration
# =============================================================================

variable "app_domain" {
  description = "Primary domain for the application"
  type        = string
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable Prometheus/Grafana monitoring stack"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable centralized logging with Loki"
  type        = bool
  default     = true
}
