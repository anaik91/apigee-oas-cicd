module "api2" {
  source                = "./oas-deployment"
  apigee_org            = "apigee-payg-377208"
  apigee_env            = "dev"
  api_proxy_path        = path.cwd
  apigee_proxy_name     = "oas2"
  apigee_proxy_basepath = "/oas2"
  oas_file_location     = path.cwd
  oas_file_name         = "httpbin.yaml"
  base_sf_pre           = "SF-spitfire-pre"
  base_sf_post          = "SF-spitfire-post"
  override              = false

  depends_on = [module.shareflows]
}