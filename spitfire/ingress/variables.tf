variable "istio_version" {
    default = "1.22.3"
}


variable "istio_istiod_values_path" {
  default = "istio-istiod-values.yaml"
}

variable "istio_ingress_gateway_values_path" {
  default = "istio-ingress-gateway-values.yaml"
}