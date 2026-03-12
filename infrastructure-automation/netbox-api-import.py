#!/usr/bin/env python3
"""
Netbox API Import Script
Imports infrastructure inventory into Netbox
"""

import json
import sys
import os

try:
    import pynetbox
except ImportError:
    print("ERROR: pynetbox module not found")
    print("Install it with: pip3 install pynetbox")
    sys.exit(1)

# Configuration
NETBOX_URL = os.environ.get("NETBOX_URL", "http://localhost:8000")
API_TOKEN = os.environ.get("NETBOX_API_TOKEN", "")

if not API_TOKEN:
    print("ERROR: NETBOX_API_TOKEN environment variable not set")
    print("\nTo get your API token:")
    print("1. Log into Netbox web UI")
    print("2. Click your username (top right) → API Tokens")
    print("3. Click 'Add a token'")
    print("4. Create token with write permissions")
    print("5. Export it: export NETBOX_API_TOKEN='your-token-here'")
    print("\nThen run this script again.")
    sys.exit(1)

INVENTORY_FILE = os.environ.get("INVENTORY_FILE", "./netbox-inventory.json")

print(f"=== Netbox API Import ===")
print(f"Netbox URL: {NETBOX_URL}")
print(f"Inventory: {INVENTORY_FILE}")
print()

# Initialize Netbox API
try:
    nb = pynetbox.api(NETBOX_URL, token=API_TOKEN)
    nb.http_session.verify = False  # Disable SSL verification for self-signed certs
    print("✓ Connected to Netbox API")
except Exception as e:
    print(f"✗ Failed to connect to Netbox: {e}")
    sys.exit(1)

# Load inventory data
try:
    with open(INVENTORY_FILE, 'r') as f:
        data = json.load(f)
    print(f"✓ Loaded inventory data")
    print(f"  - Devices: {len(data['devices'])}")
    print(f"  - Networks: {len(data['networks'])}")
    print()
except Exception as e:
    print(f"✗ Failed to load inventory: {e}")
    sys.exit(1)

# Track statistics
stats = {
    'sites': {'created': 0, 'exists': 0, 'failed': 0},
    'manufacturers': {'created': 0, 'exists': 0, 'failed': 0},
    'device_roles': {'created': 0, 'exists': 0, 'failed': 0},
    'platforms': {'created': 0, 'exists': 0, 'failed': 0},
    'prefixes': {'created': 0, 'exists': 0, 'failed': 0},
    'devices': {'created': 0, 'exists': 0, 'failed': 0},
    'ip_addresses': {'created': 0, 'exists': 0, 'failed': 0}
}

# Create or get site
print("[1/7] Creating site...")
try:
    site = nb.dcim.sites.get(slug='site-main')
    if site:
        print("  ✓ Site 'Site-Main' already exists")
        stats['sites']['exists'] += 1
    else:
        site = nb.dcim.sites.create(
            name='Site-Main',
            slug='site-main',
            status='active'
        )
        print("  ✓ Created site: Site-Main")
        stats['sites']['created'] += 1
except Exception as e:
    print(f"  ✗ Error with site: {e}")
    stats['sites']['failed'] += 1

# Create manufacturers
print("\n[2/7] Creating manufacturers...")
manufacturers = set()
for device in data['devices']:
    if 'manufacturer' in device and device['manufacturer'] not in ['Unknown', '']:
        manufacturers.add(device['manufacturer'])

for mfr_name in manufacturers:
    try:
        mfr = nb.dcim.manufacturers.get(slug=mfr_name.lower().replace(' ', '-'))
        if mfr:
            stats['manufacturers']['exists'] += 1
        else:
            nb.dcim.manufacturers.create(
                name=mfr_name,
                slug=mfr_name.lower().replace(' ', '-')
            )
            print(f"  ✓ Created manufacturer: {mfr_name}")
            stats['manufacturers']['created'] += 1
    except Exception as e:
        print(f"  ✗ Error creating manufacturer {mfr_name}: {e}")
        stats['manufacturers']['failed'] += 1

# Create device roles
print("\n[3/7] Creating device roles...")
roles = set()
for device in data['devices']:
    if 'device_role' in device:
        roles.add(device['device_role'])

for role_name in roles:
    try:
        role_slug = role_name.lower().replace('/', '-').replace(' ', '-')
        role = nb.dcim.device_roles.get(slug=role_slug)
        if role:
            stats['device_roles']['exists'] += 1
        else:
            nb.dcim.device_roles.create(
                name=role_name,
                slug=role_slug,
                color='2196f3'  # Blue
            )
            print(f"  ✓ Created device role: {role_name}")
            stats['device_roles']['created'] += 1
    except Exception as e:
        print(f"  ✗ Error creating device role {role_name}: {e}")
        stats['device_roles']['failed'] += 1

# Create platforms
print("\n[4/7] Creating platforms...")
platforms = set()
for device in data['devices']:
    if 'platform' in device and device['platform'] not in ['Unknown', '']:
        platforms.add(device['platform'])

for platform_name in platforms:
    try:
        platform_slug = platform_name.lower().replace(' ', '-').replace('.', '-')
        platform = nb.dcim.platforms.get(slug=platform_slug)
        if platform:
            stats['platforms']['exists'] += 1
        else:
            nb.dcim.platforms.create(
                name=platform_name,
                slug=platform_slug
            )
            print(f"  ✓ Created platform: {platform_name}")
            stats['platforms']['created'] += 1
    except Exception as e:
        print(f"  ✗ Error creating platform {platform_name}: {e}")
        stats['platforms']['failed'] += 1

# Create prefixes/networks
print("\n[5/7] Creating prefixes/networks...")
for network in data['networks']:
    try:
        if network['prefix'] == 'TBD':
            print(f"  ⊘ Skipping TBD prefix: {network['vlan']}")
            continue

        prefix = nb.ipam.prefixes.get(prefix=network['prefix'])
        if prefix:
            stats['prefixes']['exists'] += 1
        else:
            nb.ipam.prefixes.create(
                prefix=network['prefix'],
                description=network.get('description', ''),
                status='active'
            )
            print(f"  ✓ Created prefix: {network['prefix']} ({network['vlan']})")
            stats['prefixes']['created'] += 1
    except Exception as e:
        print(f"  ✗ Error creating prefix {network['prefix']}: {e}")
        stats['prefixes']['failed'] += 1

# Create devices
print("\n[6/7] Creating devices...")
for device in data['devices']:
    try:
        # Get or create device type if model is specified
        device_type = None
        if device.get('model') and device.get('manufacturer'):
            mfr_slug = device['manufacturer'].lower().replace(' ', '-')
            model_slug = device['model'].lower().replace(' ', '-')

            manufacturer = nb.dcim.manufacturers.get(slug=mfr_slug)
            if manufacturer:
                device_type = nb.dcim.device_types.get(slug=model_slug)
                if not device_type:
                    try:
                        device_type = nb.dcim.device_types.create(
                            manufacturer=manufacturer.id,
                            model=device['model'],
                            slug=model_slug
                        )
                    except:
                        pass

        # Get device role
        role_slug = device['device_role'].lower().replace('/', '-').replace(' ', '-')
        role = nb.dcim.device_roles.get(slug=role_slug)

        # Get platform
        platform = None
        if device.get('platform') and device['platform'] not in ['Unknown', '']:
            platform_slug = device['platform'].lower().replace(' ', '-').replace('.', '-')
            platform = nb.dcim.platforms.get(slug=platform_slug)

        # Check if device exists
        existing = nb.dcim.devices.get(name=device['name'])
        if existing:
            print(f"  ⊙ Device already exists: {device['name']}")
            stats['devices']['exists'] += 1
        else:
            # Create device
            device_data = {
                'name': device['name'],
                'device_role': role.id if role else None,
                'site': site.id if site else None,
                'status': device.get('status', 'active')
            }

            if device_type:
                device_data['device_type'] = device_type.id
            if platform:
                device_data['platform'] = platform.id

            new_device = nb.dcim.devices.create(**device_data)
            print(f"  ✓ Created device: {device['name']} ({device.get('primary_ip', 'no IP')})")
            stats['devices']['created'] += 1

            # Add primary IP if specified
            if device.get('primary_ip'):
                try:
                    ip_addr = nb.ipam.ip_addresses.get(address=device['primary_ip'])
                    if not ip_addr:
                        ip_addr = nb.ipam.ip_addresses.create(
                            address=device['primary_ip'],
                            status='active',
                            assigned_object_type='dcim.device',
                            assigned_object_id=new_device.id
                        )
                        stats['ip_addresses']['created'] += 1

                        # Set as primary IP
                        new_device.primary_ip4 = ip_addr.id
                        new_device.save()
                except Exception as e:
                    print(f"    ⚠ Could not assign IP {device['primary_ip']}: {e}")

    except Exception as e:
        print(f"  ✗ Error creating device {device['name']}: {e}")
        stats['devices']['failed'] += 1

# Summary
print("\n" + "="*50)
print("IMPORT SUMMARY")
print("="*50)
for category, counts in stats.items():
    total = counts['created'] + counts['exists'] + counts['failed']
    if total > 0:
        print(f"\n{category.upper()}:")
        print(f"  Created: {counts['created']}")
        print(f"  Already existed: {counts['exists']}")
        print(f"  Failed: {counts['failed']}")

print("\n✓ Import complete!")
print(f"\nAccess Netbox at: {NETBOX_URL}")
