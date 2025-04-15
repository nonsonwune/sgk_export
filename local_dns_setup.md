# Local DNS Setup Guide for SGK Export Application

This guide explains how to set up local DNS on both macOS and Windows so that the SGK Export application can be accessed using `http://sgk-export.local` without specifying a port number.

## Prerequisites

- Administrator/sudo access on your computer
- The application server running on the host machine
- Knowledge of your machine's IP address on the local network
- Nginx installed on the host machine

## Finding Your Local IP Address

### macOS
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Windows
```
ipconfig | findstr /i "IPv4"
```

## macOS Setup

### Option 1: Using dnsmasq (Recommended)

1. **Install dnsmasq using Homebrew:**
   ```bash
   brew install dnsmasq
   ```

2. **Configure dnsmasq:**
   ```bash
   # Create config directory if it doesn't exist
   mkdir -p $(brew --prefix)/etc/
   
   # Configure dnsmasq to resolve sgk-export.local to your IP
   echo 'address=/sgk-export.local/192.168.1.X' > $(brew --prefix)/etc/dnsmasq.conf
   ```
   (Replace 192.168.1.X with your actual IP address)

3. **Start dnsmasq service:**
   ```bash
   sudo brew services start dnsmasq
   ```

4. **Configure macOS to use your local DNS:**
   ```bash
   sudo mkdir -p /etc/resolver
   echo 'nameserver 127.0.0.1' | sudo tee /etc/resolver/local
   ```

5. **Modify nginx to use port 80:**
   ```bash
   sudo nano /usr/local/etc/nginx/servers/sgk_export.conf
   ```
   
   Change these lines:
   ```
   listen 8080;
   server_name localhost;
   ```

   To:
   ```
   listen 80;
   server_name sgk-export.local;
   ```

6. **Grant nginx permission to use port 80:**
   ```bash
   sudo chown root:wheel /usr/local/opt/nginx/bin/nginx
   sudo chmod u+s /usr/local/opt/nginx/bin/nginx
   ```

7. **Test and restart nginx:**
   ```bash
   sudo nginx -t
   sudo brew services restart nginx
   ```

### Option 2: Using Port Forwarding (Alternative)

If you prefer to keep nginx running on port 8080, you can use port forwarding:

1. **Set up port forwarding from port 80 to 8080:**
   ```bash
   echo "
   rdr pass inet proto tcp from any to any port 80 -> 127.0.0.1 port 8080
   " | sudo pfctl -ef -
   ```

2. **Add hosts entry:**
   ```bash
   sudo nano /etc/hosts
   ```
   
   Add this line:
   ```
   192.168.1.X sgk-export.local
   ```
   (Replace 192.168.1.X with your actual IP address)

## Windows Setup

### Option 1: Using Acrylic DNS Proxy (Recommended)

1. **Download and install Acrylic DNS Proxy:**
   - Download from [Acrylic DNS Proxy website](https://mayakron.altervista.org/support/acrylic/Home.htm)
   - Run the installer with administrator privileges

2. **Configure Acrylic:**
   - Open `C:\Program Files (x86)\Acrylic DNS Proxy\AcrylicHosts.txt`
   - Add the following line:
     ```
     192.168.1.X sgk-export.local
     ```
     (Replace 192.168.1.X with your actual IP address)

3. **Set Windows to use the local DNS server:**
   - Open Control Panel > Network and Internet > Network and Sharing Center
   - Click on your active network connection > Properties
   - Select "Internet Protocol Version 4 (TCP/IPv4)" > Properties
   - Select "Use the following DNS server addresses"
   - Set "Preferred DNS server" to `127.0.0.1`
   - Click OK to save changes

4. **Restart Acrylic DNS service:**
   - Open Services (Win+R, type `services.msc`)
   - Find "Acrylic DNS Proxy"
   - Right-click and select "Restart"

### Option 2: Using hosts file only

1. **Edit the hosts file:**
   - Open Notepad as Administrator
   - Open the file `C:\Windows\System32\drivers\etc\hosts`
   - Add the following line:
     ```
     192.168.1.X sgk-export.local
     ```
     (Replace 192.168.1.X with your actual IP address)
   - Save the file

2. **Flush DNS cache:**
   ```
   ipconfig /flushdns
   ```

## Setting Up Nginx on the Host Server

Regardless of which OS you're using for the host server, configure nginx to listen on port 80:

1. **Edit the nginx configuration file:**
   ```bash
   # For macOS
   sudo nano /usr/local/etc/nginx/servers/sgk_export.conf
   
   # For Linux
   sudo nano /etc/nginx/sites-available/sgk_export
   ```

2. **Update the listening port and server name:**
   ```
   listen 80;
   server_name sgk-export.local;
   ```

3. **Test and restart nginx:**
   ```bash
   # Test configuration
   sudo nginx -t
   
   # For macOS
   sudo brew services restart nginx
   
   # For Linux
   sudo systemctl restart nginx
   ```

## For Client Devices on the Network

For other devices on your network to use your DNS setup:

### Method 1: Configure each device's DNS server

Set the primary DNS server on each device to point to your host machine's IP address.

### Method 2: Configure your router (Best for entire network)

If you have access to your router settings:

1. Access your router's admin interface
2. Find DNS settings
3. Add a custom DNS entry mapping `sgk-export.local` to your host machine's IP
4. Save settings and restart router if required

## Troubleshooting

### Cannot access the site
- Check that nginx is running: `ps aux | grep nginx`
- Verify that port 80 is open: `sudo lsof -i :80`
- Check the nginx error logs:
  - macOS: `/usr/local/var/log/nginx/error.log`
  - Linux: `/var/log/nginx/error.log`

### DNS not resolving
- Test DNS resolution: `nslookup sgk-export.local`
- Flush DNS cache:
  - macOS: `sudo killall -HUP mDNSResponder`
  - Windows: `ipconfig /flushdns`
  
### Port 80 already in use
- Find what's using the port: 
  - macOS/Linux: `sudo lsof -i :80`
  - Windows: `netstat -ano | findstr :80`
- Stop the service or configure nginx to use a different port and set up port forwarding

## Security Considerations

This setup is intended for local office use only. For production or public-facing deployments:

- Use proper SSL certificates
- Consider more robust DNS and firewall configurations
- Follow security best practices for web server hardening 