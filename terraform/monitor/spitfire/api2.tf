module "api2" {
  source                = "./apigee-oas-deployment"
  apigee_org            = var.apigee_org
  apigee_env            = var.apigee_env
  api_proxy_path        = path.cwd
  apigee_proxy_name     = "oas2"
  apigee_proxy_basepath = "/oas2"
  oas_file_location     = path.cwd
  oas_file_name         = "openapi.yaml"
  base_sf_pre           = "SF-spitfire-pre"
  base_sf_post          = "SF-spitfire-post"
  override              = true
  override_flow_name    = "getFeatureState"
  override_sf_pre       = "SF-spitfire-override-pre"
  override_sf_post      = "SF-spitfire-override-post"
  # gcs_bucket            = module.apigee_proxy_state.name
  # gcs_object_prefix     = "apis/dev"
  depends_on = [module.shareflows]
}