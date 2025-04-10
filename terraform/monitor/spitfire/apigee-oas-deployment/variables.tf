variable "apigee_mgmt_api" {
  description = "The base URL for the Apigee Management API."
  default     = "https://apigee.googleapis.com/v1"
}

variable "apigee_org" {
  description = "The Apigee organization name."
  default     = ""
}

variable "apigee_env" {
  description = "The Apigee environment name (e.g., 'dev', 'prod')."
  default     = ""
}

variable "api_proxy_path" {
  description = "The base path where API proxy bundles are located."
  default     = ""
}

variable "apigee_proxy_name" {
  description = "A list of API proxy names to be deployed."
  type        = string
  default     = ""
}


variable "apigee_proxy_basepath" {
  type    = string
  default = ""
}

variable "target_url" {
  type    = string
  default = "https://localhost:8443"
}

variable "oas_file_location" {
  type    = string
  default = ""
}

variable "oas_file_name" {
  type    = string
  default = ""
}

variable "oas_file_sha" {
  type    = string
  default = ""
}

variable "override_flow_name" {
  type    = string
  default = ""
}

variable "base_sf_pre" {
  type    = string
  default = ""
}

variable "base_sf_post" {
  type    = string
  default = ""
}

variable "override" {
  type    = bool
  default = false
}

variable "override_sf_pre" {
  type    = string
  default = ""
}

variable "override_sf_post" {
  type    = string
  default = ""
}

# variable "gcs_bucket" {
#   type        = string
#   description = "Bucket to store API Proxy Bundles"
# }

# variable "gcs_object_prefix" {
#   type        = string
#   description = "Object Prefix to store API Proxy Bundles"
# }