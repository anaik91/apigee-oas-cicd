variable "apigee_org" {
  description = "The Apigee organization name."
  default     = "apigee-payg-377208"
}

variable "apigee_env" {
  description = "The Apigee environment name (e.g., 'dev', 'prod')."
  default     = "dev"
}

variable "openid_discovery_endpoint" {
  description = "The OpenID Connect discovery endpoint URL."
  default     = "https://apigee.34.117.238.243.nip.io/jwks"
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
