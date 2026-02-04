#!/bin/bash

echo "=========================================="
echo "AMATS Setup - Linux/Mac"
echo "Access Management and Asset Tracking System"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed! Please install Python 3.9 or higher."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment!"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies!"
    exit 1
fi

echo "Running database migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Migration failed!"
    exit 1
fi

echo "Creating demo data..."
python << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amats_project.settings')
import django
django.setup()
from django.contrib.auth.models import User
from asset_management.models import AssetCategory

# Create admin
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@utv.gh', 'admin123')
    print('Created admin user: admin/admin123')

# Create technician
if not User.objects.filter(username='tech').exists():
    tech = User.objects.create_user('tech', 'tech@utv.gh', 'tech123')
    tech.profile.role = 'TECH'
    tech.profile.save()
    print('Created technician user: tech/tech123')

# Create categories
categories = ['Laptops', 'Cameras', 'Servers', 'Network Equipment', 'Storage Media']
for cat in categories:
    AssetCategory.objects.get_or_create(name=cat)
print('Created asset categories')
print('Demo data created successfully!')
EOF

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Access the system:"
echo "  Admin: admin / admin123"
echo "  Tech:  tech / tech123"
echo ""
echo "Starting server..."
python manage.py runserver
