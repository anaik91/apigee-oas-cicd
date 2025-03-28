locals {

  env_id = "organizations/${var.apigee_org}/environments/${var.apigee_env}"
  proxy_path = {
    for key in var.api_proxies : key => "${var.api_proxy_path}/${key}"
  }

  proxy_revisions = {
    for key in var.api_proxies : key => google_apigee_api.api_proxy[key].revision[
      length(google_apigee_api.api_proxy[key].revision) - 1
    ]
  }

  shared_flow_path = {
  for key in var.shared_flows : key => "${var.shared_flow_path}/${key}" }
}

data "google_client_config" "default" {
}

resource "google_apigee_target_server" "apigee_target_server" {
  for_each    = var.target_servers
  name        = each.key
  description = "Apigee Target Server: ${each.key}"
  protocol    = each.value.protocol
  host        = each.value.host
  port        = each.value.port
  env_id      = local.env_id
  s_sl_info {
    enabled = each.value.ssl_enabled
  }
}

resource "google_apigee_environment_keyvaluemaps" "apigee_environment_keyvaluemaps" {
  env_id = local.env_id
  name   = var.kvm_name
}

resource "google_apigee_environment_keyvaluemaps_entries" "apigee_environment_keyvaluemaps_entries" {
  env_keyvaluemap_id = google_apigee_environment_keyvaluemaps.apigee_environment_keyvaluemaps.id
  name               = "url"
  value              = var.openid_discovery_endpoint
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

resource "google_apigee_sharedflow_deployment" "shared_flow" {
  for_each      = local.shared_flow_path
  org_id        = var.apigee_org
  environment   = var.apigee_env
  sharedflow_id = each.key
  revision      = google_apigee_sharedflow.shared_flow[each.key].latest_revision_id
  depends_on = [google_apigee_environment_keyvaluemaps_entries.apigee_environment_keyvaluemaps_entries,
  google_apigee_target_server.apigee_target_server]
}

data "archive_file" "bundle" {
  for_each         = local.proxy_path
  type             = "zip"
  source_dir       = each.value
  output_path      = "${each.key}.zip"
  output_file_mode = "0644"
}

resource "google_apigee_api" "api_proxy" {
  for_each      = local.proxy_path
  name          = each.key
  org_id        = var.apigee_org
  config_bundle = data.archive_file.bundle[each.key].output_path
}

data "http" "deploy_api" {
  for_each = local.proxy_path
  url      = "${var.apigee_mgmt_api}/organizations/${var.apigee_org}/environments/${var.apigee_env}/apis/${each.key}/revisions/${local.proxy_revisions[each.key]}/deployments?override=true"
  method   = "POST"

  request_headers = {
    "Authorization" : "Bearer ${data.google_client_config.default.access_token}"
  }

  lifecycle {
    postcondition {
      condition     = strcontains(self.response_body, "already deployed") || contains([200], self.status_code)
      error_message = "Failed to deploy API ${self.response_body}"
    }
  }

  depends_on = [google_apigee_sharedflow_deployment.shared_flow]
}
