#!/usr/bin/env python
"""
AMATS Setup Script
Initializes the database and creates sample data
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amats_project.settings')
django.setup()

from django.contrib.auth.models import User
from asset_management.models import AssetCategory, Asset, UserProfile

def setup_demo_data():
    """Create demonstration data"""
    print("Setting up AMATS demonstration data...")

    # Create categories
    categories = [
        ('Laptops', 'Portable computers for staff'),
        ('Cameras', 'Broadcast cameras and equipment'),
        ('Servers', 'Server hardware and storage'),
        ('Network Equipment', 'Routers, switches, access points'),
        ('Storage Media', 'External drives, USB devices'),
        ('Audio Equipment', 'Microphones, mixers, speakers'),
    ]

    for name, desc in categories:
        AssetCategory.objects.get_or_create(name=name, defaults={'description': desc})
    print(f"✓ Created {len(categories)} asset categories")

    # Create demo users if they don't exist
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            'admin', 'admin@utv.gh', 'admin123'
        )
        admin.profile.role = 'ADMIN'
        admin.profile.department = 'IT & Broadcast Engineering'
        admin.profile.save()
        print("✓ Created admin user (admin/admin123)")

    if not User.objects.filter(username='technician').exists():
        tech = User.objects.create_user(
            'technician', 'tech@utv.gh', 'tech123'
        )
        tech.profile.role = 'TECH'
        tech.profile.department = 'Broadcast Engineering'
        tech.profile.save()
        print("✓ Created technician user (technician/tech123)")

    # Create sample assets
    sample_assets = [
        ('UTV-LAP-001', 'Broadcast Laptop 1', 'Laptops', 'AVAILABLE', 'Dell Precision', '00:1A:2B:3C:4D:5E'),
        ('UTV-CAM-001', 'Studio Camera A', 'Cameras', 'AVAILABLE', 'Sony PXW-Z280', '00:1A:2B:3C:4D:5F'),
        ('UTV-SRV-001', 'Main Broadcast Server', 'Servers', 'ASSIGNED', 'Dell PowerEdge', '00:1A:2B:3C:4D:60'),
        ('UTV-NET-001', 'Core Switch', 'Network Equipment', 'AVAILABLE', 'Cisco Catalyst', None),
        ('UTV-STR-001', 'Video Storage Array', 'Storage Media', 'AVAILABLE', 'Synology NAS', '00:1A:2B:3C:4D:61'),
    ]

    for tag, name, cat_name, status, model, mac in sample_assets:
        category = AssetCategory.objects.get(name=cat_name)
        Asset.objects.get_or_create(
            asset_tag=tag,
            defaults={
                'name': name,
                'category': category,
                'status': status,
                'model': model,
                'mac_address': mac,
                'created_by': User.objects.first(),
            }
        )
    print(f"✓ Created {len(sample_assets)} sample assets")

    print("\nSetup complete! You can now:")
    print("  - Login as admin: admin / admin123")
    print("  - Login as technician: technician / tech123")
    print("  - Access admin panel at /admin/")

if __name__ == '__main__':
    from django.core.management import call_command

    print("AMATS System Setup")
    print("==================\n")

    # Run migrations
    print("Running migrations...")
    call_command('migrate', verbosity=0)
    print("✓ Database ready\n")

    # Setup demo data
    setup_demo_data()

    print("\nStarting development server...")
    call_command('runserver')
