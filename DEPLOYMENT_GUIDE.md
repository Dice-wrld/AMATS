# AMATS Production Deployment Guide

## Overview
This guide covers deploying AMATS to a production environment suitable for UTV Ghana's operations.

## Prerequisites
- Linux server (Ubuntu 20.04 LTS recommended) or Windows Server 2019+
- Python 3.9+
- PostgreSQL 12+ (recommended) or MySQL 8+
- Nginx web server
- SSL Certificate (Let's Encrypt recommended)
- Domain name (optional but recommended)

## Production Checklist

### 1. Environment Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib

# Create database
sudo -u postgres psql
create database amats_db;
create user amats_user with encrypted password 'secure_password';
grant all privileges on database amats_db to amats_user;
\q
```

### 2. Application Setup
```bash
# Create application directory
sudo mkdir -p /var/www/amats
sudo chown $USER:$USER /var/www/amats
cd /var/www/amats

# Clone/extract application
git clone <repository> .  # or extract zip file

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Configure environment
cp .env.example .env
# Edit .env with production values:
# - Set DJANGO_DEBUG=False
# - Set strong SECRET_KEY
# - Configure PostgreSQL database
# - Add your domain to ALLOWED_HOSTS
```

### 3. Database Migration
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 4. Gunicorn Configuration
Create `/etc/systemd/system/amats.service`:
```ini
[Unit]
Description=AMATS Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/amats
Environment="PATH=/var/www/amats/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=amats_project.settings"
ExecStart=/var/www/amats/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/amats/app.sock amats_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl start amats
sudo systemctl enable amats
```

### 5. Nginx Configuration
Create `/etc/nginx/sites-available/amats`:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /var/www/amats;
    }
    location /media/ {
        root /var/www/amats;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/amats/app.sock;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/amats /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 7. Security Hardening
```bash
# Set proper file permissions
sudo chown -R www-data:www-data /var/www/amats/
sudo chmod -R 755 /var/www/amats

# Secure .env file
sudo chmod 600 /var/www/amats/.env

# Configure firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 8. Backup Strategy
Create backup script `/var/www/amats/backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/amats"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump amats_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/amats/media/

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /var/www/amats/backup.sh
```

### 9. Monitoring Setup
Install monitoring tools:
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Monitor disk space
sudo apt install ncdu
```

### 10. Automated Tasks
Add to crontab for automated scanning:
```bash
# Scan network every hour
0 * * * * cd /var/www/amats && venv/bin/python manage.py scan_network --subnet 192.168.1.0/24 >> /var/log/amats_scan.log 2>&1

# Check overdue daily at 8 AM
0 8 * * * cd /var/www/amats && venv/bin/python manage.py check_overdue >> /var/log/amats_overdue.log 2>&1
```

## Windows Server Deployment

### IIS + FastCGI Method
1. Install Python 3.9+ and add to PATH
2. Install IIS with CGI support
3. Install wfastcgi: `pip install wfastcgi`
4. Configure web.config for FastCGI
5. Set up SQL Server or PostgreSQL
6. Configure Windows Firewall

### Alternative: Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "amats_project.wsgi:application"]
```

## Post-Deployment Tasks

1. **Create Production Users**
   - Login as admin
   - Create User accounts for all IT staff
   - Assign appropriate roles (Admin, Technician, Supervisor)

2. **Configure Categories**
   - Add UTV-specific categories:
     - Broadcast Cameras
     - Editing Suites
     - Satellite Equipment
     - Studio Lighting
     - Field Production Gear

3. **Asset Import**
   - Prepare CSV with existing assets
   - Use admin interface or custom import script

4. **Network Configuration**
   - Set correct subnet in Admin > Settings
   - Test MAC address detection
   - Verify firewall rules for scanning

5. **Email Notifications** (Optional)
   - Configure SMTP settings
   - Test overdue notifications
   - Set up admin alerts

## Troubleshooting

### Common Issues:

**Static files not loading:**
```bash
python manage.py collectstatic --noinput
# Check nginx static files path
```

**Permission denied on upload:**
```bash
sudo chown -R www-data:www-data /var/www/amats/media/
```

**Database connection fails:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in .env file
- Ensure amats_user has proper permissions

**Network scan not working:**
- Requires root/sudo for ARP scanning
- Alternative: Use python-nmap with proper permissions
- Check firewall allows ICMP

## Maintenance

### Regular Tasks:
- **Daily:** Check error logs, verify backups
- **Weekly:** Review audit logs, check disk space
- **Monthly:** Update SSL certificates (if not using certbot auto)
- **Quarterly:** Security updates, dependency updates

### Log Locations:
- Application: `/var/log/amats.log`
- Nginx: `/var/log/nginx/amats-error.log`
- System: `sudo journalctl -u amats`

## Support

For technical support or customization:
- Check README.md for basic documentation
- Review code comments for implementation details
- Refer to Django documentation: https://docs.djangoproject.com/

## Security Notes

- Never commit .env file to version control
- Regularly update dependencies: `pip list --outdated`
- Monitor failed login attempts in audit logs
- Keep SSL certificates up to date
- Restrict admin access by IP if possible
