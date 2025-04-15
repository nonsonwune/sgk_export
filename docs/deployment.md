# SGK Export System Deployment Guide

This comprehensive guide provides detailed instructions for deploying the SGK Export System in various environments, with special attention to office deployments using Network Attached Storage (NAS).

## Table of Contents

1. [Deployment Options](#deployment-options)
   - [Local Office Deployment](#local-office-deployment)
   - [Cloud Deployment](#cloud-deployment)
   - [Development Environment](#development-environment)
2. [Prerequisites](#prerequisites)
3. [Server Preparation](#server-preparation)
4. [Database Setup](#database-setup)
5. [Storage Configuration](#storage-configuration)
   - [Local Storage](#local-storage)
   - [NAS Configuration](#nas-configuration)
   - [Cloud Storage](#cloud-storage)
6. [Application Installation](#application-installation)
7. [Configuration](#configuration)
8. [Service Setup](#service-setup)
9. [Security Hardening](#security-hardening)
10. [Monitoring & Logging](#monitoring--logging)
11. [Backup & Recovery](#backup--recovery)
12. [Accessing the Application](#accessing-the-application)
13. [Upgrading & Maintenance](#upgrading--maintenance)
14. [Troubleshooting](#troubleshooting)

## Deployment Options

### Local Office Deployment

The SGK Export System can be deployed on an internal office server for teams that need to access the system within the company network. This guide primarily focuses on this deployment method.

**Advantages:**
- Complete control over infrastructure
- No ongoing cloud service costs
- Private network security

**Requirements:**
- Windows Server (2016+) or Linux server
- PostgreSQL database
- Network Attached Storage (optional but recommended)
- Network infrastructure for office-wide access

### Cloud Deployment

For organizations preferring cloud deployment, SGK Export System can be deployed on services like:
- AWS (EC2 + RDS)
- Microsoft Azure
- Google Cloud Platform
- Render.com (simplified deployment)

**Advantages:**
- Scalability and reliability
- Managed database options
- External accessibility
- Reduced IT infrastructure maintenance

Refer to the [Cloud Deployment](#cloud-deployment-detailed) section for specific instructions.

### Development Environment

For developers working on the application, a local development setup is recommended.

## Prerequisites

### Windows Server Requirements
- Windows Server 2016+ or Windows 10/11 Pro (64-bit)
- Minimum hardware: 4GB RAM, 4 CPU cores, 50GB storage
- Administrator access
- Static IP address on local network

### Linux Server Requirements
- Ubuntu 20.04+, CentOS 8+, or other major distribution
- Minimum hardware: 4GB RAM, 4 CPU cores, 50GB storage
- sudo/root access
- Static IP address on local network

### Software Requirements
- Python 3.8+ (3.9+ recommended)
- PostgreSQL 13+
- Git (for application installation)
- Web server: Nginx (recommended) or Apache
- Network Attached Storage (optional for file sharing)

## Server Preparation

### Windows Server Setup

1. **Update Windows**:
   - Install all available Windows updates
   - Restart the server after updates

2. **Python Installation**:
   ```bash
   # Download Python 3.9 (64-bit) from https://www.python.org/downloads/windows/
   # Run the installer with these options:
   # - Add Python to PATH
   # - Install for all users
   # - Customize installation > Add py launcher, pip, tcl/tk and IDLE
   ```

   Verify installation:
   ```
   python --version
   pip --version
   ```

3. **Install Required Tools**:
   ```bash
   # Install Git from https://git-scm.com/download/win
   # Install Visual C++ build tools if needed for package compilation
   ```

### Linux Server Setup

1. **Update system**:
   ```bash
   sudo apt update && sudo apt upgrade -y   # Ubuntu/Debian
   # OR
   sudo yum update -y                       # CentOS/RHEL
   ```

2. **Install Python and development tools**:
   ```bash
   # Ubuntu/Debian
   sudo apt install -y python3.9 python3.9-venv python3.9-dev python3-pip git build-essential

   # CentOS/RHEL
   sudo yum install -y python39 python39-devel python39-pip git
   ```

3. **Install additional dependencies**:
   ```bash
   # Ubuntu/Debian - Required for WeasyPrint and other packages
   sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libpq-dev
   ```

## Database Setup

### PostgreSQL Installation (Windows)

1. Download PostgreSQL 13+ installer from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
2. Run the installer with the following options:
   - Install all components
   - Set password for postgres user (record this securely)
   - Use default port 5432
   - Set locale to match your region

3. Create the application database:
   ```
   # Open pgAdmin (installed with PostgreSQL)
   # Right-click Databases → Create → Database...
   # Name: sgk_export
   # Owner: postgres
   ```

4. Enable remote access (if needed):
   - Edit `pg_hba.conf` in PostgreSQL data directory
   - Add: `host all all 192.168.1.0/24 md5` (adjust subnet to match network)
   - Edit `postgresql.conf` to set `listen_addresses = '*'`
   - Restart PostgreSQL service

### PostgreSQL Installation (Linux)

1. Install PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo apt install -y postgresql postgresql-contrib

   # CentOS/RHEL
   sudo yum install -y postgresql-server postgresql-contrib
   sudo postgresql-setup --initdb
   sudo systemctl enable postgresql
   sudo systemctl start postgresql
   ```

2. Create database and user:
   ```bash
   sudo -u postgres psql -c "CREATE USER sgk_user WITH PASSWORD 'secure_password';"
   sudo -u postgres psql -c "CREATE DATABASE sgk_export OWNER sgk_user;"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sgk_export TO sgk_user;"
   ```

## Storage Configuration

The SGK Export System requires storage for uploaded files. Choose one of the following options:

### Local Storage

For single-server deployments without shared access requirements:

1. Create a dedicated directory:
   ```bash
   # Windows
   mkdir C:\sgk_export\file_storage
   
   # Linux
   sudo mkdir -p /opt/sgk_export/file_storage
   sudo chown <app_user>:<app_group> /opt/sgk_export/file_storage
   ```

2. Set appropriate permissions:
   ```bash
   # Windows - Use File Explorer to grant permissions to app service account
   
   # Linux
   sudo chmod 755 /opt/sgk_export/file_storage
   ```

### NAS Configuration

For multi-user environments with shared file access:

#### NAS Device Setup

1. Configure your NAS according to manufacturer instructions
2. Create a dedicated share called `sgk_export_share`
3. Create a subfolder called `uploads` inside the share
4. Configure permissions:
   - Grant read/write access to the service account running the application
   - Consider creating a dedicated user account for the application
   
#### Mounting NAS on Windows

1. Map network drive:
   ```
   # Open File Explorer
   # Right-click "This PC" → "Map network drive..."
   # Drive: S:
   # Folder: \\NAS-IP-ADDRESS\sgk_export_share
   # Check "Reconnect at sign-in"
   # Check "Connect using different credentials" if needed
   ```

2. Verify the connection:
   ```
   dir S:\uploads
   ```

3. Configure to automatically reconnect at startup:
   ```
   # Create a script in Startup folder or use Task Scheduler
   net use S: \\NAS-IP-ADDRESS\sgk_export_share /persistent:yes
   ```

#### Mounting NAS on Linux

1. Install NFS or CIFS support:
   ```bash
   # For NFS
   sudo apt install -y nfs-common    # Ubuntu/Debian
   sudo yum install -y nfs-utils     # CentOS/RHEL
   
   # For CIFS (SMB)
   sudo apt install -y cifs-utils    # Ubuntu/Debian
   sudo yum install -y cifs-utils    # CentOS/RHEL
   ```

2. Create mount point:
   ```bash
   sudo mkdir -p /mnt/sgk_export_share
   ```

3. Mount the share:
   ```bash
   # For NFS
   sudo mount -t nfs NAS-IP-ADDRESS:/sgk_export_share /mnt/sgk_export_share
   
   # For CIFS (SMB)
   sudo mount -t cifs //NAS-IP-ADDRESS/sgk_export_share /mnt/sgk_export_share -o username=USER,password=PASSWORD
   ```

4. Configure auto-mount at boot:
   ```bash
   # Edit /etc/fstab and add:
   
   # For NFS
   NAS-IP-ADDRESS:/sgk_export_share /mnt/sgk_export_share nfs defaults 0 0
   
   # For CIFS (SMB)
   //NAS-IP-ADDRESS/sgk_export_share /mnt/sgk_export_share cifs username=USER,password=PASSWORD,iocharset=utf8,file_mode=0777,dir_mode=0777 0 0
   ```

### Cloud Storage

For cloud deployments, consider using object storage:
- AWS S3
- Azure Blob Storage
- Google Cloud Storage

Implementation details are available in the [Cloud Deployment](#cloud-deployment-detailed) section.

## Application Installation

### Downloading the Application

1. Create application directory:
   ```bash
   # Windows
   mkdir C:\sgk_export
   cd C:\sgk_export
   
   # Linux
   sudo mkdir -p /opt/sgk_export
   sudo chown $USER:$USER /opt/sgk_export
   cd /opt/sgk_export
   ```

2. Clone the repository:
   ```bash
   # Clone the repository with the local-file-storage branch (recommended for office deployments)
   git clone --branch local-file-storage <repository-url> .
   # OR download and extract the application archive
   ```

   Note: The **local-file-storage** branch is specifically designed for office deployments
   with local or NAS file storage options and should be used instead of the main branch.

### Setting Up Python Virtual Environment

1. Create and activate virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```bash
   python -c "import flask; print(flask.__version__)"
   ```

### Initial Database Setup

Initialize the database schema:

```bash
# With virtual environment activated
flask db upgrade
```

## Configuration

### Environment Variables

Create a `.env` file in the application root:

```
# Windows path: C:\sgk_export\.env
# Linux path: /opt/sgk_export/.env

# Application configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=<generate-secure-random-key>

# Database configuration
DATABASE_URL=postgresql://sgk_user:secure_password@localhost/sgk_export

# Storage configuration
# For local storage:
USE_NAS_STORAGE=false
UPLOAD_FOLDER=C:\sgk_export\file_storage  # Windows
UPLOAD_FOLDER=/opt/sgk_export/file_storage  # Linux

# For NAS storage:
USE_NAS_STORAGE=true
NAS_UPLOAD_FOLDER=S:\uploads  # Windows
NAS_UPLOAD_FOLDER=/mnt/sgk_export_share/uploads  # Linux

# Logging configuration
GUNICORN_LOG_LEVEL=info  # Options: debug, info, warning, error
```

Generate a secure random key:
```bash
# Windows/Linux with Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Web Server Configuration

#### Nginx Configuration (Linux)

1. Install Nginx:
   ```bash
   # Ubuntu/Debian
   sudo apt install -y nginx
   
   # CentOS/RHEL
   sudo yum install -y nginx
   ```

2. Create Nginx configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/sgk_export
   ```

   Add this content:
   ```nginx
   server {
       listen 80;
       server_name sgk-export.local;  # Replace with your domain or server IP
       
       access_log /var/log/nginx/sgk_export_access.log;
       error_log /var/log/nginx/sgk_export_error.log;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

3. Enable the configuration:
   ```bash
   sudo ln -s /etc/nginx/sites-available/sgk_export /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

#### IIS Configuration (Windows)

For Windows servers, Internet Information Services (IIS) can be used:

1. Install IIS with URL Rewrite Module
2. Install the ASP.NET Core Hosting Bundle
3. Create a new website in IIS, pointing to the application directory
4. Create web.config file for URL rewriting to the Python application

## Service Setup

### Windows Service Setup

1. Install required package:
   ```bash
   pip install pywin32
   ```

2. Create service script `C:\sgk_export\gunicorn_service.py`:
   ```python
   import win32serviceutil
   import win32service
   import win32event
   import servicemanager
   import socket
   import sys
   import os
   import subprocess

   class SGKExportService(win32serviceutil.ServiceFramework):
       _svc_name_ = "SGKExportService"
       _svc_display_name_ = "SGK Export Service"
       _svc_description_ = "Runs the SGK Export application using Gunicorn"

       def __init__(self, args):
           win32serviceutil.ServiceFramework.__init__(self, args)
           self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
           socket.setdefaulttimeout(60)
           self.is_running = False

       def SvcStop(self):
           self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
           win32event.SetEvent(self.hWaitStop)
           self.is_running = False

       def SvcDoRun(self):
           servicemanager.LogMsg(
               servicemanager.EVENTLOG_INFORMATION_TYPE,
               servicemanager.PYS_SERVICE_STARTED,
               (self._svc_name_, '')
           )
           self.is_running = True
           self.main()

       def main(self):
           app_dir = r'C:\sgk_export'
           os.chdir(app_dir)
           
           # Set environment variables
           with open(os.path.join(app_dir, '.env'), 'r') as f:
               for line in f:
                   line = line.strip()
                   if line and not line.startswith('#') and '=' in line:
                       key, value = line.split('=', 1)
                       os.environ[key] = value
           
           # Start Gunicorn
           cmd = [
               r'C:\sgk_export\venv\Scripts\python.exe',
               r'C:\sgk_export\venv\Scripts\gunicorn',
               '-c', 'gunicorn.conf.py', 
               'wsgi:app'
           ]
           process = subprocess.Popen(cmd)
           
           # Wait for service stop signal
           while self.is_running:
               rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
               if rc == win32event.WAIT_OBJECT_0:
                   # Stop Gunicorn
                   process.terminate()
                   break

   if __name__ == '__main__':
       if len(sys.argv) == 1:
           servicemanager.Initialize()
           servicemanager.PrepareToHostSingle(SGKExportService)
           servicemanager.StartServiceCtrlDispatcher()
       else:
           win32serviceutil.HandleCommandLine(SGKExportService)
   ```

3. Install the service:
   ```bash
   python gunicorn_service.py install
   ```

4. Configure service recovery options:
   ```
   # Open Services app (services.msc)
   # Find SGKExportService
   # Right-click -> Properties -> Recovery tab
   # First failure: Restart the Service
   # Second failure: Restart the Service
   # Subsequent failures: Restart the Service
   # Reset fail count after: 1 day
   ```

5. Start the service:
   ```bash
   net start SGKExportService
   ```

### Linux Systemd Service

1. Create systemd service file:
   ```bash
   sudo nano /etc/systemd/system/sgk_export.service
   ```

   Add this content:
   ```ini
   [Unit]
   Description=SGK Export Application
   After=network.target postgresql.service

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/sgk_export
   Environment="PATH=/opt/sgk_export/venv/bin"
   EnvironmentFile=/opt/sgk_export/.env
   ExecStart=/opt/sgk_export/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
   Restart=always
   RestartSec=5
   
   [Install]
   WantedBy=multi-user.target
   ```

2. Set appropriate permissions:
   ```bash
   sudo chown -R www-data:www-data /opt/sgk_export
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sgk_export
   sudo systemctl start sgk_export
   ```

4. Check service status:
   ```bash
   sudo systemctl status sgk_export
   ```

## Security Hardening

### File System Permissions

1. Restrict sensitive files:
   ```bash
   # Windows
   icacls C:\sgk_export\.env /inheritance:r /grant:r "SYSTEM:(R)" /grant:r "Administrators:(F)" /grant:r "SERVICE_ACCOUNT:(R)"
   
   # Linux
   sudo chmod 640 /opt/sgk_export/.env
   sudo chown www-data:www-data /opt/sgk_export/.env
   ```

### Firewall Configuration

#### Windows Firewall

1. Allow required ports:
   ```
   netsh advfirewall firewall add rule name="SGK Export Web" dir=in action=allow protocol=TCP localport=80,443,8000
   ```

#### Linux Firewall (UFW)

1. Configure UFW:
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

### HTTPS Configuration

For production environments, HTTPS is strongly recommended:

#### Self-signed Certificate (Development)

```bash
# Windows (using OpenSSL)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Linux
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/sgk-cert.key -out /etc/ssl/certs/sgk-cert.crt
```

#### Let's Encrypt (Production)

For public-facing deployments, use Let's Encrypt:

```bash
# Linux with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring & Logging

### Log Files

Key log files to monitor:

- Application logs: 
  - `logs/error.log`
  - `logs/access.log`
- Web server logs:
  - Nginx: `/var/log/nginx/`
  - IIS: `C:\inetpub\logs\LogFiles\`
- Database logs:
  - PostgreSQL: `/var/log/postgresql/` (Linux)
  - PostgreSQL: `C:\Program Files\PostgreSQL\13\data\log\` (Windows)

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Linux
sudo nano /etc/logrotate.d/sgk_export
```

Add:
```
/opt/sgk_export/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload sgk_export
    endscript
}
```

### Process Monitoring

For production environments, consider adding:

- Prometheus for metrics collection
- Grafana for visualization
- Node exporter for system metrics
- PostgreSQL exporter for database metrics

## Backup & Recovery

### Database Backup

#### Automated PostgreSQL Backup (Windows)

1. Create backup script `C:\sgk_export\scripts\backup.bat`:
   ```batch
   @echo off
   set PGPASSWORD=your_password
   set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%
   set BACKUP_DIR=C:\backups
   
   mkdir %BACKUP_DIR%\%TIMESTAMP%
   
   pg_dump -h localhost -U postgres -F c -b -v -f "%BACKUP_DIR%\%TIMESTAMP%\sgk_export.backup" sgk_export
   
   forfiles /p %BACKUP_DIR% /d -30 /c "cmd /c if @isdir==TRUE rd /s /q @path"
   ```

2. Add to Task Scheduler:
   - Open Task Scheduler
   - Create a new task to run daily
   - Action: Start a program
   - Program: `C:\sgk_export\scripts\backup.bat`

#### Automated PostgreSQL Backup (Linux)

1. Create backup script:
   ```bash
   sudo nano /opt/sgk_export/scripts/backup.sh
   ```

   Add:
   ```bash
   #!/bin/bash
   TIMESTAMP=$(date +%Y%m%d)
   BACKUP_DIR=/var/backups/sgk_export
   
   mkdir -p $BACKUP_DIR/$TIMESTAMP
   
   export PGPASSWORD=your_password
   pg_dump -h localhost -U postgres -F c -b -v -f "$BACKUP_DIR/$TIMESTAMP/sgk_export.backup" sgk_export
   
   # Remove backups older than 30 days
   find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
   ```

2. Make executable and add to crontab:
   ```bash
   sudo chmod +x /opt/sgk_export/scripts/backup.sh
   sudo crontab -e
   ```

   Add:
   ```
   0 1 * * * /opt/sgk_export/scripts/backup.sh
   ```

### File Backup Strategy

1. Regular backups of:
   - Application code
   - Uploaded files
   - Configuration files
   - Database

2. Offsite backup strategy:
   - Regular copies to external drive
   - Cloud backup (AWS S3, Azure, etc.)
   - Separate NAS device in different location

## Accessing the Application

### Local Network Access

1. From any computer on the local network:
   - Open web browser
   - Navigate to `http://server-ip-address` or the configured domain name

### DNS Configuration (Optional)

For easier access, set up DNS:

1. **Windows Server DNS**:
   - Open DNS Manager
   - Add a new A record for sgk-export.local pointing to server IP

2. **Linux Bind DNS**:
   - Configure a DNS zone for local network
   - Add A record for the application

3. Alternatively, edit hosts files on client machines:
   - Windows: `C:\Windows\System32\drivers\etc\hosts`
   - Linux: `/etc/hosts`
   - Add: `192.168.1.x  sgk-export.local`

## Upgrading & Maintenance

### Application Updates

1. Backup first:
   ```bash
   # Backup database
   # Backup code and configuration
   ```

2. Pull latest code:
   ```bash
   cd /opt/sgk_export  # Linux
   cd C:\sgk_export    # Windows
   
   git pull  # If installed from git
   # OR extract updated application files
   ```

3. Update dependencies:
   ```bash
   # Activate virtual environment
   pip install -r requirements.txt
   ```

4. Database migrations:
   ```bash
   flask db upgrade
   ```

5. Restart services:
   ```bash
   # Windows
   net stop SGKExportService
   net start SGKExportService
   
   # Linux
   sudo systemctl restart sgk_export
   ```

### Security Updates

Regularly update system components:

- Operating system updates
- Database server updates
- Web server updates
- Python and dependency updates

## Troubleshooting

### Common Issues and Solutions

#### Application Not Starting

1. Check logs:
   ```bash
   # Check application logs
   cat logs/error.log
   
   # Check service logs
   # Windows
   sc query SGKExportService
   
   # Linux
   sudo journalctl -u sgk_export
   ```

2. Verify database connection:
   ```bash
   # Test PostgreSQL connection
   psql -U sgk_user -h localhost -d sgk_export
   ```

3. Check Python environment:
   ```bash
   # Windows
   venv\Scripts\python -c "import sys; print(sys.executable)"
   
   # Linux
   venv/bin/python -c "import sys; print(sys.executable)"
   ```

#### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   # Windows
   sc query postgresql-x64-13
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Check database credentials:
   - Verify `.env` file has correct DATABASE_URL
   - Test connection with psql client

3. Check network/firewall:
   ```bash
   # Windows
   netstat -a | findstr 5432
   
   # Linux
   sudo netstat -tulpn | grep postgres
   ```

#### Storage Access Issues

1. For NAS storage:
   ```bash
   # Windows
   dir S:\uploads
   
   # Linux
   ls -la /mnt/sgk_export_share/uploads
   ```

2. Check permissions:
   ```bash
   # Windows
   icacls S:\uploads
   
   # Linux
   ls -la /mnt/sgk_export_share/uploads
   ```

3. Verify file storage configuration in the `.env` file:
   ```bash
   # If using local storage, ensure these are set correctly:
   USE_NAS_STORAGE=false
   UPLOAD_FOLDER=C:\sgk_export\file_storage  # Windows
   UPLOAD_FOLDER=/opt/sgk_export/file_storage  # Linux
   
   # If using NAS storage, ensure these are set correctly:
   USE_NAS_STORAGE=true
   NAS_UPLOAD_FOLDER=S:\uploads  # Windows
   NAS_UPLOAD_FOLDER=/mnt/sgk_export_share/uploads  # Linux
   ```

4. Test file upload functionality:
   ```bash
   # With the virtual environment activated
   python -c "from app import create_app; from app.utils.file_storage import upload_file; app = create_app(); app.app_context().push(); result = upload_file(b'test data', 'test.txt'); print(f'Upload test result: {result}')"
   ```
   If successful, this will output a UUID. Otherwise, check the app logs for errors.

#### Web Server Issues

1. Check if server is running:
   ```bash
   # Windows (IIS)
   iisreset /status
   
   # Linux (Nginx)
   sudo systemctl status nginx
   ```

2. Test internal service:
   ```bash
   curl http://localhost:8000/
   ```

### Diagnostic Commands

```bash
# Check disk space
df -h                # Linux
Get-PSDrive          # Windows PowerShell

# Check memory usage
free -m              # Linux
Get-Process          # Windows PowerShell

# Check open files and connections
lsof                 # Linux
netstat -ano         # Windows
```

## Cloud Deployment Detailed

### AWS Deployment

1. Launch EC2 instance (t3.small or larger)
2. Set up RDS PostgreSQL instance
3. Configure Security Groups
4. Set up S3 bucket for file storage
5. Deploy application using Elastic Beanstalk or directly on EC2

### Render.com Deployment

1. Create a new Web Service
2. Link to GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn wsgi:app`
5. Add environment variables from `.env` file
6. Create PostgreSQL database
7. Use Render Disk or connect to cloud storage

---

## Appendix

### Version History

| Version | Date       | Changes                           |
|---------|------------|-----------------------------------|
| 1.0     | 2023-05-01 | Initial deployment guide          |
| 1.1     | 2023-06-15 | Added Linux deployment            |
| 2.0     | 2023-12-10 | Comprehensive rewrite with cloud  |

### Quick Reference Commands

#### Windows
```powershell
# Start application service
net start SGKExportService

# Stop application service
net stop SGKExportService

# Check service status
sc query SGKExportService

# Database backup
pg_dump -U postgres -F c -f "C:\backups\sgk_export.backup" sgk_export
```

#### Linux
```bash
# Start application service
sudo systemctl start sgk_export

# Stop application service
sudo systemctl stop sgk_export

# View logs
sudo journalctl -u sgk_export

# Database backup
pg_dump -U postgres -F c -f "/var/backups/sgk_export.backup" sgk_export
```

### Architecture Diagram

```
┌───────────────┐       ┌───────────────┐
│  Web Browser  │───────│  Load Balancer│ (optional)
└───────────────┘       └───────┬───────┘
                                │
                                ▼
┌───────────────────────────────────────────────┐
│               Application Server              │
│  ┌────────────┐       ┌─────────────────┐    │
│  │ Web Server │◄─────►│ Gunicorn/Flask  │    │
│  │(Nginx/IIS) │       └────────┬────────┘    │
│  └────────────┘                │             │
└──────────────────────┬─────────┼─────────────┘
                       │         │
                       ▼         ▼
      ┌───────────────────┐    ┌─────────────────────┐
      │  PostgreSQL DB    │    │ File Storage        │
      │  ┌─────────────┐  │    │ ┌─────────────────┐ │
      │  │ sgk_export  │  │    │ │ Uploaded Files  │ │
      │  └─────────────┘  │    │ └─────────────────┘ │
      └───────────────────┘    └─────────────────────┘
       (local or remote)        (local, NAS or cloud)
``` 