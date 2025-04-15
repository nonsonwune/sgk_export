# Nginx Configuration for SGK Export Application

This directory contains Nginx configuration files for the SGK Export application, optimized for Progressive Web App (PWA) features.

## Configuration Files

- `sgk_export.conf`: General configuration for Linux/Unix servers
- `sgk_export_macos.conf`: Specific configuration for macOS with Homebrew paths

## Features

These configurations include:

- **PWA optimization**: Special cache control headers for service worker and manifest files
- **Security headers**: Content-Security-Policy, X-Frame-Options, etc.
- **Performance optimization**: Gzip compression, cache control for static assets
- **Proxy settings**: Forwarding requests to the application server

## Setup Instructions

### macOS Setup

1. Install Nginx using Homebrew:
   ```
   brew install nginx
   ```

2. Run the setup script (from the project root directory):
   ```
   sudo ./setup_nginx_macos.sh
   ```

3. Or manually copy the configuration:
   ```
   cp conf/nginx/sgk_export_macos.conf /usr/local/etc/nginx/servers/
   ```

4. Test the configuration:
   ```
   nginx -t
   ```

5. Restart Nginx:
   ```
   brew services restart nginx
   ```

### Linux Setup

1. Install Nginx:
   ```
   # Ubuntu/Debian
   sudo apt install -y nginx
   
   # CentOS/RHEL
   sudo yum install -y nginx
   ```

2. Copy the configuration file:
   ```
   sudo cp conf/nginx/sgk_export.conf /etc/nginx/sites-available/sgk_export
   ```

3. Create a symbolic link:
   ```
   sudo ln -s /etc/nginx/sites-available/sgk_export /etc/nginx/sites-enabled/
   ```

4. Update paths in the configuration file:
   ```
   sudo nano /etc/nginx/sites-available/sgk_export
   ```
   Replace `/path/to/app/` with the actual path to your application.

5. Test the configuration:
   ```
   sudo nginx -t
   ```

6. Restart Nginx:
   ```
   sudo systemctl restart nginx
   ```

## Verification

After setting up Nginx, you can verify that it's working correctly:

1. Open your browser and navigate to the appropriate URL:
   - macOS: `http://localhost:8080`
   - Linux: `http://your-server-ip` or `http://your-domain.com`

2. Verify that the PWA features are working:
   - Check if the manifest and service worker are being loaded correctly
   - Check if you can install the application as a PWA
   - Test offline functionality

## Troubleshooting

If you encounter issues with the Nginx configuration:

1. Check the Nginx error logs:
   - macOS: `/usr/local/var/log/nginx/error.log` and `/usr/local/var/log/nginx/sgk_export_error.log`
   - Linux: `/var/log/nginx/error.log` and `/var/log/nginx/sgk_export_error.log`

2. Ensure the application server is running on the expected port (default: 8000).

3. Verify file permissions if you're seeing 403 Forbidden errors.

4. If you make changes to the configuration, remember to reload or restart Nginx. 