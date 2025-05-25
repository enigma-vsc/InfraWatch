import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient

def load_env(env_file_path: str):
    if not os.path.exists(env_file_path):
        raise FileNotFoundError(f".env file not found at: {env_file_path}")
    load_dotenv(dotenv_path=env_file_path)

def get_resource_client() -> ResourceManagementClient:
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        raise ValueError("AZURE_SUBSCRIPTION_ID is not set in environment.")
    
    credential = DefaultAzureCredential()
    return ResourceManagementClient(credential, subscription_id)

def get_compute_client() -> ComputeManagementClient:
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        raise ValueError("AZURE_SUBSCRIPTION_ID is not set in environment.")
    credential = DefaultAzureCredential()
    return ComputeManagementClient(credential, subscription_id)

def list_resource_groups(client: ResourceManagementClient):
    print("Listing Resource Groups:")
    print("====================================")
    for rg in client.resource_groups.list():
        print(f"- {rg.name}")

def list_virtual_machines(client: ComputeManagementClient):
    print("Listing Virtual Machines:")
    print("====================================")
    vms = client.virtual_machines.list_all()
    for vm in vms:
        print(vm.name)


def main():
    env_file_path = os.getenv("ENV_FILE_PATH", ".env")
    load_env(env_file_path)
    print(f"Using environment file: {env_file_path}")
    client = get_resource_client()
    compute_client = get_compute_client()
    list_resource_groups(client)
    list_virtual_machines(compute_client)

if __name__ == "__main__":
    main()