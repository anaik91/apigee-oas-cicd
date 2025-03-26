# Deploy Apigee Proxy from OpenAPI Spec
The following repository contains code which can convert and openapi spec to Apigee API proxy bundle and it will can automatically inject sharedflows based on the input provide. Once the bundle is generated it uses terraform to deploy the API into Apigee Organization

## Scripts

Script to inject default sharedflows across all OAS operations

```bash

cd scripts
python3 prepare_bundle.py  \
  --apigee_org apigee-payg-377208 \
  --api_name newapi \
  --api_base_path /newapi \
  --oas_file_location . \
  --oas_file_name httpbin.yaml
```

Script to inject default sharedflows across all OAS operations except the overridden OAS operation

```bash
cd scripts
python3 prepare_bundle.py \
--apigee_org apigee-payg-377208 \
--api_name newapi \
--api_base_path /newapi \
--oas_file_location . \
--oas_file_name httpbin.yaml \
--override_flow_name getUsersGroups \
--override_sf_name FC-Base-Pre
```

## Terraform

Follow the instructions to run terraform

```bash
cd terraform

terraform init

terraform plan \
    -var "apigee_org=$APIGEE_ORG }}" \
    -var "apigee_env=$APIGEE_ENV" \
    -var "proxy_name=$APIGEE_PROXY_NAME" \
    -var "proxy_bundle_path=<PATH>"

terraform apply \
    -auto-approve \
    -var "apigee_org=$APIGEE_ORG }}" \
    -var "apigee_env=$APIGEE_ENV" \
    -var "proxy_name=$APIGEE_PROXY_NAME" \
    -var "proxy_bundle_path=<PATH>"
```