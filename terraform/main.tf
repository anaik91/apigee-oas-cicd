data "google_client_config" "default" {
}

data "archive_file" "bundle" {
  type             = "zip"
  source_dir       = var.proxy_bundle_path
  output_path      = "${var.proxy_name}.zip"
  output_file_mode = "0644"
}

resource "google_apigee_api" "api_proxy" {
  name          = var.proxy_name
  org_id        = var.apigee_org
  config_bundle = data.archive_file.bundle.output_path
}

locals {
  revisions       = google_apigee_api.api_proxy.revision
  latest_revision = local.revisions[length(local.revisions) - 1]
  shared_flow_path = {
  for key in var.shared_flows : key => "${var.shared_flow_path}/${key}" }
}

data "http" "deploy_api" {
  url    = "${var.apigee_mgmt_api}/organizations/${var.apigee_org}/environments/${var.apigee_env}/apis/${google_apigee_api.api_proxy.name}/revisions/${local.latest_revision}/deployments?override=true"
  method = "POST"

  request_headers = {
    "Authorization" : "Bearer ${data.google_client_config.default.access_token}"
  }

  lifecycle {
    postcondition {
      condition     = strcontains(self.response_body, "already deployed") || contains([200], self.status_code)
      error_message = "Failed to deploy API ${self.response_body}"
    }
  }
}


data "archive_file" "shared_flow_bundle" {
  for_each         = local.shared_flow_path
  type             = "zip"
  source_dir       = each.value
  output_path      = "${each.key}.zip"
  output_file_mode = "0644"
}

resource "google_apigee_sharedflow" "shared_flow" {
  for_each      = local.shared_flow_path
  name          = each.key
  org_id        = var.apigee_org
  config_bundle = data.archive_file.shared_flow_bundle[each.key].output_path
}

# resource "google_apigee_sharedflow_deployment" "shared_flow" {
#   for_each      = local.shared_flow_path
#   org_id        = var.apigee_org
#   environment   = var.apigee_env
#   sharedflow_id = each.key
#   revision      = google_apigee_sharedflow.shared_flow[each.key].latest_revision_id
# }

data "http" "deploy_sharedflow" {
  for_each      = local.shared_flow_path
  url    = "${var.apigee_mgmt_api}/organizations/${var.apigee_org}/environments/${var.apigee_env}/sharedflows/${each.key}/revisions/${google_apigee_sharedflow.shared_flow[each.key].latest_revision_id}/deployments?override=true"
  method = "POST"

  request_headers = {
    "Authorization" : "Bearer ${data.google_client_config.default.access_token}"
  }

  lifecycle {
    postcondition {
      condition     = strcontains(self.response_body, "already deployed") || contains([200], self.status_code)
      error_message = "Failed to deploy API ${self.response_body}"
    }
  }
}