#!/usr/bin/env python3

import ssl
import getpass
import time
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

def read_config(filename='vconnect_starter.txt'):
    """Read vCenter hostname and username from the starter file"""
    config = {}
    with open(filename, 'r') as f:
        content = f.read()
        
        # Extract host value
        if 'host=' in content:
            start = content.find('host=') + 6
            end = content.find('"', start)
            config['vcenter_host'] = content[start:end]
        
        # Extract user value
        if 'user=' in content:
            start = content.find('user=') + 6
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
    
    # Filter VMs if name_filter provided
    if name_filter:
        vms = [vm for vm in vms if name_filter.lower() in vm.name.lower()]
    
    return vms

def display_vm_info(vms):
    """Display VM metadata"""
    if not vms:
        print("\nNo VMs found!")
        return
        
    print(f"\n{'VM Name':<30} {'Power State':<15} {'CPUs':<8} {'Memory (GB)':<12} {'IP Address':<15}")
    print("=" * 90)
    
    for vm in vms:
        name = vm.name
        power_state = vm.runtime.powerState
        num_cpu = vm.config.hardware.numCPU
        memory_gb = vm.config.hardware.memoryMB / 1024
        
        # Get IP address
        ip_address = "N/A"
        if vm.guest.ipAddress:
            ip_address = vm.guest.ipAddress
        
        print(f"{name:<30} {power_state:<15} {num_cpu:<8} {memory_gb:<12.2f} {ip_address:<15}")

def vmmenu():
    """Display VM Actions menu"""
    print("\n[1] Power on VM")
    print("[2] Power Off VM")
    print("[3] Take a Snapshot")
    print("[4] Delete a VM")
    print("[5] Reconfigure a VM")
    print("[6] Rename a VM")
    print("[0] Exit the VM Actions.")

def power_on_vm(si):
    """Power on one or more VMs"""
    print("\n=== Power On VM(s) ===")
    
    vms = search_vms(si)
    print("\nVMs managed by vCenter:")
    for vm in vms:
        print(f"  - {vm.name}")
    
    vm_name = input("\nEnter VM name to power on (leave empty for ALL): ").strip()
    
    if vm_name:
        target_vms = [vm for vm in vms if vm_name.lower() in vm.name.lower()]
        if not target_vms:
            print(f"No VM found matching '{vm_name}'")
            return
    else:
        confirm = input("Are you sure you want to power on ALL VMs? (Y/N): ").strip().upper()
        if confirm != 'Y':
            print("Cancelled.")
            return
        target_vms = vms
    
    for vm in target_vms:
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            print(f"{vm.name} is already powered on, skipping!")
        else:
            print(f"{vm.name} is not powered on, powering on now!")
            try:
                task = vm.PowerOn()
                time.sleep(2)
                print(f"{vm.name} is now powered on!")
            except Exception as e:
                print(f"Failed to power on {vm.name}: {e}")

def power_off_vm(si):
    """Power off one or more VMs"""
    print("\n=== Power Off VM(s) ===")
    
    vms = search_vms(si)
    print("\nVMs managed by vCenter:")
    for vm in vms:
        print(f"  - {vm.name}")
    
    vm_name = input("\nEnter VM name to power off (leave empty for ALL): ").strip()
    
    if vm_name:
        target_vms = [vm for vm in vms if vm_name.lower() in vm.name.lower()]
        if not target_vms:
            print(f"No VM found matching '{vm_name}'")
            return
    else:
        confirm = input("Are you sure you want to power off ALL VMs? (Y/N): ").strip().upper()
        if confirm != 'Y':
            print("Cancelled.")
            return
        target_vms = vms
    
    for vm in target_vms:
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
            print(f"{vm.name} is already powered off, skipping!")
        else:
            print(f"{vm.name} is powered on, powering off now!")
            try:
                task = vm.PowerOff()
                time.sleep(2)
                print(f"{vm.name} is now powered off!")
            except Exception as e:
                print(f"Failed to power off {vm.name}: {e}")

def create_snapshot(si):
    """Create a snapshot of a VM"""
    print("\n=== Take a Snapshot ===")
    
    vms = search_vms(si)
    print("\nVMs managed by vCenter:")
    for vm in vms:
        print(f"  - {vm.name}")
    
    vm_name = input("\nEnter VM name to snapshot: ").strip()
    
    target_vms = [vm for vm in vms if vm_name.lower() in vm.name.lower()]
    if not target_vms:
        print(f"No VM found matching '{vm_name}'")
        return
    
    vm = target_vms[0]
    
    confirm = input(f"Create snapshot of '{vm.name}'? (Y/N): ").strip().upper()
    if confirm != 'Y':
        print("Cancelled.")
        return
    
    snapshot_name = input("Enter snapshot name: ").strip()
    if not snapshot_name:
        snapshot_name = f"Snapshot-{time.strftime('%Y%m%d-%H%M%S')}"
    
    snapshot_description = input("Enter snapshot description (optional): ").strip()
    
    print(f"\nCreating snapshot '{snapshot_name}' for {vm.name}...")
    try:
        task = vm.CreateSnapshot(
            name=snapshot_name,
            description=snapshot_description,
            memory=False,
            quiesce=False
        )
        print(f"Snapshot '{snapshot_name}' created successfully!")
    except Exception as e:
        print(f"Failed to create snapshot: {e}")

def delete_vm(si):
    """Delete a VM from disk"""
    print("\n=== Delete a VM ===")
    
    vms = search_vms(si)
    print("\nVMs managed by vCenter:")
    for vm in vms:
        print(f"  - {vm.name}")
    
    vm_name = input("\nEnter VM name to DELETE: ").strip()
    
    target_vms = [vm for vm in vms if vm_name.lower() in vm.name.lower()]
    if not target_vms:
        print(f"No VM found matching '{vm_name}'")
        return
    
    vm = target_vms[0]
    
    # Double confirmation for deletion
    print(f"\n⚠️  WARNING: You are about to DELETE '{vm.name}' permanently!")
    confirm1 = input(f"Are you ABSOLUTELY SURE you want to delete '{vm.name}'? (YES/NO): ").strip().upper()
    if confirm1 != 'YES':
        print("Cancelled.")
        return
    
    confirm2 = input(f"Type the VM name '{vm.name}' to confirm deletion: ").strip()
    if confirm2 != vm.name:
        print("VM name does not match. Deletion cancelled.")
        return
    
    # Check if VM is powered off
    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOff:
        print(f"\n{vm.name} must be powered off before deletion.")
        power_off = input("Power off now? (Y/N): ").strip().upper()
        if power_off == 'Y':
            try:
                task = vm.PowerOff()
                time.sleep(2)
                print(f"{vm.name} powered off.")
            except Exception as e:
                print(f"Failed to power off: {e}")
                return
        else:
            print("Deletion cancelled.")
            return
    
    # Delete the VM
    print(f"\nDeleting {vm.name} from disk...")
    try:
        task = vm.Destroy_Task()
        print(f"✓ {vm.name} has been deleted successfully!")
    except Exception as e:
        print(f"Failed to delete VM: {e}")

def reconfigure_vm(si):
    """Reconfigure VM CPU and Memory"""
    print("\n=== Reconfigure a VM ===")
    
    vms = search_vms(si)
    print("\nVMs managed by vCenter:")
    for vm in vms:
        print(f"  - {vm.name}")
    
    vm_name = input("\nEnter VM name to reconfigure: ").strip()
    
    target_vms = [vm for vm in vms if vm_name.lower() in vm.name.lower()]
    if not target_vms:
        print(f"No VM found matching '{vm_name}'")
        return
    
    vm = target_vms[0]
    
    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOff:
        print(f"\n⚠️  {vm.name} must be powered off to reconfigure hardware!")
        print("Please power off the VM first.")
        return
    
    confirm = input(f"Reconfigure '{vm.name}'? (Y/N): ").strip().upper()
    if confirm != 'Y':
        print("Cancelled.")
        return
    
    change_cpu = input("Change CPU count? (Y/N): ").strip().upper()
    new_cpu = None
    if change_cpu == 'Y':
        try:
            new_cpu = int(input("Enter new CPU count: ").strip())
        except ValueError:
            print("Invalid CPU count")
            return
    
    change_mem = input("Change Memory? (Y/N): ").strip().upper()
    new_memory_gb = None
    if change_mem == 'Y':
        try:
            new_memory_gb = int(input("Enter new Memory in GB: ").strip())
        except ValueError:
            print("Invalid memory size")
            return
    
    config_spec = vim.vm.ConfigSpec()
    
    if new_cpu:
        config_spec.numCPUs = new_cpu
    
    if new_memory_gb:
        config_spec.memoryMB = new_memory_gb * 1024
    
    print(f"\nReconfiguring {vm.name}...")
    try:
        task = vm.Reconfigure(spec=config_spec)
        print(f"✓ {vm.name} has been reconfigured!")
        if new_cpu:
            print(f"  - CPUs: {new_cpu}")
        if new_memory_gb:
            print(f"  - Memory: {new_memory_gb} GB")
    except Exception as e:
        print(f"Failed to reconfigure VM: {e}")

def rename_vm(si):
    """Rename a VM"""
    print("\n=== Rename a VM ===")
    
    vms = search_vms(si)
    print("\nVMs managed by vCenter:")
    for vm in vms:
        print(f"  - {vm.name}")
    
    vm_name = input("\nEnter VM name to rename: ").strip()
    
    target_vms = [vm for vm in vms if vm_name.lower() in vm.name.lower()]
    if not target_vms:
        print(f"No VM found matching '{vm_name}'")
        return
    
    vm = target_vms[0]
    
    confirm = input(f"Rename '{vm.name}'? (Y/N): ").strip().upper()
    if confirm != 'Y':
        print("Cancelled.")
        return
    
    new_name = input("Enter new VM name: ").strip()
    if not new_name:
        print("Name cannot be empty")
        return
    
    print(f"\nRenaming {vm.name} to {new_name}...")
    try:
        task = vm.Rename(newName=new_name)
        print(f"✓ VM renamed successfully to '{new_name}'!")
    except Exception as e:
        print(f"Failed to rename VM: {e}")

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
    
    aboutInfo = si.content.about
    print(aboutInfo)
    
    get_session_info(si, vcenter_host)
    
    option = 0
    
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
    
    aboutInfo = si.content.about
    print(aboutInfo)
    
    get_session_info(si, vcenter_host)
    
    # Main menu loop
    while True:
        print("\n[1] VCenter Info")
        print("[2] Session Details")
        print("[3] VM Details")
        print("[4] Perform VM Actions")
        print("[0] Exit the program.")
        
        option = int(input("Enter your option: "))
        
        if option == 1:
            print("VCenter Info Option Selected.")
            aboutInfo = si.content.about
            print(aboutInfo)
        
        elif option == 2:
            print("Session Details Selected.")
            get_session_info(si, vcenter_host)
        
        elif option == 3:
            print("VM Details Selected.")
            name_filter = input("Enter VM name to search (leave empty for all): ").strip()
            if name_filter:
                vms = search_vms(si, name_filter)
            else:
                vms = search_vms(si)
            display_vm_info(vms)
        
        elif option == 4:
            print()
            vmmenu()
            vmoption = int(input("Enter your option: "))
            
            while vmoption != 0:
                if vmoption == 1:
                    power_on_vm(si)
                
                elif vmoption == 2:
                    power_off_vm(si)
                
                elif vmoption == 3:
                    create_snapshot(si)
                
                elif vmoption == 4:
                    delete_vm(si)
                
                elif vmoption == 5:
                    reconfigure_vm(si)
                
                elif vmoption == 6:
                    rename_vm(si)
                
                vmmenu()
                vmoption = int(input("Enter your option: "))
        
        elif option == 0:
            print("Exiting program...")
            Disconnect(si)
            print("Goodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
