#!/usr/bin/env python3

import ssl
import getpass
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

def read_config(filename='vconnect_starter.txt'):
    config = {}
    with open(filename, 'r') as f:
        content = f.read()
        
        if 'host=' in content:
            start = content.find('host=') + 6  # +6 to skip 'host="'
            end = content.find('"', start)
            config['vcenter_host'] = content[start:end]
        
        if 'user=' in content:
            start = content.find('user=') + 6  # +6 to skip 'user="'
            end = content.find('"', start)
            config['username'] = content[start:end]
    
    return config

def get_session_info(si, vcenter_host):
    """Display current session information"""
    session_mgr = si.content.sessionManager
    current_session = session_mgr.currentSession
    
    print("\n=== Current Session Information ===")
    print(f"DOMAIN/Username: {current_session.userName}")
    print(f"vCenter Server: {vcenter_host}")
    print(f"Source IP Address: {current_session.ipAddress}")
    print("=" * 40)

def search_vms(si, name_filter=None):
    """Search for VMs by name filter. If no filter, return all VMs"""
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive
    )
    
    vms = container_view.view
    container_view.Destroy()
    
    if name_filter:
        vms = [vm for vm in vms if name_filter.lower() in vm.name.lower()]
    
    return vms

def display_vm_info(vms):
    """Display VM metadata"""
    print(f"\n{'VM Name':<30} {'Power State':<15} {'CPUs':<8} {'Memory (GB)':<12} {'IP Address':<15}")
    print("=" * 90)
    
    for vm in vms:
        name = vm.name
        power_state = vm.runtime.powerState
        num_cpu = vm.config.hardware.numCPU
        memory_gb = vm.config.hardware.memoryMB / 1024
        
        ip_address = "N/A"
        if vm.guest.ipAddress:
            ip_address = vm.guest.ipAddress
        
        print(f"{name:<30} {power_state:<15} {num_cpu:<8} {memory_gb:<12.2f} {ip_address:<15}")

def main():
    print("Reading configuration from vconnect_starter.txt...")
    config = read_config('vconnect_starter.txt')
    vcenter_host = config['vcenter_host']
    username = config['username']
    
    print(f"vCenter Host: {vcenter_host}")
    print(f"Username: {username}")
    
    password = getpass.getpass(f"\nEnter password for {username}: ")
    
    print("Connecting to vCenter...")
    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    s.verify_mode = ssl.CERT_NONE
    
    si = SmartConnect(host=vcenter_host, 
                     user=username, 
                     pwd=password, 
                     sslContext=s)
    
    get_session_info(si, vcenter_host)
    
    while True:
        print("\n=== VM Manager Menu ===")
        print("1. List all VMs")
        print("2. Search VMs by name")
        print("3. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            # Requirement 3: Search with no filter (all VMs)
            vms = search_vms(si)
            # Requirement 4: Display VM metadata
            display_vm_info(vms)
        
        elif choice == '2':
            # Requirement 3: Search with filter
            name_filter = input("Enter VM name to search: ")
            vms = search_vms(si, name_filter)
            if vms:
                # Requirement 4: Display VM metadata
                display_vm_info(vms)
            else:
                print(f"No VMs found matching '{name_filter}'")
        
        elif choice == '3':
            print("Disconnecting...")
            Disconnect(si)
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()


