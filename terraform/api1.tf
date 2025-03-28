module "api1" {
  source                = "./oas-deployment"
  apigee_org            = var.apigee_org
  apigee_env            = var.apigee_env
  api_proxy_path        = path.module
  apigee_proxy_name     = "oas1"
  apigee_proxy_basepath = "/oas1"
  oas_file_location     = path.module
  oas_file_name         = "httpbin.yaml"
  override_flow_name    = "getUsersGroups"
  base_sf_pre           = "SF-spitfire-pre"
  base_sf_post          = "SF-spitfire-post"
  override              = true
  override_sf_pre       = "SF-spitfire-override-pre"
  override_sf_post      = "SF-spitfire-override-post"

  depends_on = [module.shareflows]
}