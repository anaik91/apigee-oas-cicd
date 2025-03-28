module "shareflows" {
  source           = "./sharedflow-deployment"
  apigee_org       = "apigee-payg-377208"
  apigee_env       = "dev"
  shared_flow_path = "${path.cwd}/../sharedflows"
  shared_flows = [
    "SF-spitfire-pre",
    "SF-spitfire-post",
    "SF-spitfire-override-pre",
    "SF-spitfire-override-post"
  ]
  kvm_name                  = "openid_config"
  openid_discovery_endpoint = var.openid_discovery_endpoint
  target_servers            = var.target_servers
}