# =============================================================================
# Monitoring Stack Module - Prometheus, Grafana, Loki
# =============================================================================

# =============================================================================
# Prometheus Stack (includes Grafana)
# =============================================================================

resource "helm_release" "prometheus_stack" {
  count = var.enable_monitoring ? 1 : 0

  name             = "prometheus"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true
  version          = "55.5.0"

  values = [<<-EOF
    prometheus:
      prometheusSpec:
        retention: 15d
        storageSpec:
          volumeClaimTemplate:
            spec:
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: 50Gi
        serviceMonitorSelectorNilUsesHelmValues: false
        podMonitorSelectorNilUsesHelmValues: false

    grafana:
      enabled: true
      adminPassword: "${var.grafana_admin_password}"
      persistence:
        enabled: true
        size: 10Gi
      dashboardProviders:
        dashboardproviders.yaml:
          apiVersion: 1
          providers:
          - name: 'default'
            orgId: 1
            folder: ''
            type: file
            disableDeletion: false
            editable: true
            options:
              path: /var/lib/grafana/dashboards/default
      dashboards:
        default:
          investment-system:
            gnetId: 15757
            revision: 1
            datasource: Prometheus

    alertmanager:
      enabled: true
      alertmanagerSpec:
        storage:
          volumeClaimTemplate:
            spec:
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: 10Gi
  EOF
  ]

  depends_on = [digitalocean_kubernetes_cluster.main]
}

# =============================================================================
# Loki for Log Aggregation
# =============================================================================

resource "helm_release" "loki" {
  count = var.enable_logging ? 1 : 0

  name             = "loki"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki-stack"
  namespace        = "monitoring"
  create_namespace = true
  version          = "2.9.11"

  values = [<<-EOF
    loki:
      enabled: true
      persistence:
        enabled: true
        size: 50Gi
    
    promtail:
      enabled: true
    
    grafana:
      enabled: false  # Using grafana from prometheus-stack
  EOF
  ]

  depends_on = [helm_release.prometheus_stack]
}

# =============================================================================
# Variables for Monitoring Module
# =============================================================================

variable "grafana_admin_password" {
  description = "Admin password for Grafana"
  type        = string
  sensitive   = true
  default     = "admin"  # Change in production!
}
