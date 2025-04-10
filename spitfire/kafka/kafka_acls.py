#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import json
import argparse
from datetime import timezone # Needed for expiry calculation
import time # Needed for expiry calculation

# --- GCP Specific Imports ---
try:
    import google.auth
    import google.auth.transport.requests
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    print("ERROR: Missing 'google-auth' library. Please install it: pip install google-auth")
    sys.exit(1)
# --- End GCP Specific Imports ---

from confluent_kafka import KafkaException, KafkaError
from confluent_kafka.admin import (AdminClient, AclBinding, AclBindingFilter,
                                   ResourceType, ResourcePatternType,
                                   AclOperation, AclPermissionType)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- OAUTHBEARER Token Refresh Callback for GCP ---
def gcp_oauth_token_provider(oauthbearer_config):
    """
    Called by confluent-kafka-python to retrieve an OAuth token using
    Google Application Default Credentials (ADC).
    """
    try:
        # Fetch credentials using ADC strategy
        # Scopes might be needed depending on the Kafka service, but often default scopes are sufficient
        # credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform']) # Example scope
        credentials, project = google.auth.default()

        # Create an authenticated session to refresh the token
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req) # Get/refresh the access token

        token = credentials.token
        expiry_timestamp_ms = int(credentials.expiry.replace(tzinfo=timezone.utc).timestamp() * 1000) # Must be UTC epoch ms
        principal = credentials.service_account_email if hasattr(credentials, 'service_account_email') else "gcp-adc-user" # Principal associated with the token

        logger.debug(f"Successfully obtained GCP OAuth token for principal '{principal}', expires at {credentials.expiry}")
        # Note: confluent_kafka takes expiry_timestamp_ms and principal, but they might not be used
        # by all brokers. The token itself is the critical part.
        return token, expiry_timestamp_ms

    except DefaultCredentialsError as e:
        logger.error(f"GCP Default Credentials Error: {e}. Ensure ADC is configured "
                     "(run 'gcloud auth application-default login', use a service account, "
                     "or set GOOGLE_APPLICATION_CREDENTIALS).")
        # Signal failure to librdkafka
        raise KafkaException(KafkaError._AUTHENTICATION, f"GCP ADC Error: {e}")
    except Exception as e:
        logger.error(f"Failed to get GCP OAuth token: {e}")
        # Signal failure to librdkafka
        raise KafkaException(KafkaError._AUTHENTICATION, f"GCP Token Error: {e}")

# --- End OAUTHBEARER Callback ---


# Helper function (no changes needed)
def parse_nullable_string(s):
    if s is None or s == "None":
        return None
    else:
        return str(s)

# KafkaACLManager Class (no significant changes needed inside the class methods)
class KafkaACLManager:
    def __init__(self, admin_config):
        if not isinstance(admin_config, dict) or 'bootstrap.servers' not in admin_config:
            raise ValueError("admin_config must be a dict containing 'bootstrap.servers'")

        # --- OAUTHBEARER Integration Point ---
        # Check if OAUTHBEARER is configured and set the callback
        if admin_config.get('sasl.mechanism') == 'OAUTHBEARER':
            # The callback function itself is assigned here.
            # The 'sasl.oauthbearer.config' is passed *to* the callback if set,
            # but we don't need it for the GCP ADC approach.
            admin_config['oauth_cb'] = gcp_oauth_token_provider
            logger.info("GCP OAUTHBEARER token provider callback configured.")
            # Remove incompatible Java config keys if they were accidentally passed
            admin_config.pop('sasl.login.callback.handler.class', None)
            admin_config.pop('sasl.jaas.config', None)
        # --- End OAUTHBEARER Integration ---

        try:
            self.admin_client = AdminClient(admin_config)
            logger.info(f"AdminClient created for brokers: {admin_config['bootstrap.servers']}")
        except Exception as e:
            logger.error(f"Failed to create AdminClient: {e}")
            raise

    def _to_enum(self, enum_type, value_str, allow_any=False):
        # (Content unchanged from previous version)
        if allow_any and value_str is None: return enum_type.ANY
        if allow_any and isinstance(value_str, str) and value_str.upper() == 'ANY': return enum_type.ANY
        if not isinstance(value_str, str):
             if isinstance(value_str, enum_type): return value_str
             raise ValueError(f"Invalid input type for {enum_type.__name__}: {type(value_str)}. Expected string.")
        try:
            return enum_type[value_str.upper()]
        except KeyError:
            valid_values = [e.name for e in enum_type]
            raise ValueError(f"Invalid value '{value_str}' for {enum_type.__name__}. Valid values: {valid_values}{' (or ANY)' if allow_any else ''}")

    def create_acl(self, resource_type_str, resource_name, resource_pattern_type_str,
                   principal, host, operation_str, permission_type_str, request_timeout=15.0):
        # (Content largely unchanged)
        acl_binding = None
        try:
            res_type = self._to_enum(ResourceType, resource_type_str, allow_any=False)
            res_pattern_type = self._to_enum(ResourcePatternType, resource_pattern_type_str, allow_any=False)
            op = self._to_enum(AclOperation, operation_str, allow_any=False)
            perm_type = self._to_enum(AclPermissionType, permission_type_str, allow_any=False)
            res_name = parse_nullable_string(resource_name)
            if res_type != ResourceType.CLUSTER and res_name is None: raise ValueError("resource_name cannot be None/null for non-CLUSTER resource types")
            if res_type == ResourceType.CLUSTER and res_name is not None: logger.warning(f"resource_name '{res_name}' provided for CLUSTER resource type will be ignored."); res_name = None
            if principal is None or host is None: raise ValueError("Principal and host cannot be None/null for ACL creation.")
            principal = str(principal); host = str(host)
            acl_binding = AclBinding(res_type, res_name, res_pattern_type, principal, host, op, perm_type)
            logger.info(f"Attempting to create ACL: {acl_binding}")
            fs = self.admin_client.create_acls([acl_binding], request_timeout=request_timeout)
            future = fs[acl_binding]; future.result(); logger.info(f"Successfully requested creation of ACL: {acl_binding}")
            return True
        # (Error handling unchanged)
        except KeyError as e: logger.error(f"Invalid enum value provided for create: {e}"); return False
        except ValueError as e: logger.error(f"Input validation error for create: {e}"); return False
        except KafkaException as e: log_msg = f"Failed to create ACL"; log_msg += f" {acl_binding}" if acl_binding else ""; log_msg += f": {e}"; logger.error(log_msg); return False
        except Exception as e: logger.error(f"An unexpected error occurred during ACL creation: {e}"); return False


    def describe_acls(self, resource_type_str=None, resource_name=None, resource_pattern_type_str=None,
                      principal=None, host=None, operation_str=None, permission_type_str=None,
                      request_timeout=15.0):
        # (Content unchanged)
        acl_filter = None
        try:
            res_type = self._to_enum(ResourceType, resource_type_str, allow_any=True)
            res_pattern_type = self._to_enum(ResourcePatternType, resource_pattern_type_str, allow_any=True)
            op = self._to_enum(AclOperation, operation_str, allow_any=True)
            perm_type = self._to_enum(AclPermissionType, permission_type_str, allow_any=True)
            res_name = parse_nullable_string(resource_name); filt_principal = parse_nullable_string(principal); filt_host = parse_nullable_string(host)
            acl_filter = AclBindingFilter(res_type, res_name, res_pattern_type, filt_principal, filt_host, op, perm_type)
            logger.info(f"Attempting to describe ACLs matching filter: {acl_filter}")
            future = self.admin_client.describe_acls(acl_filter, request_timeout=request_timeout)
            results = future.result(); logger.info(f"Found {len(results)} ACL(s) matching filter.")
            return results
        # (Error handling unchanged)
        except KeyError as e: logger.error(f"Invalid enum value provided for describe filter: {e}"); return None
        except ValueError as e: logger.error(f"Input validation error for describe filter: {e}"); return None
        except KafkaException as e: log_msg = f"Failed to describe ACLs"; log_msg += f" matching filter {acl_filter}" if acl_filter else ""; log_msg += f": {e}"; logger.error(log_msg); return None
        except Exception as e: logger.error(f"An unexpected error occurred during ACL description: {e}"); return None


    def delete_acl(self, resource_type_str=None, resource_name=None, resource_pattern_type_str=None,
                   principal=None, host=None, operation_str=None, permission_type_str=None,
                   request_timeout=15.0):
        # (Content unchanged)
        acl_filter = None
        try:
            res_type = self._to_enum(ResourceType, resource_type_str, allow_any=True)
            res_pattern_type = self._to_enum(ResourcePatternType, resource_pattern_type_str, allow_any=True)
            op = self._to_enum(AclOperation, operation_str, allow_any=True)
            perm_type = self._to_enum(AclPermissionType, permission_type_str, allow_any=True)
            res_name = parse_nullable_string(resource_name); filt_principal = parse_nullable_string(principal); filt_host = parse_nullable_string(host)
            acl_filter = AclBindingFilter(res_type, res_name, res_pattern_type, filt_principal, filt_host, op, perm_type)
            logger.info(f"Attempting to delete ACLs matching filter: {acl_filter}")
            fs = self.admin_client.delete_acls([acl_filter], request_timeout=request_timeout)
            future = fs[acl_filter]; results_wrapper = future.result()
            filter_result = results_wrapper[0]
            if filter_result.exception is not None: raise filter_result.exception
            deleted_bindings = filter_result.bindings
            logger.info(f"Successfully requested deletion, {len(deleted_bindings)} ACL(s) matched filter.")
            return deleted_bindings
        # (Error handling unchanged)
        except KeyError as e: logger.error(f"Invalid enum value provided for delete filter: {e}"); return None
        except ValueError as e: logger.error(f"Input validation error for delete filter: {e}"); return None
        except KafkaException as e: log_msg = f"Failed to delete ACLs"; log_msg += f" matching filter {acl_filter}" if acl_filter else ""; log_msg += f": {e}"; logger.error(log_msg); return None
        except Exception as e: logger.error(f"An unexpected error occurred during ACL deletion: {e}"); return None


def process_acls_from_file(acl_manager, file_path):
    # (Content unchanged from previous version)
    try:
        with open(file_path, 'r') as f: acl_definitions = json.load(f)
    except FileNotFoundError: logger.error(f"Error: JSON file not found at '{file_path}'"); return False
    except json.JSONDecodeError as e: logger.error(f"Error: Could not decode JSON file '{file_path}': {e}"); return False
    except Exception as e: logger.error(f"Error reading file '{file_path}': {e}"); return False
    if not isinstance(acl_definitions, list): logger.error(f"Error: JSON content in '{file_path}' must be a list of ACL objects."); return False
    logger.info(f"Processing {len(acl_definitions)} ACL definitions from '{file_path}'...")
    overall_success = True
    for i, acl_data in enumerate(acl_definitions):
        if not isinstance(acl_data, dict): logger.warning(f"Skipping item #{i+1}: Not a valid dictionary object."); overall_success = False; continue
        action = acl_data.get('action'); description = acl_data.get('description', f'ACL definition #{i+1}')
        logger.info(f"\n--- Processing Action: {action} ({description}) ---")
        resource_type = acl_data.get('resource_type'); resource_name = acl_data.get('resource_name'); resource_pattern_type = acl_data.get('resource_pattern_type')
        principal = acl_data.get('principal'); host = acl_data.get('host'); operation = acl_data.get('operation'); permission_type = acl_data.get('permission_type')
        success = False
        if action == "CREATE":
            required_create = ['resource_type', 'resource_pattern_type', 'principal', 'host', 'operation', 'permission_type']
            if resource_type != 'CLUSTER' and 'resource_name' not in acl_data: required_create.append('resource_name')
            missing = [field for field in required_create if field not in acl_data or acl_data.get(field) is None]
            if missing: logger.error(f"Skipping CREATE: Missing required fields: {missing} in definition: {acl_data}"); overall_success = False; continue
            success = acl_manager.create_acl(resource_type, resource_name, resource_pattern_type, principal, host, operation, permission_type)
        elif action == "DELETE":
             if not resource_pattern_type: logger.error(f"Skipping DELETE: 'resource_pattern_type' is required for delete filter in definition: {acl_data}"); overall_success = False; continue
             deleted_bindings = acl_manager.delete_acl(resource_type, resource_name, resource_pattern_type, principal, host, operation, permission_type)
             success = deleted_bindings is not None
             if success: print(f"  Deletion request sent. Matched {len(deleted_bindings)} ACLs for deletion.")
        elif action == "DESCRIBE":
            described_acls = acl_manager.describe_acls(resource_type, resource_name, resource_pattern_type, principal, host, operation, permission_type)
            success = described_acls is not None
            if success:
                 if described_acls: print(f"  Found {len(described_acls)} matching ACL(s):"); [print(f"    - {acl}") for acl in described_acls]
                 else: print("  No ACLs found matching the filter.")
        else: logger.warning(f"Skipping item #{i+1}: Unknown or missing action '{action}'"); overall_success = False; continue
        if not success: logger.warning(f"Action '{action}' for '{description}' may have failed or encountered an error."); overall_success = False
    return overall_success


# --- Main Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manage Kafka ACLs from JSON with OAUTHBEARER support for GCP.")
    parser.add_argument("--bootstrap_servers", help="Kafka bootstrap servers (e.g., 'kafka.example.com:9093')")
    parser.add_argument("--acl_file", help="Path to the JSON file containing ACL definitions.")
    parser.add_argument("-X", "--config", action='append', default=[],
                        help="Additional client configuration properties ('prop=val'). "
                             "Use this for SSL settings (e.g., ssl.ca.location) or other librdkafka options. "
                             "Do NOT use for OAUTHBEARER-specific Java properties.")

    args = parser.parse_args()

    # --- Core OAUTHBEARER Configuration ---
    admin_conf = {
        'bootstrap.servers': args.bootstrap_servers,
        'security.protocol': 'SASL_SSL', # Required for OAUTHBEARER typically
        'sasl.mechanism': 'OAUTHBEARER',
        # 'debug': 'security,broker,protocol' # Optional: Enable verbose debugging if needed
    }
    # --- End Core OAUTHBEARER Configuration ---

    # Parse and add additional configuration properties (-X args)
    # Useful for SSL CA location, timeouts, etc.
    for conf_item in args.config:
        try:
            key, value = conf_item.split('=', 1)
            conf_key = key.strip()
            conf_value = value.strip()
            # Avoid overriding core OAUTHBEARER settings unless explicitly intended
            if conf_key in ['security.protocol', 'sasl.mechanism', 'oauth_cb']:
                 logger.warning(f"Attempting to override core auth setting '{conf_key}' via -X. Ensure this is intended.")
            # Reject incompatible Java settings
            if conf_key in ['sasl.login.callback.handler.class', 'sasl.jaas.config']:
                 logger.error(f"Ignoring incompatible Java configuration key '{conf_key}' from -X arguments. Use the Python OAUTHBEARER callback.")
                 continue # Skip adding this key

            admin_conf[conf_key] = conf_value
            logger.info(f"Adding config from -X: {conf_key} = {conf_value}")
        except ValueError:
            logger.error(f"Ignoring invalid configuration item: '{conf_item}'. Expected format 'prop=val'.")
            sys.exit(1)

    # Example SSL config using -X:
    # python kafka_acl_tool.py <servers> acls.json -X ssl.ca.location=./ca.pem

    try:
        # The KafkaACLManager __init__ will now automatically set the oauth_cb
        acl_manager = KafkaACLManager(admin_conf)
    except KafkaException as e:
        logger.error(f"KafkaException during AdminClient initialization: {e}")
        if e.args[0].code() == KafkaError._AUTHENTICATION:
             logger.error("Authentication failed. Check OAUTHBEARER setup, ADC, and broker configuration.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Exiting due to AdminClient initialization failure: {e}")
        sys.exit(1)

    # Process ACLs defined in the JSON file
    operation_status = process_acls_from_file(acl_manager, args.acl_file)

    if operation_status:
        logger.info("\n--- Finished processing ACL definitions from JSON file. Check logs for details. ---")
        sys.exit(0)
    else:
        logger.error("\n--- Finished processing ACL definitions from JSON file, but some operations failed or were skipped. Check logs for details. ---")
        sys.exit(1)