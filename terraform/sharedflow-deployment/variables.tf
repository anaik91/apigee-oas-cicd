variable "apigee_org" {
  description = "The Apigee organization name."
  default     = ""
}

variable "apigee_env" {
  description = "The Apigee environment name (e.g., 'dev', 'prod')."
  default     = ""
}


variable "shared_flow_path" {
  description = "The base path where shared flow bundles are located."
  default     = ""
}

variable "shared_flows" {
  description = "A list of shared flow names to be deployed."
  type        = list(string)
  default = [
    "SF-spitfire-pre",
    "SF-spitfire-post",
    "SF-spitfire-override-pre",
    "SF-spitfire-override-post"
  ]
}

variable "kvm_name" {
  description = "The name of the Key-Value Map (KVM) to store openid discovery config."
  default     = "openid_config"
}

variable "openid_discovery_endpoint" {
  description = "The OpenID Connect discovery endpoint URL."
  default     = ""
}

variable "target_servers" {
  type = map(object({
    host        = string
    port        = number
    protocol    = string
    ssl_enabled = bool
  }))
  description = "Map of target servers to use across all APIs"
  default = {
    "user-manager-user-query" = {
      host        = "example.com"
      port        = 443
      protocol    = "HTTP"
      ssl_enabled = true
    },
    "user-manager-user-create" = {
      host        = "example.com"
      port        = 443
      protocol    = "HTTP"
      ssl_enabled = true
    },
    "auth-manager-token-introspect" = {
      host        = "example.com"
      port        = 443
      protocol    = "HTTP"
      ssl_enabled = true
    }
  }
}
