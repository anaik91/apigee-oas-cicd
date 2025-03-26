variable "apigee_mgmt_api" {
  default = "https://apigee.googleapis.com/v1"
}

variable "apigee_org" {
  default = "apigee-payg-377208"
}

variable "apigee_env" {
  default = "dev"
}

variable "proxy_name" {
  default = "proxy1"
}

variable "proxy_bundle_path" {
  default = "api"
}

data "google_client_config" "default" {
}

data "archive_file" "bundle" {
  type             = "zip"
  source_dir       = "${path.module}/${var.proxy_bundle_path}"
  output_path      = "${path.module}/bundle.zip"
  output_file_mode = "0644"
}

resource "google_apigee_api" "api_proxy" {
  name          = var.proxy_name
  org_id        = var.apigee_org
  config_bundle = data.archive_file.bundle.output_path
}

locals {
  revisions = google_apigee_api.api_proxy.revision
  latest_revision = local.revisions[length(local.revisions) - 1]
}

data "http" "deploy_api" {
  url = "${var.apigee_mgmt_api}/organizations/${var.apigee_org}/environments/${var.apigee_env}/apis/${google_apigee_api.api_proxy.name}/revisions/${local.latest_revision}/deployments?override=true"
  method = "POST"

  request_headers = {
    "Authorization": "Bearer ${data.google_client_config.default.access_token}"
  }

  lifecycle {
    postcondition {
      condition     = strcontains(self.response_body, "already deployed") || contains([200], self.status_code)
      error_message = "Failed to deploy API ${self.response_body}"
    }
  }
}