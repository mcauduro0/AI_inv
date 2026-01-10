# =============================================================================
# Investment Agent System - Main Terraform Configuration
# =============================================================================
# This file defines the core infrastructure for the agentic investment system
# on DigitalOcean, including Kubernetes, databases, and storage.
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.34"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    # Configure this for your DigitalOcean Spaces backend
    # endpoint                    = "nyc3.digitaloceanspaces.com"
    # bucket                      = "investment-system-tfstate"
    # key                         = "terraform.tfstate"
    # region                      = "us-east-1" # Required but ignored for DO Spaces
    # skip_credentials_validation = true
    # skip_metadata_api_check     = true
  }
}

# =============================================================================
# Provider Configuration
# =============================================================================

provider "digitalocean" {
  token = var.do_token
}

provider "kubernetes" {
  host                   = digitalocean_kubernetes_cluster.main.endpoint
  token                  = digitalocean_kubernetes_cluster.main.kube_config[0].token
  cluster_ca_certificate = base64decode(digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = digitalocean_kubernetes_cluster.main.endpoint
    token                  = digitalocean_kubernetes_cluster.main.kube_config[0].token
    cluster_ca_certificate = base64decode(digitalocean_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate)
  }
}

# =============================================================================
# Data Sources
# =============================================================================

data "digitalocean_kubernetes_versions" "current" {
  version_prefix = "1.29."
}

# =============================================================================
# VPC - Virtual Private Cloud
# =============================================================================

resource "digitalocean_vpc" "main" {
  name        = "${var.project_name}-vpc-${var.environment}"
  region      = var.region
  ip_range    = var.vpc_ip_range
  description = "VPC for ${var.project_name} ${var.environment} environment"
}

# =============================================================================
# Kubernetes Cluster (DOKS)
# =============================================================================

resource "digitalocean_kubernetes_cluster" "main" {
  name         = "${var.project_name}-k8s-${var.environment}"
  region       = var.region
  version      = data.digitalocean_kubernetes_versions.current.latest_version
  vpc_uuid     = digitalocean_vpc.main.id
  auto_upgrade = true
  surge_upgrade = true

  maintenance_policy {
    start_time = "04:00"
    day        = "sunday"
  }

  # Default node pool for core services
  node_pool {
    name       = "core-pool"
    size       = var.k8s_node_size
    node_count = var.k8s_node_count
    auto_scale = true
    min_nodes  = var.k8s_min_nodes
    max_nodes  = var.k8s_max_nodes

    labels = {
      service = "core"
      env     = var.environment
    }

    tags = ["${var.project_name}", "${var.environment}", "core"]
  }

  tags = ["${var.project_name}", "${var.environment}"]
}

# Agent-specific node pool (for scaling agent workloads)
resource "digitalocean_kubernetes_node_pool" "agents" {
  cluster_id = digitalocean_kubernetes_cluster.main.id
  name       = "agent-pool"
  size       = var.agent_node_size
  node_count = var.agent_node_count
  auto_scale = true
  min_nodes  = var.agent_min_nodes
  max_nodes  = var.agent_max_nodes

  labels = {
    service = "agents"
    env     = var.environment
  }

  tags = ["${var.project_name}", "${var.environment}", "agents"]
}

# =============================================================================
# Managed PostgreSQL Database
# =============================================================================

resource "digitalocean_database_cluster" "postgres" {
  name                 = "${var.project_name}-pg-${var.environment}"
  engine               = "pg"
  version              = "16"
  size                 = var.db_size
  region               = var.region
  node_count           = var.db_node_count
  private_network_uuid = digitalocean_vpc.main.id

  maintenance_window {
    day  = "sunday"
    hour = "02:00:00"
  }

  tags = ["${var.project_name}", "${var.environment}", "database"]
}

# Create the main application database
resource "digitalocean_database_db" "investment_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "investment_system"
}

# Create database user for the application
resource "digitalocean_database_user" "app_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "investment_app"
}

# Firewall to allow only K8s cluster access
resource "digitalocean_database_firewall" "postgres_fw" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "k8s"
    value = digitalocean_kubernetes_cluster.main.id
  }
}

# =============================================================================
# Managed Redis Cache
# =============================================================================

resource "digitalocean_database_cluster" "redis" {
  name                 = "${var.project_name}-redis-${var.environment}"
  engine               = "redis"
  version              = "7"
  size                 = var.redis_size
  region               = var.region
  node_count           = var.redis_node_count
  private_network_uuid = digitalocean_vpc.main.id

  tags = ["${var.project_name}", "${var.environment}", "cache"]
}

# Firewall to allow only K8s cluster access
resource "digitalocean_database_firewall" "redis_fw" {
  cluster_id = digitalocean_database_cluster.redis.id

  rule {
    type  = "k8s"
    value = digitalocean_kubernetes_cluster.main.id
  }
}

# =============================================================================
# DigitalOcean Spaces (S3-compatible Object Storage)
# =============================================================================

resource "digitalocean_spaces_bucket" "main" {
  name   = "${var.project_name}-storage-${var.environment}"
  region = var.spaces_region
  acl    = "private"

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = var.cors_allowed_origins
    max_age_seconds = 3000
  }

  lifecycle_rule {
    id      = "cleanup-old-logs"
    enabled = true
    prefix  = "logs/"

    expiration {
      days = 90
    }
  }

  lifecycle_rule {
    id      = "archive-old-reports"
    enabled = true
    prefix  = "reports/"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }
  }
}

# =============================================================================
# Container Registry
# =============================================================================

resource "digitalocean_container_registry" "main" {
  name                   = "${var.project_name}-registry"
  subscription_tier_slug = var.registry_tier
  region                 = var.region
}

# Connect registry to K8s cluster
resource "digitalocean_container_registry_docker_credentials" "main" {
  registry_name = digitalocean_container_registry.main.name
}

# =============================================================================
# Load Balancer (created by Kubernetes Ingress, but we define the firewall)
# =============================================================================

resource "digitalocean_firewall" "k8s_lb" {
  name = "${var.project_name}-lb-fw-${var.environment}"

  tags = ["${var.project_name}-lb"]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# =============================================================================
# Project Resource Grouping
# =============================================================================

resource "digitalocean_project" "main" {
  name        = "${var.project_name}-${var.environment}"
  description = "Investment Agent System - ${var.environment} environment"
  purpose     = "Machine Learning / AI"
  environment = var.environment == "prod" ? "Production" : "Development"

  resources = [
    digitalocean_kubernetes_cluster.main.urn,
    digitalocean_database_cluster.postgres.urn,
    digitalocean_database_cluster.redis.urn,
    digitalocean_spaces_bucket.main.urn,
  ]
}
