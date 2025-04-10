#!/bin/bash
set -e

SCRIPTPATH="$(
    cd "$(dirname "$0")" || exit >/dev/null 2>&1
    pwd -P
)"

CENTRIFUGO_HELM_REPO="https://centrifugal.github.io/helm-charts"
# GRAFANA_HELM_REPO="https://grafana.github.io/helm-charts"
# PROMETHEUS_HELM_REPO="https://prometheus-community.github.io/helm-charts"
CENTRIFUGO_CHART_NAME="centrifugal/centrifugo"
CENTRIFUGO_RELEASE_NAME="centrifugo"
CENTRIFUGO_NAMESPACE="centrifugo"

# GRAFANA_CHART_NAME="grafana/grafana"
# GRAFANA_RELEASE_NAME="grafana"
# GRAFANA_NAMESPACE="grafana"

# PROMETHEUS_CHART_NAME="prometheus-community/prometheus"
# PROMETHEUS_RELEASE_NAME="prometheus"
# PROMETHEUSNAMESPACE="prometheus"


helm repo add centrifugal "${CENTRIFUGO_HELM_REPO}"
# helm repo add prometheus-community "${PROMETHEUS_HELM_REPO}"
# helm repo add grafana "${GRAFANA_HELM_REPO}"
helm repo update

helm upgrade \
    --install \
    --namespace "${CENTRIFUGO_NAMESPACE}" \
    --create-namespace \
    "${CENTRIFUGO_RELEASE_NAME}" \
    "${CENTRIFUGO_CHART_NAME}" \
    -f "${SCRIPTPATH}/centrifugo_values.yaml"

# helm upgrade \
#     --install \
#     --namespace "${GRAFANA_NAMESPACE}" \
#     --create-namespace \
#     "${GRAFANA_RELEASE_NAME}" \
#     "${GRAFANA_CHART_NAME}" \
#     -f "${SCRIPTPATH}/grafana_values.yaml"