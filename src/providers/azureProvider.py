#!/usr/bin/env python3
"""
InfraWatch - Azure VM Instance Listing
Basic Azure SDK connection and VM discovery
"""

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import ClientAuthenticationError
from rich.console import Console
from rich.table import Table
from rich import print
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
import sys
import os


class AzureProvider:
    """Azure connection and VM operations"""
    
    def __init__(self, subscription_id=None):
        self.console = Console()
        self.subscription_id = subscription_id or self.get_subscription_id()
        self.credential = None
        self.compute_client = None
        self.network_client = None
        
    def authenticate(self):
        """Initialize Azure authentication"""
        try:
            # Try Azure CLI credentials first, then default credential chain
            try:
                self.credential = AzureCliCredential()
                # Test the credential
                token = self.credential.get_token("https://management.azure.com/.default")
            except:
                self.credential = DefaultAzureCredential()
                
            return True
            
        except ClientAuthenticationError:
            self.console.print("[red]❌ Azure authentication failed![/red]")
            self.console.print("Make sure you have:")
            self.console.print("• Azure CLI installed and logged in: [cyan]az login[/cyan]")
            self.console.print("• Or proper environment variables set")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Error authenticating with Azure: {e}[/red]")
            return False
    
    def get_subscription_id(self):
        """Get subscription ID if not provided"""
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not self.subscription_id:
            raise ValueError("❌ Error: AZURE_SUBSCRIPTION_ID is not defined. Please set it in your environment variables.")
        return self.subscription_id

    
    def initialize_clients(self):
        """Initialize Azure management clients"""
        if not self.authenticate():
            return False
            
        try:
            self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            self.network_client = NetworkManagementClient(self.credential, self.subscription_id)
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Error initializing Azure clients: {e}[/red]")
            return False
    

def main():
    """Main entry point"""
    env_path = find_dotenv()
    #print(f"Found .env file at: {env_path}")
    if not env_path:
        print("No .env file found. Please create one with your Azure credentials.")
        sys.exit(1)
    # Load environment variables
    load_dotenv(env_path)
    # print(os.getenv("AZURE_SUBSCRIPTION_ID"))
    # print('Client ID',os.getenv('AZURE_CLIENT_ID'))
    console = Console()
    # Print header
    console.print("\n🔍 [bold blue]InfraWatch[/bold blue] - Azure VM Monitor")
    console.print("=" * 50)
    
    # Initialize Azure provider
    provider = AzureProvider(subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"))  # Will auto-detect subscription
    console.print("🔄 Fetching Azure VMs...")


if __name__ == "__main__":
    main()