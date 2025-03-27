variable "apigee_mgmt_api" {
  default = "https://apigee.googleapis.com/v1"
}

variable "apigee_org" {
  default = ""
}

variable "apigee_env" {
  default = ""
}

variable "proxy_name" {
  default = "proxy1"
}

variable "proxy_bundle_path" {
  default = ""
}

variable "shared_flow_path" {
  default = ""
}

variable "shared_flows" {
  type = list(string)
  default = [
    "SF-spitfire-pre",
    "SF-spitfire-post",
    "SF-spitfire-override-pre",
    "SF-spitfire-override-post"
  ]
}

variable "target_servers" {
  type = map(object({
    host        = string
    port        = number
    protocol    = string
    ssl_enabled = bool
  }))
  description = "Map of target servers to use"
  default = {
    "user-manager-user-query" = {
      host        = "example.com"
      port        = 443
      protocol    = "HTTP"
      ssl_enabled = true
    }
    "user-manager-user-create" = {
      host        = "example.com"
      port        = 443
      protocol    = "HTTP"
      ssl_enabled = true
    }
    "auth-manager-token-introspect" = {
      host        = "example.com"
      port        = 443
      protocol    = "HTTP"
      ssl_enabled = true
    }
  }
}