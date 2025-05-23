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
    
    def get_vm_public_ip(self, vm, resource_group):
        """Get public IP for a VM if it exists"""
        try:
            # Get network interfaces for the VM
            for nic_ref in vm.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                nic = self.network_client.network_interfaces.get(resource_group, nic_name)
                
                # Check each IP configuration
                for ip_config in nic.ip_configurations:
                    if ip_config.public_ip_address:
                        pip_name = ip_config.public_ip_address.id.split('/')[-1]
                        public_ip = self.network_client.public_ip_addresses.get(resource_group, pip_name)
                        return public_ip.ip_address
            return "N/A"
        except:
            return "N/A"
    
    def list_vms(self):
        """Get all VMs across all resource groups"""
        if not self.initialize_clients():
            return []
            
        try:
            vms = []
            
            # Get all VMs in subscription
            all_vms = self.compute_client.virtual_machines.list_all()
            
            for vm in all_vms:
                # Extract resource group from VM ID
                resource_group = vm.id.split('/')[4]
                
                # Get VM instance view for power state
                try:
                    instance_view = self.compute_client.virtual_machines.instance_view(resource_group, vm.name)
                    power_state = "unknown"
                    for status in instance_view.statuses:
                        if status.code.startswith('PowerState/'):
                            power_state = status.code.split('/')[-1]
                            break
                except:
                    power_state = "unknown"
                
                # Get public IP
                public_ip = self.get_vm_public_ip(vm, resource_group)
                
                # Get private IP
                private_ip = "N/A"
                try:
                    if vm.network_profile.network_interfaces:
                        nic_ref = vm.network_profile.network_interfaces[0]
                        nic_name = nic_ref.id.split('/')[-1]
                        nic = self.network_client.network_interfaces.get(resource_group, nic_name)
                        if nic.ip_configurations:
                            private_ip = nic.ip_configurations[0].private_ip_address or "N/A"
                except:
                    pass
                
                vm_data = {
                    'name': vm.name,
                    'resource_group': resource_group,
                    'size': vm.hardware_profile.vm_size,
                    'location': vm.location,
                    'power_state': power_state,
                    'os_type': vm.storage_profile.os_disk.os_type.value if vm.storage_profile.os_disk.os_type else 'Unknown',
                    'public_ip': public_ip,
                    'private_ip': private_ip,
                    'tags': vm.tags or {},
                    'provisioning_state': vm.provisioning_state
                }
                
                # Check if tagged
                vm_data['tagged'] = len(vm_data['tags']) > 0
                
                vms.append(vm_data)
            
            return vms
            
        except Exception as e:
            self.console.print(f"[red]❌ Error fetching Azure VMs: {e}[/red]")
            return []

def display_vms_table(vms):
    """Display VMs in a Rich table"""
    console = Console()
    
    if not vms:
        console.print("[yellow]⚠️  No Azure VMs found in this subscription[/yellow]")
        return
    
    # Create table
    table = Table(title=f"🔍 InfraWatch - Azure VMs ({len(vms)} found)")
    
    # Add columns
    table.add_column("VM Name", style="cyan")
    table.add_column("Resource Group", style="blue")
    table.add_column("Size", style="green")
    table.add_column("Power State", style="magenta")
    table.add_column("OS Type", style="yellow")
    table.add_column("Public IP", style="white")
    table.add_column("Tagged", style="yellow")
    table.add_column("Location", style="dim")
    
    # Add rows
    for vm in vms:
        # Color-code power state
        power_state = vm['power_state']
        if power_state == 'running':
            state_display = f"[green]{power_state}[/green]"
        elif power_state in ['stopped', 'deallocated']:
            state_display = f"[red]{power_state}[/red]"
        else:
            state_display = f"[yellow]{power_state}[/yellow]"
        
        # Tagged status
        tagged_display = "✅" if vm['tagged'] else "[red]❌[/red]"
        
        table.add_row(
            vm['name'],
            vm['resource_group'],
            vm['size'],
            state_display,
            vm['os_type'],
            vm['public_ip'],
            tagged_display,
            vm['location']
        )
    
    console.print(table)
    
    # Summary stats
    running_count = sum(1 for vm in vms if vm['power_state'] == 'running')
    untagged_count = sum(1 for vm in vms if not vm['tagged'])
    
    console.print(f"\n📊 Summary:")
    console.print(f"• Total VMs: {len(vms)}")
    console.print(f"• Running: [green]{running_count}[/green]")
    console.print(f"• Untagged: [red]{untagged_count}[/red]")
    
    # Resource group breakdown
    rg_counts = {}
    for vm in vms:
        rg = vm['resource_group']
        rg_counts[rg] = rg_counts.get(rg, 0) + 1
    
    console.print(f"• Resource Groups: {len(rg_counts)}")
    for rg, count in sorted(rg_counts.items()):
        console.print(f"  - {rg}: {count} VM(s)")

def main():
    """Main entry point"""
    env_path = find_dotenv()
    print(f"Found .env file at: {env_path}")
    if not env_path:
        print("No .env file found. Please create one with your Azure credentials.")
        sys.exit(1)
    # Load environment variables
    load_dotenv(env_path)
    load_dotenv()
    print(os.getenv("AZURE_SUBSCRIPTION_ID")) 
    #print('Client ID',os.getenv('AZURE_CLIENT_ID'))
    console = Console()
    # Print header
    console.print("\n🔍 [bold blue]InfraWatch[/bold blue] - Azure VM Monitor")
    console.print("=" * 50)
    
    # Initialize Azure provider
    provider = AzureProvider()  # Will auto-detect subscription
    
    # Get VMs
    console.print("🔄 Fetching Azure VMs...")
    vms = provider.list_vms()
    
    # Display results
    display_vms_table(vms)

if __name__ == "__main__":
    main()