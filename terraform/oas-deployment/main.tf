locals {
  command = (var.override ?
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --override_flow_name ${var.override_flow_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post} \
        --override_sf_pre ${var.override_sf_pre} \
        --override_sf_post ${var.override_sf_post}
      EOF
    :
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post} \
      EOF
  )

  revision = google_apigee_api.api_proxy.revision[length(google_apigee_api.api_proxy.revision) - 1]
}

data "google_client_config" "default" {
}

resource "null_resource" "prepare_apigee_bundle" {
  triggers = {
    timestamp = timestamp()
    apigee_org        = var.apigee_org
    api_name          = var.apigee_proxy_name
    api_base_path     = var.apigee_proxy_basepath
    oas_file_location = var.oas_file_location
    oas_file_name     = var.oas_file_name
    base_sf_pre       = var.base_sf_pre
    base_sf_post      = var.base_sf_post
  }

  provisioner "local-exec" {
    command = local.command
  }
}

# data "archive_file" "bundle" {
#   for_each         = local.proxy_path
#   type             = "zip"
#   source_dir       = each.value
#   output_path      = "${each.key}.zip"
#   output_file_mode = "0644"
# }

resource "google_apigee_api" "api_proxy" {
  name          = var.apigee_proxy_name
  org_id        = var.apigee_org
  config_bundle = "${var.apigee_proxy_name}.zip"
}

data "http" "deploy_api" {
  url    = "${var.apigee_mgmt_api}/organizations/${var.apigee_org}/environments/${var.apigee_env}/apis/${var.apigee_proxy_name}/revisions/${local.revision}/deployments?override=true"
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

  depends_on = [null_resource.prepare_apigee_bundle, google_apigee_api.api_proxy]
}
