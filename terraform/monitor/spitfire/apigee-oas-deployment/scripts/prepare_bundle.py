import argparse
import subprocess
import shlex  # For safer string splitting if needed
import logging
import os
import sys
import zipfile
import shutil
import requests
import json
import xmltodict
from google.cloud import storage
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set default log level (can be changed)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ApigeeCliRunner:
    """
    A class to encapsulate the execution of the apigeecli command for creating APIs.

    This class manages the construction of the command, execution via subprocess,
    and logging of results.  It allows for easy instantiation and reuse with
    different parameter sets.  It also provides a method to unzip the generated
    API proxy bundle.
    """

    def __init__(
            self,
            access_token,
            basepath="/testoas",
            name="testoas",
            oas_base_folderpath=".",
            oas_name="httpbin.yaml",
            org="test-org",
            target_url="http://localhost:8080",
            default_token=True,  # Boolean parameter
            import_api=False,    # Boolean parameter, renamed to avoid clash with import keyword
            validate=True,      # Boolean parameter
            skip_policy=True,     # Boolean parameter
            ):
        """
        Initializes the ApigeeCliRunner with the specified parameters.

        Parameters:
            basepath (str): The basepath for the API.
            name (str): The name of the API.
            oas_base_folderpath (str): The path to the folder containing the OpenAPI specification.
            oas_name (str): The name of the OpenAPI specification file.
            org (str): The Apigee organization.
            default_token (bool): Whether to use the default token for authentication.
            import_api (bool): Whether to import the API.  Renamed from 'import' to 'import_api'
                             to avoid keyword clash.
            validate (bool): Whether to validate the OpenAPI specification.
            skip_policy (bool): Whether to skip policy attachment.
            output_dir (str): The directory where the generated bundle should be created.
        """
        self.basepath = basepath
        self.name = name
        self.oas_base_folderpath = oas_base_folderpath
        self.oas_name = oas_name
        self.org = org
        self.target_url = target_url
        self.default_token = default_token
        self.import_api = import_api
        self.validate = validate
        self.skip_policy = skip_policy
        self.access_token = access_token


    def create_bundle(self):
        """
        Executes the apigeecli command to create an API proxy bundle.

        Returns:
            str: The full path to the created ZIP file, or None if creation failed.
        """

        command = [
            "apigeecli",
            "apis",
            "create",
            "openapi",
            "--basepath", self.basepath,
            "--name", self.name,
            "--oas-base-folderpath", self.oas_base_folderpath,
            "--oas-name", self.oas_name,
            "--org", self.org,
            "--target-url", self.target_url,
        ]

        # Add boolean arguments conditionally
        if self.default_token:
            command.append("--default-token")
        if self.import_api is False:  # The apigeecli expects the flag without the value.
            command.append("--import=false")  # the api needs the value set to false.
        if self.validate:
            command.append("--validate")
        if self.skip_policy:
            command.append("--skip-policy")

        logging.info(" Running apigeecli command ")
        logging.info(shlex.join(command))  # Print the command for clarity
        logging.info("--")

        try:
            result = subprocess.run(
                command,
                check=True,       # Raise CalledProcessError on non-zero exit code
                capture_output=True,  # Capture standard output and standard error
                text=True          # Decode output as text (UTF-8)
            )

            logging.info(" Command executed successfully ")
            logging.info("STDOUT:\n%s", result.stdout)
            if result.stderr:  # Only log if there's something on stderr
                logging.warning("STDERR:\n%s", result.stderr)  # Use warning level for stderr

            return True

        except subprocess.CalledProcessError as e:
            logging.error(" Command failed ")
            logging.error(f"Return code: {e.returncode}")
            logging.error("STDOUT:\n%s", e.stdout)
            logging.error("STDERR:\n%s", e.stderr)
            return False  # Indicate failure

        except FileNotFoundError:
            logging.error(" Error: apigeecli not found ")
            logging.error("Please ensure 'apigeecli' is installed and in your system's PATH.")
            return False  # Indicate failure

        except Exception as e:
            logging.exception(" An unexpected error occurred ")  # Use logging.exception to include traceback
            return False # Indicate failure

    def unzip_bundle(self, bundle_path, extract_path=None):
        """
        Unzips the specified API proxy bundle.

        Parameters:
            bundle_path (str): The path to the ZIP file to unzip.
            extract_path (str, optional): The directory to extract the contents to.
                If None, a directory with the same name as the bundle (without the .zip)
                will be created in the same directory as the bundle. Defaults to None.
        """

        if not extract_path:
            extract_path = os.path.splitext(bundle_path)[0]  # Remove .zip and use as directory name

        try:
            with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            logging.info(f" Successfully extracted bundle to: {extract_path} ")
        except FileNotFoundError:
            logging.error(f" Error: Bundle not found at {bundle_path} ")
        except zipfile.BadZipFile:
            logging.error(f" Error: Invalid ZIP file: {bundle_path} ")
        except Exception as e:
            logging.exception(f" An error occurred while unzipping the bundle ")
    

    def inject_policy(self, bundle_dir, policy_name, policy_content):
        """
        Injects an XML policy file into the specified API proxy bundle directory.

        Parameters:
            bundle_dir (str): The path to the extracted API proxy bundle directory.
            policy_name (str): The name of the policy file (e.g., "MyPolicy").
            policy_content (str): The XML content of the policy.
        """

        policies_dir = os.path.join(bundle_dir, "apiproxy", "policies")

        # Create the policies directory if it doesn't exist
        if not os.path.exists(policies_dir):
            os.makedirs(policies_dir)

        policy_path = os.path.join(policies_dir, f"{policy_name}.xml")

        try:
            with open(policy_path, "w") as f:
                f.write(policy_content)
            logging.info(f" Successfully injected policy '{policy_name}' into: {policies_dir} ")
        except Exception as e:
            logging.exception(f" An error occurred while injecting policy '{policy_name}' ")

    def zip_bundle(self, bundle_dir, output_zip_path=None):
        """
        Zips the API proxy bundle directory into a ZIP file.

        Parameters:
            bundle_dir (str): The path to the API proxy bundle directory to zip.
            output_zip_path (str, optional): The path to the output ZIP file.
                If None, a ZIP file with the same name as the bundle directory
                will be created in the same directory.  Defaults to None.

        Returns:
            str: The path to the created ZIP file, or None if zipping failed.
        """
        if not output_zip_path:
            output_zip_path = bundle_dir + ".zip" # e.g., "output/all-params-api.zip"

        try:
            # Use shutil.make_archive to create the zip file
            shutil.make_archive(os.path.splitext(output_zip_path)[0], 'zip', bundle_dir)
            logging.info(f" Successfully zipped bundle to: {output_zip_path} ")
            return output_zip_path

        except FileNotFoundError:
            logging.error(f" Error: Bundle directory not found: {bundle_dir} ")
            return None
        except Exception as e:
            logging.exception(f" An error occurred while zipping the bundle ")
            return None

    def inject_shared_flow_to_flows(self, bundle_dir, shared_flow_name, flow_names, flow_type="Request"):
        """
        Parses apiproxy/proxies/default.xml, injects a shared flow callout into specified flows.

        Args:
            bundle_dir (str): Path to the extracted bundle directory.
            shared_flow_name (str): Name of the shared flow to inject.
            flow_names (list): List of flow names where the shared flow should be injected. If "PreFlow", then it will inject in the preflow, and the same with PostFlow
            flow_type (str):  "Request" or "Response" to indicate where to inject the SharedFlow.
        """

        proxy_xml_path = os.path.join(bundle_dir, "apiproxy", "proxies", "default.xml")

        if flow_type not in ["Request", "Response"]:
            logging.error(f"Invalid flow_type: {flow_type}. Must be 'Request' or 'Response'.")
            return

        try:
            with open(proxy_xml_path, "r") as f:
                xml_content = f.read()

            proxy_dict = xmltodict.parse(xml_content)

            if "PreFlow" in flow_names:
                preflow = proxy_dict['ProxyEndpoint']['PreFlow']
                self._inject_shared_flow(preflow, shared_flow_name, flow_type)
                flow_names.remove("PreFlow") # Remove PreFlow so it isn't processed in the loop
            if "PostFlow" in flow_names:
                postflow = proxy_dict['ProxyEndpoint']['PostFlow']
                self._inject_shared_flow(postflow, shared_flow_name, flow_type)
                flow_names.remove("PostFlow")

            # Locate the desired flows and insert the shared flow callout
            flows = proxy_dict.get('ProxyEndpoint', {}).get('Flows', {}).get('Flow', [])
            if isinstance(flows, dict):
                flows = [flows]
            for flow in flows:
                if flow['@name'] in flow_names:
                    # Insert the SharedFlowCallout at the beginning of the specified flow chain
                    if flow_type not in flow or flow[flow_type] is None:
                        flow[flow_type] = {}
                    if 'Step' not in flow[flow_type] or flow[flow_type]['Step'] is None:
                        flow[flow_type]['Step'] = []
                    if not isinstance(flow[flow_type]['Step'], list):
                        flow[flow_type]['Step'] = [flow[flow_type]['Step']] # Ensure 'Step' is a list
                    flow[flow_type]['Step'].insert(0, {'Name': shared_flow_name})

            # Convert the modified dictionary back to XML
            updated_xml_content = xmltodict.unparse(proxy_dict, pretty=True)

            # Write the updated XML content back to the file
            with open(proxy_xml_path, "w") as f:
                f.write(updated_xml_content)

            logging.info(f" Successfully injected shared flow '{shared_flow_name}' into {flow_type} flows: {flow_names} ")

        except FileNotFoundError:
            logging.error(f" Error: Proxy XML file not found: {proxy_xml_path} ")
        except Exception as e:
            logging.exception(" An error occurred while injecting shared flow ")

    def _inject_shared_flow(self, flow_element, shared_flow_name, flow_type):
        """
        Helper function to inject the shared flow into pre or post flow
        """
        if flow_type not in flow_element or flow_element[flow_type] is None:
            flow_element[flow_type] = {}
        if 'Step' not in flow_element[flow_type] or flow_element[flow_type]['Step'] is None:
            flow_element[flow_type]['Step'] = []
        if not isinstance(flow_element[flow_type]['Step'], list):
            flow_element[flow_type]['Step'] = [flow_element[flow_type]['Step']]  # Ensure 'Step' is a list
        flow_element[flow_type]['Step'].insert(0, {'Name': shared_flow_name})

    def get_all_flows(self, bundle_dir):
        """
        Parses apiproxy/proxies/default.xml and returns a list of all flow names.

        Args:
            bundle_dir (str): Path to the extracted bundle directory.

        Returns:
            list: A list of flow names present in the proxy.
        """
        proxy_xml_path = os.path.join(bundle_dir, "apiproxy", "proxies", "default.xml")
        flow_names = []

        try:
            with open(proxy_xml_path, "r") as f:
                xml_content = f.read()

            proxy_dict = xmltodict.parse(xml_content)

            # Extract flow names from the Flows section
            flows = proxy_dict.get('ProxyEndpoint', {}).get('Flows', {}).get('Flow', [])
            if isinstance(flows, dict):
                flows = [flows]
            for flow in flows:
                flow_names.append(flow['@name'])

            logging.info(f" Successfully retrieved flow names from: {proxy_xml_path} ")
            return flow_names

        except FileNotFoundError:
            logging.error(f" Error: Proxy XML file not found: {proxy_xml_path} ")
            return None
        except Exception as e:
            logging.exception(" An error occurred while retrieving flow names ")
            return None

    def validate_proxy(self, proxy_name, zip_file_path):
        """
        Validates the API proxy ZIP file by calling the Apigee API.

        Args:
            zip_file_path (str): The path to the API proxy ZIP file.

        Returns:
            dict: The JSON response from the Apigee API, or None if validation failed.
        """

        if not self.access_token:
            logging.error(" Access token is missing.  Cannot validate proxy. ")
            return None

        api_url = f"https://apigee.googleapis.com/v1/organizations/{self.org}/apis?name={proxy_name}&validate=true&action=validate"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }

        try:
            with open(zip_file_path, "rb") as f:
                response = requests.post(api_url, headers=headers, data=f)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_json = response.json()
            logging.info(" Proxy validation successful ")
            logging.debug(f"Validation response: {json.dumps(response_json, indent=2)}") # Log with indent for readability
            return response_json

        except requests.exceptions.HTTPError as e:
            logging.error(" Proxy validation failed (HTTP Error) ")
            logging.error(f"Status code: {e.response.status_code}")
            try:
              logging.error(f"Response body: {json.dumps(e.response.json(), indent=2)}") # Attempt to log the response body as JSON
            except json.JSONDecodeError:
              logging.error(f"Response body: {e.response.text}") # If JSON decode fails, log as text.
            return None
        except FileNotFoundError:
            logging.error(f" Error: ZIP file not found: {zip_file_path} ")
            return None
        except Exception as e:
            logging.exception(" An error occurred during proxy validation ")
            return None

    def deploy_proxy(self, proxy_name, env_name, revision):
        """
        Deploys the API proxy revision by calling the Apigee API.

        Args:
            proxy_name (str): The name of the API proxy.
            env_name (str): The apigee env name to deploy API proxy.
            revision (str): The revision of the API proxy to deploy.

        Returns:
            dict: The JSON response from the Apigee API, or None if validation failed.
        """

        if not self.access_token:
            logging.error(" Access token is missing.  Cannot validate proxy. ")
            return None

        api_url = f"https://apigee.googleapis.com/v1/organizations/{self.org}/environments/{env_name}/apis/{proxy_name}/revisions/{revision}/deployments?override=true"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(api_url, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_json = response.json()
            logging.info(" Proxy deploy successful ")
            logging.debug(f"deploy response: {json.dumps(response_json, indent=2)}") # Log with indent for readability
            return response_json

        except requests.exceptions.HTTPError as e:
            logging.error(" Proxy deploy failed (HTTP Error) ")
            logging.error(f"Status code: {e.response.status_code}")
            try:
              logging.error(f"Response body: {json.dumps(e.response.json(), indent=2)}") # Attempt to log the response body as JSON
            except json.JSONDecodeError:
              logging.error(f"Response body: {e.response.text}") # If JSON decode fails, log as text.
            return None
        except Exception as e:
            logging.exception(" An error occurred during proxy deployment ")
            return None

    def undeploy_proxy(self, proxy_name, env_name, revision):
        """
        Validates the API proxy ZIP file by calling the Apigee API.

        Args:
            proxy_name (str): The name of the API proxy.
            env_name (str): The apigee env name to deploy API proxy.
            revision (str): The revision of the API proxy to deploy.

        Returns:
            dict: The JSON response from the Apigee API, or None if validation failed.
        """

        if not self.access_token:
            logging.error(" Access token is missing.  Cannot validate proxy. ")
            return None

        api_url = f"https://apigee.googleapis.com/v1/organizations/{self.org}/environments/{env_name}/apis/{proxy_name}/revisions/{revision}/deployments"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.delete(api_url, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_json = response.json()
            logging.info(" Proxy undeploy successful ")
            logging.debug(f"undeploy response: {json.dumps(response_json, indent=2)}") # Log with indent for readability
            return response_json

        except requests.exceptions.HTTPError as e:
            logging.error(" Proxy undeploy failed (HTTP Error) ")
            logging.error(f"Status code: {e.response.status_code}")
            try:
              logging.error(f"Response body: {json.dumps(e.response.json(), indent=2)}") # Attempt to log the response body as JSON
            except json.JSONDecodeError:
              logging.error(f"Response body: {e.response.text}") # If JSON decode fails, log as text.
            return None
        except Exception as e:
            logging.exception(" An error occurred during proxy undeployment ")
            return None

    def upload_to_gcs(self, local_zip_path, bucket_name, gcs_destination_path):
        """
        Uploads the specified local ZIP file (API proxy bundle) to Google Cloud Storage.

        Relies on Application Default Credentials (ADC) for authentication.
        Ensure your environment is authenticated (e.g., `gcloud auth application-default login`
        or running in a GCP environment with appropriate service account permissions).

        Args:
            local_zip_path (str): The path to the local ZIP file to upload.
            bucket_name (str): The name of the target GCS bucket.
            gcs_destination_path (str): The desired path (object name) for the file
                                         within the GCS bucket (e.g., 'proxies/my-proxy-v1.zip').

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        try:
            # Instantiates a client. Handles authentication via ADC.
            storage_client = storage.Client()

            # Get the target bucket
            try:
                bucket = storage_client.get_bucket(bucket_name)
            except NotFound:
                logging.error(f" Error: GCS bucket '{bucket_name}' not found. ")
                return False

            # Create a blob object representing the destination path
            blob = bucket.blob(gcs_destination_path)

            # Upload the local file
            logging.info(f" Uploading '{local_zip_path}' to 'gs://{bucket_name}/{gcs_destination_path}'... ")
            blob.upload_from_filename(local_zip_path)

            logging.info(f" Successfully uploaded bundle to gs://{bucket_name}/{gcs_destination_path} ")
            return True

        except FileNotFoundError:
            logging.error(f" Error: Local file not found at '{local_zip_path}' ")
            return False
        except Exception as e:
            # Catching other potential exceptions from the google-cloud-storage library
            # or other unexpected issues.
            logging.exception(f" An error occurred while uploading to GCS: {e} ")
            return False

    def download_from_gcs(self, bucket_name, gcs_source_path, local_destination_path):
        """
        Downloads an object (e.g., an API proxy bundle ZIP) from Google Cloud Storage
        to a local file path.

        Relies on Application Default Credentials (ADC) for authentication.
        Ensure your environment is authenticated (e.g., `gcloud auth application-default login`
        or running in a GCP environment with appropriate service account permissions).

        Args:
            bucket_name (str): The name of the source GCS bucket.
            gcs_source_path (str): The path (object name) of the file within the GCS bucket
                                   to download (e.g., 'proxies/my-proxy-v1.zip').
            local_destination_path (str): The full path on the local filesystem where
                                          the downloaded file should be saved. Parent
                                          directories will be created if they don't exist.

        Returns:
            bool: True if the download was successful, False otherwise.
        """
        try:
            # Instantiates a client. Handles authentication via ADC.
            storage_client = storage.Client()

            # Get the source bucket
            try:
                bucket = storage_client.get_bucket(bucket_name)
            except NotFound:
                logging.error(f" Error: GCS bucket '{bucket_name}' not found. ")
                return False
            except Exception as e: # Catch other potential client/bucket errors
                 logging.exception(f" Error accessing GCS bucket '{bucket_name}': {e} ")
                 return False

            # Get the blob (object) to download
            blob = bucket.blob(gcs_source_path)

            # Check if the blob exists before attempting download
            if not blob.exists():
                logging.error(f" Error: Object '{gcs_source_path}' not found in bucket '{bucket_name}'. ")
                return False

            # Create local directories if they don't exist
            local_dir = os.path.dirname(local_destination_path)
            if local_dir: # Ensure local_dir is not empty (e.g., if dest is just a filename)
                os.makedirs(local_dir, exist_ok=True)

            # Download the blob to the specified local path
            logging.info(f" Downloading 'gs://{bucket_name}/{gcs_source_path}' to '{local_destination_path}'... ")
            blob.download_to_filename(local_destination_path, timeout=120) # Add a timeout

            logging.info(f" Successfully downloaded file to {local_destination_path} ")
            return True

        except NotFound:
             # This might be redundant if blob.exists() check is robust, but good failsafe
             logging.error(f" Error: GCS object not found during download: gs://{bucket_name}/{gcs_source_path} ")
             return False
        except Exception as e:
            # Catching other potential exceptions from the google-cloud-storage library
            # (e.g., permissions, network issues) or local filesystem errors.
            logging.exception(f" An error occurred while downloading from GCS: {e} ")
            # Clean up potentially partially downloaded file
            if os.path.exists(local_destination_path):
                 try:
                     os.remove(local_destination_path)
                     logging.info(f" Removed potentially incomplete file: {local_destination_path}")
                 except OSError as rm_err:
                     logging.error(f" Error removing incomplete file {local_destination_path}: {rm_err}")
            return False


def flow_callout_template(fc_name, sf_name) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<FlowCallout continueOnError="false" enabled="true" name="{fc_name}">
<DisplayName>{fc_name}</DisplayName>
<Parameters/>
<SharedFlowBundle>{sf_name}</SharedFlowBundle>
</FlowCallout>
"""

def main():

    parser = argparse.ArgumentParser(description="Create and modify Apigee API proxies.")
    parser.add_argument("--apigee_org", required=True, help="Apigee organization")
    parser.add_argument("--access_token", required=True, help="GCP access token")
    parser.add_argument("--api_name", required=True, help="API proxy name")
    parser.add_argument("--api_base_path", required=True, help="API base path")
    parser.add_argument("--target_url", required=True, help="OAS Target URL")
    parser.add_argument("--oas_file_location", required=True, help="OAS file location")
    parser.add_argument("--oas_file_name", required=True, help="OAS file name")
    parser.add_argument("--override_flow_names", default="", help="Comma separated list of flow operations to override")
    parser.add_argument("--base_sf_pre",required=True, help="Request Shared flow to override with")
    parser.add_argument("--base_sf_post",required=True, help="Response Shared flow to override with")
    parser.add_argument("--override_sf_pre",default="", help="Request Shared flow to override with")
    parser.add_argument("--override_sf_post",default="", help="Response Shared flow to override with")
    parser.add_argument('--enable_gcs_persistence', action='store_true', dest='use_gcs',
                    default=False,
                    help='Explicitly enable GCS persistence (default: disabled)')
    parser.add_argument('--gcs_pull', action='store_true', dest='gcs_pull',
                    default=False,
                    help='Explicitly enable GCS persistence (default: disabled)')
    parser.add_argument("--gcs_bucket",default="", help="Response Shared flow to override with")
    parser.add_argument("--gcs_object_prefix",default="", help="Response Shared flow to override with")
    parser.add_argument('--undeploy_revision', action='store_true', dest='undeploy_revision',
                    default=False,
                    help='Explicitly enable GCS persistence (default: disabled)')
    parser.add_argument('--deploy_revision', action='store_true', dest='deploy_revision',
                    default=False,
                    help='Explicitly enable GCS persistence (default: disabled)')
    parser.add_argument("--apigee_env", help="Apigee Env Name")
    parser.add_argument("--api_revision", help="Apigee Proxy Revision")

    args = parser.parse_args()
    apigee_org = args.apigee_org
    target_url = args.target_url
    api_name = args.api_name
    api_base_path = args.api_base_path
    oas_file_location= args.oas_file_location
    oas_file_name=args.oas_file_name

    override_flow = args.override_flow_names.split(',') if len(args.override_flow_names) > 0 else []

    if len(override_flow) > 0 and (len(args.override_sf_pre) == 0 and len(args.override_sf_post)):
        logging.error("Please provide --override_sf_name since you have provided --override_flow_names")
        sys.exit(1)
    base_sf_pre = args.base_sf_pre
    base_sf_post = args.base_sf_post
    override_sf_pre = args.override_sf_pre
    override_sf_post = args.override_sf_post

    api1 = ApigeeCliRunner(
        args.access_token,
        basepath=api_base_path,
        name=api_name,
        oas_base_folderpath=oas_file_location,
        oas_name=oas_file_name,
        org=apigee_org,
        target_url=target_url,
        default_token=False,
        import_api=False, # Set to False,
        validate=True,
        skip_policy=True,
    )

    if args.gcs_pull:
        if api1.download_from_gcs(
            args.gcs_bucket,
            f"{args.gcs_object_prefix}/{api_name}.zip",
            f"{api_name}.zip"
        ):
            logging.info(f"Bundle {api_name}.zip fetched from GCS.")
        else:
            logging.error(f"Bundle {api_name}.zip fetch from GCS failed.")
            sys.exit(1)
        return

    if args.deploy_revision:
        if api1.deploy_proxy(
            api_name,
            args.apigee_env,
            args.api_revision
        ) is not None:
            logging.info(f"Proxy {api_name} with revison {args.api_revision} has been deployed")
        else:
            logging.error(f"Deploy of proxy {api_name} with revison {args.api_revision} failed")
            sys.exit(1)
        return

    if args.undeploy_revision:
        if api1.undeploy_proxy(
            api_name,
            args.apigee_env,
            args.api_revision
        ) is not None:
            logging.info(f"Proxy {api_name} with revison {args.api_revision} has been undeployed")
        else:
            logging.error(f"Undeploy of proxy {api_name} with revison {args.api_revision} failed")
            sys.exit(1)
        return

    if api1.create_bundle():
        bundle_path = f"./{api_name}.zip"

        if bundle_path:
            api1.unzip_bundle(bundle_path)

            proxy_path = api_name
            
            # Inject Base Flow Callout Request Flow
            policy1_name="FC-base-request-process"
            policy1=flow_callout_template(
                policy1_name,
                base_sf_pre
            )
            api1.inject_policy(
                proxy_path,
                policy1_name,
                policy1
            )

            # Inject Base Flow Callout Response Flow
            policy2_name="FC-base-response-process"
            policy2=flow_callout_template(
                policy2_name,
                base_sf_post
            )
            api1.inject_policy(
                proxy_path,
                policy2_name,
                policy2
            )

            all_flows = api1.get_all_flows(proxy_path)
            # logging.info(f"Flows list:  {all_flows}")

            if len(override_flow) > 0:
                # Inject Override Flow Callout Request Flow
                policy3_name="FC-override-request-process"
                policy3=flow_callout_template(
                    policy3_name,
                    override_sf_pre
                )
                api1.inject_policy(
                    proxy_path,
                    policy3_name,
                    policy3
                )

                # Inject Override Flow Callout Response Flow
                policy4_name="FC-override-response-process"
                policy4=flow_callout_template(
                    policy4_name,
                    override_sf_post
                )
                api1.inject_policy(
                    proxy_path,
                    policy4_name,
                    policy4
                )
                for flow_name in all_flows:
                    if flow_name in override_flow:
                        api1.inject_shared_flow_to_flows(
                            proxy_path,
                            policy3_name,
                            [flow_name],
                            flow_type="Request"
                        )
                        api1.inject_shared_flow_to_flows(
                            proxy_path,
                            policy4_name,
                            [flow_name],
                            flow_type="Response"
                        )
                    else:
                        api1.inject_shared_flow_to_flows(
                            proxy_path,
                            policy1_name,
                            [flow_name],
                            flow_type="Request"
                        )

                        api1.inject_shared_flow_to_flows(
                            proxy_path,
                            policy2_name,
                            [flow_name],
                            flow_type="Response"
                        )
            else:
                api1.inject_shared_flow_to_flows(
                            proxy_path,
                            policy1_name,
                            ['PreFlow'],
                            flow_type="Request"
                        )

                api1.inject_shared_flow_to_flows(
                    proxy_path,
                    policy2_name,
                    ['PostFlow'],
                    flow_type="Response"
                )

            api1.zip_bundle(
                proxy_path,
                f"{api_name}.zip"
            )

            if api1.validate_proxy(api_name, f"{api_name}.zip") is not None:
                logging.info("Bundle validated successful.")
                if args.use_gcs:
                    logging.info("Uploading bundle to GCS.")
                    if api1.upload_to_gcs(f"{api_name}.zip",
                                       args.gcs_bucket,
                                       f"{args.gcs_object_prefix}/{api_name}.zip"):
                        logging.info("Bundle uploaded to GCS.")
                    else:
                        logging.error("Bundle upload to GCS failed.")
        else:
            logging.error("Bundle creation failed, cannot unzip.")
            sys.exit(1)
    else:
        logging.error("Bundle creation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()