module "shareflows" {
  source           = "./sharedflow-deployment"
  apigee_org       = var.apigee_org
  apigee_env       = var.apigee_env
  shared_flow_path = "${path.cwd}/../../../sharedflows"
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