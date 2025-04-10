resource "kubernetes_namespace" "istio_ingress" {
  metadata {
    name = "istio-ingress"
    labels = {
      istio-injection="enabled"
    }
  }
}

resource "helm_release" "istio_ingressgateway" {
  name       = "istio-ingress"

  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  wait = "true"
  namespace = kubernetes_namespace.istio_ingress.metadata[0].name
  values = [
    "${file("${var.istio_ingress_gateway_values_path}")}"
  ]
  version = var.istio_version

  depends_on = [
    kubernetes_namespace.istio_ingress
  ]
}