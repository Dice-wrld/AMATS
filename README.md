# AMATS - Asset Management and Asset Tracking System

## UTV Ghana Field Study Project
**Developed by:** Amissah Kevin Baiden  
**Institution:** Ghana Communication Technology University  
**Program:** BSc Cyber Security  
**Course:** Field Trip and Report Writing  
**Date:** November 2025

---

## Overview

AMATS (Asset Management and Asset Tracking System) is a comprehensive web-based solution designed to address the security liabilities identified at the Information Technology Department of United Television (UTV) Ghana. The system provides computerized access management and asset tracking capabilities to replace manual logbook processes.

## Features

### Core Functionality
- **User Authentication:** Role-based access control (Admin, Technician, Supervisor)
- **Asset Management:** Complete IT and broadcast equipment lifecycle management
- **Assignment Tracking:** Digital issuance and return workflow
- **Network Auto-Detection:** Automatic asset discovery via MAC address scanning
- **Audit Trail:** Comprehensive logging of all system activities
- **Reporting:** CSV export capabilities for inventory and compliance

### Security Features
- Password hashing with Django's built-in security
- Session management and CSRF protection
- Role-based permissions and access control
- IP address logging for all transactions
- Complete audit trail for compliance

### Technical Specifications
- **Framework:** Django 4.2 LTS
- **Frontend:** Bootstrap 5 with Crispy Forms
- **Database:** SQLite (development) / PostgreSQL (production)
- **Python:** 3.9+
- **Network Scanning:** Custom Python scanner with ARP detection

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Instructions

1. **Clone or extract the repository:**
   ```bash
   cd amats_system
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the application:**
   - URL: http://127.0.0.1:8000
   - Admin: http://127.0.0.1:8000/admin

---

## Project Structure

```
amats_system/
├── amats_project/          # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point
├── asset_management/       # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Business logic
│   ├── forms.py           # Form definitions
│   ├── urls.py            # App URL patterns
│   ├── admin.py           # Admin configuration
│   └── templates/         # HTML templates
│       └── asset_management/
├── network_scanner/        # Network detection module
│   └── scanner.py         # MAC address scanner
├── static/                # Static assets
│   ├── css/
│   └── js/
├── requirements.txt       # Python dependencies
└── manage.py             # Django management script
```

---

## Usage

### Initial Setup

1. **Login:** Use superuser credentials or create users via admin panel
2. **Create Categories:** Add asset categories (e.g., Laptops, Cameras, Servers)
3. **Add Assets:** Register all IT and broadcast equipment
4. **Configure Network:** Set up subnet for automatic device detection

### Daily Operations

**Issuing Assets:**
- Navigate to asset list
- Select "Issue" on available asset
- Assign to technician with due date
- System logs transaction automatically

**Returning Assets:**
- Go to dashboard or user profile
- Click "Return" on active assignment
- Verify condition and complete return

**Network Scanning:**
- Access Network Scan menu (Admin only)
- Enter subnet (e.g., 192.168.1.0/24)
- System detects devices and updates timestamps
- Missing assets appearing on network are flagged

**Generating Reports:**
- Go to Reports section
- Select report type (Inventory, Assignments)
- Download CSV for external analysis

---

## Security Considerations

- Change default SECRET_KEY in production
- Use HTTPS in production environment
- Regular database backups
- Network scanner requires appropriate permissions
- Monitor audit logs for anomalies

---

## Field Study Context

This system addresses the following vulnerabilities identified at UTV Ghana:

1. **Outdated Tracking:** Replaced manual logbooks with digital system
2. **Access Control:** Clear role-based permissions and accountability
3. **Asset Visibility:** Real-time status tracking and network detection
4. **Audit Compliance:** Comprehensive logging for security assessments
5. **Missing Device Detection:** Automatic discovery when devices reconnect

---

## License

Academic Project - Ghana Communication Technology University

## Contact

**Developer:** Amissah Kevin Baiden  
**Institution:** Ghana Communication Technology University  
**Department:** Computer Science  
**Program:** BSc Cyber Security

---

## Acknowledgements

- **UTV Ghana:** For providing operational insights through public reports
- **Dr. Martin Mabeifam Ujakpa:** For guidance on field-study methodology
- **Despite Group of Companies:** For broadcasting industry context
