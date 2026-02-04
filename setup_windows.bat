@echo off
ECHO ==========================================
ECHO AMATS Setup - Windows
ECHO Access Management and Asset Tracking System
ECHO ==========================================
ECHO.

REM Check if Python is installed
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO Python is not installed! Please install Python 3.9 or higher.
    pause
    exit /b 1
)

ECHO Creating virtual environment...
python -m venv venv
IF ERRORLEVEL 1 (
    ECHO Failed to create virtual environment!
    pause
    exit /b 1
)

ECHO Activating virtual environment...
call venv\Scripts\activate

ECHO Installing dependencies...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    ECHO Failed to install dependencies!
    pause
    exit /b 1
)

ECHO Running database migrations...
python manage.py migrate
IF ERRORLEVEL 1 (
    ECHO Migration failed!
    pause
    exit /b 1
)

ECHO Creating demo data...
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amats_project.settings')
import django
django.setup()
from django.contrib.auth.models import User
from asset_management.models import AssetCategory, Asset

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
"

ECHO.
ECHO ==========================================
ECHO Setup Complete!
ECHO ==========================================
ECHO.
ECHO Access the system:
ECHO   Admin: admin / admin123
ECHO   Tech:  tech / tech123
ECHO.
ECHO Starting server...
python manage.py runserver

pause
