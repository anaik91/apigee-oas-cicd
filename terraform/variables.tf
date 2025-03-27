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
  default = [
    "SF-spitfire-pre",
    "SF-spitfire-post",
    "SF-spitfire-override-pre",
    "SF-spitfire-override-post"
  ]
}