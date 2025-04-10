locals {
  command = (var.override ?
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --target_url ${var.target_url} \
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
        --target_url ${var.target_url} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post}
      EOF
  )

  # pull_command = (var.override ?
  #   <<EOF
  #     python3 ${path.module}/scripts/prepare_bundle.py \
  #       --apigee_org ${var.apigee_org} \
  #       --api_name ${var.apigee_proxy_name} \
  #       --api_base_path ${var.apigee_proxy_basepath} \
  #       --target_url ${var.target_url} \
  #       --oas_file_location ${var.oas_file_location} \
  #       --oas_file_name ${var.oas_file_name} \
  #       --override_flow_name ${var.override_flow_name} \
  #       --base_sf_pre ${var.base_sf_pre} \
  #       --base_sf_post ${var.base_sf_post} \
  #       --override_sf_pre ${var.override_sf_pre} \
  #       --override_sf_post ${var.override_sf_post} \
  #       --gcs_pull \
  #       --gcs_bucket ${var.gcs_bucket} \
  #       --gcs_object_prefix ${var.gcs_object_prefix}
  #     EOF
  #   :
  #   <<EOF
  #     python3 ${path.module}/scripts/prepare_bundle.py \
  #       --apigee_org ${var.apigee_org} \
  #       --api_name ${var.apigee_proxy_name} \
  #       --api_base_path ${var.apigee_proxy_basepath} \
  #       --target_url ${var.target_url} \
  #       --oas_file_location ${var.oas_file_location} \
  #       --oas_file_name ${var.oas_file_name} \
  #       --base_sf_pre ${var.base_sf_pre} \
  #       --base_sf_post ${var.base_sf_post} \
  #       --gcs_pull \
  #       --gcs_bucket ${var.gcs_bucket} \
  #       --gcs_object_prefix ${var.gcs_object_prefix}
  #     EOF
  # )

  deploy_command = (var.override ?
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --target_url ${var.target_url} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --override_flow_name ${var.override_flow_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post} \
        --override_sf_pre ${var.override_sf_pre} \
        --override_sf_post ${var.override_sf_post} \
        --deploy_revision \
        --apigee_env ${var.apigee_env} \
        --api_revision ${local.revision}
      EOF
    :
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --target_url ${var.target_url} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post} \
        --deploy_revision \
        --apigee_env ${var.apigee_env} \
        --api_revision ${local.revision}
      EOF
  )

  undeploy_command = (var.override ?
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --target_url ${var.target_url} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --override_flow_name ${var.override_flow_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post} \
        --override_sf_pre ${var.override_sf_pre} \
        --override_sf_post ${var.override_sf_post} \
        --undeploy_revision \
        --apigee_env ${var.apigee_env} \
        --api_revision ${local.revision}
      EOF
    :
    <<EOF
      python3 ${path.module}/scripts/prepare_bundle.py \
        --apigee_org ${var.apigee_org} \
        --api_name ${var.apigee_proxy_name} \
        --api_base_path ${var.apigee_proxy_basepath} \
        --target_url ${var.target_url} \
        --oas_file_location ${var.oas_file_location} \
        --oas_file_name ${var.oas_file_name} \
        --base_sf_pre ${var.base_sf_pre} \
        --base_sf_post ${var.base_sf_post} \
        --undeploy_revision \
        --apigee_env ${var.apigee_env} \
        --api_revision ${local.revision}
      EOF
  )

  revision = google_apigee_api.api_proxy.revision[length(google_apigee_api.api_proxy.revision) - 1]
}

data "google_client_config" "default" {
}

resource "null_resource" "prepare_apigee_bundle" {
  triggers = {
    # timestamp         = timestamp()
    apigee_org        = var.apigee_org
    api_name          = var.apigee_proxy_name
    api_base_path     = var.apigee_proxy_basepath
    oas_file_location = var.oas_file_location
    oas_file_name     = var.oas_file_name
    oas_file_sha      = var.oas_file_sha
    base_sf_pre       = var.base_sf_pre
    base_sf_post      = var.base_sf_post
  }

  provisioner "local-exec" {
    command = local.command
  }
}

# resource "null_resource" "pull_apigee_bundle" {
#   triggers = {
#     # timestamp         = timestamp()
#     apigee_org        = var.apigee_org
#     api_name          = var.apigee_proxy_name
#     api_base_path     = var.apigee_proxy_basepath
#     oas_file_location = var.oas_file_location
#     oas_file_name     = var.oas_file_name
#     oas_file_sha      = var.oas_file_sha
#     base_sf_pre       = var.base_sf_pre
#     base_sf_post      = var.base_sf_post
#   }

#   provisioner "local-exec" {
#     command = local.pull_command
#   }
# }


resource "google_apigee_api" "api_proxy" {
  name          = var.apigee_proxy_name
  org_id        = var.apigee_org
  config_bundle = "${var.apigee_proxy_name}.zip"
  depends_on = [null_resource.prepare_apigee_bundle,
  ]
}

resource "null_resource" "deploy_proxy_revision" {
  triggers = {
    deploy_command = local.deploy_command
  }
  provisioner "local-exec" {
    command = self.triggers.deploy_command
  }
  depends_on = [ google_apigee_api.api_proxy ]
}


resource "null_resource" "undeploy_proxy_revision" {
  triggers = {
    undeploy_command = local.undeploy_command
  }
  provisioner "local-exec" {
    when = destroy
    command = self.triggers.undeploy_command
  }
  depends_on = [ google_apigee_api.api_proxy ]
}