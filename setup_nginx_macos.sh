#!/bin/bash

# Script to set up nginx for SGK Export on macOS

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo privileges"
  exit 1
fi

# Check if brew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Please install it first."
    echo "Run this command: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Check if nginx is installed
if ! brew list nginx &> /dev/null; then
    echo "Installing nginx..."
    brew install nginx
else
    echo "nginx is already installed"
fi

# Create log directories if they don't exist
if [ ! -d "/usr/local/var/log/nginx" ]; then
    echo "Creating nginx log directories..."
    mkdir -p /usr/local/var/log/nginx
fi

# Create empty log files if they don't exist
if [ ! -f "/usr/local/var/log/nginx/sgk_export_access.log" ]; then
    touch /usr/local/var/log/nginx/sgk_export_access.log
fi

if [ ! -f "/usr/local/var/log/nginx/sgk_export_error.log" ]; then
    touch /usr/local/var/log/nginx/sgk_export_error.log
fi

# Get the current directory
CURRENT_DIR=$(pwd)

# Copy the nginx config file
echo "Copying nginx configuration..."
cp ${CURRENT_DIR}/conf/nginx/sgk_export_macos.conf /usr/local/etc/nginx/servers/sgk_export.conf

# Check if the configuration is valid
echo "Checking nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration is valid. Restarting nginx..."
    brew services restart nginx
    echo "nginx has been configured and restarted successfully!"
    echo "Your application should now be accessible at: http://localhost:8080"
else
    echo "nginx configuration test failed. Please check the error message above."
    exit 1
fi

echo "Done!" 