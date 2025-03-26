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
            basepath="/testoas",
            name="testoas",
            oas_base_folderpath=".",
            oas_name="httpbin.yaml",
            org="test-org",
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
        self.default_token = default_token
        self.import_api = import_api
        self.validate = validate
        self.skip_policy = skip_policy
        self.access_token = None


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

    def get_access_token(self):
        """Retrieves an access token using gcloud auth print-access-token."""
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                check=True,
                capture_output=True,
                text=True
            )
            self.access_token = result.stdout.strip()
            logging.info(" Successfully retrieved access token ")
            return self.access_token
        except subprocess.CalledProcessError as e:
            logging.error(" Failed to retrieve access token using gcloud ")
            logging.error(f"STDOUT: {e.stdout}")
            logging.error(f"STDERR: {e.stderr}")
            return None
        except FileNotFoundError:
            logging.error(" gcloud command not found. Ensure Google Cloud SDK is installed and in your PATH. ")
            return None
        except Exception as e:
            logging.exception(" An unexpected error occurred while retrieving access token ")
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
            for flow in proxy_dict['ProxyEndpoint']['Flows']['Flow']:
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
            for flow in proxy_dict['ProxyEndpoint']['Flows']['Flow']:
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
          self.access_token = self.get_access_token() # Get the access token

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

def main():

    parser = argparse.ArgumentParser(description="Create and modify Apigee API proxies.")
    parser.add_argument("--apigee_org", required=True, help="Apigee organization")
    parser.add_argument("--api_name", required=True, help="API proxy name")
    parser.add_argument("--api_base_path", required=True, help="API base path")
    parser.add_argument("--oas_file_location", required=True, help="OAS file location")
    parser.add_argument("--oas_file_name", required=True, help="OAS file name")
    parser.add_argument("--override_flow_names", default="", help="Comma separated list of flow operations to override")
    parser.add_argument("--override_sf_name",default="", help="Shared flow to override with")

    args = parser.parse_args()
    apigee_org = args.apigee_org
    api_name = args.api_name
    api_base_path = args.api_base_path
    oas_file_location= args.oas_file_location
    oas_file_name=args.oas_file_name

    override_flow = args.override_flow_names.split(',') if len(args.override_flow_names) > 0 else []

    if len(override_flow) > 0 and len(args.override_sf_name) == 0:
        logging.error("Please provide --override_sf_name since you have provided --override_flow_names")
        sys.exit(1)
    override_sf_name = args.override_sf_name

    api1 = ApigeeCliRunner(
        basepath=api_base_path,
        name=api_name,
        oas_base_folderpath=oas_file_location,
        oas_name=oas_file_name,
        org=apigee_org,
        default_token=False,
        import_api=False, # Set to False,
        validate=True,
        skip_policy=True,
    )

    if api1.create_bundle():
        bundle_path = f"./{api_name}.zip"

        if bundle_path:
            api1.unzip_bundle(bundle_path)

            proxy_path = api_name

            policy1_name="FC-Base-Pre"
            policy1="""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<FlowCallout continueOnError="false" enabled="true" name="FC-Base-Pre">
<DisplayName>FC-Base-Pre</DisplayName>
<Parameters/>
<SharedFlowBundle>SF-spitfire-pre</SharedFlowBundle>
</FlowCallout>
"""
            api1.inject_policy(
                proxy_path,
                policy1_name,
                policy1
            )

            policy2_name="FC-Base-Post"
            policy2="""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<FlowCallout continueOnError="false" enabled="true" name="FC-Base-Post">
<DisplayName>FC-Base-Post</DisplayName>
<Parameters/>
<SharedFlowBundle>SF-spitfire-post</SharedFlowBundle>
</FlowCallout>
"""
            api1.inject_policy(
                proxy_path,
                policy2_name,
                policy2
            )

            all_flows = api1.get_all_flows(proxy_path)
            # logging.info(f"Flows list:  {all_flows}")

            if len(override_flow) > 0:
                policy3_name="FC-override"
                policy3=f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<FlowCallout continueOnError="false" enabled="true" name="FC-override">
<DisplayName>FC-override</DisplayName>
<Parameters/>
<SharedFlowBundle>{override_sf_name}</SharedFlowBundle>
</FlowCallout>
"""
                api1.inject_policy(
                    proxy_path,
                    policy3_name,
                    policy3
                )
                override_policy = "FC-override"
                for flow_name in all_flows:
                    if flow_name in override_flow:
                        api1.inject_shared_flow_to_flows(
                            proxy_path,
                            override_policy,
                            [flow_name],
                            flow_type="Request"
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

            api1.validate_proxy(api_name, f"{api_name}.zip")
            sys.exit(1)
        else:
            logging.error("Bundle creation failed, cannot unzip.")
    else:
        logging.error("Bundle creation failed.")
        sys.exit(1)
        


if __name__ == "__main__":
    main()