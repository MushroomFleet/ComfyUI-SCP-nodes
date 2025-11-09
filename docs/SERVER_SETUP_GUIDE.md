# Server Setup Guide for SaveImageSCP
## Ubuntu Apache2 Server Configuration

This guide provides step-by-step instructions for system administrators to configure an Ubuntu Apache2 web server to receive image uploads from the ComfyUI SaveImageSCP custom node.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [User Account Setup](#user-account-setup)
4. [Directory Structure](#directory-structure)
5. [File Permissions & Ownership](#file-permissions--ownership)
6. [Apache Configuration](#apache-configuration)
7. [SSH Security Hardening](#ssh-security-hardening)
8. [Testing & Verification](#testing--verification)
9. [Maintenance & Best Practices](#maintenance--best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The SaveImageSCP node uploads generated images via SCP/SFTP to predefined directories on your Apache2 web server. This guide ensures:

- Secure user authentication
- Proper file permissions for Apache serving
- Isolated upload directories
- Security best practices

**Time Required:** 20-30 minutes  
**Skill Level:** Intermediate Linux administration

---

## Prerequisites

- Ubuntu Server 20.04 LTS or newer
- Apache2 installed and running
- SSH server (OpenSSH) installed
- Root or sudo access
- Basic knowledge of Linux command line

Verify Apache is running:
```bash
sudo systemctl status apache2
```

Verify SSH is running:
```bash
sudo systemctl status ssh
```

---

## User Account Setup

### Step 1: Create the SCPuser Account

Create a dedicated system user for SCP uploads:

```bash
sudo adduser --system --group --home /home/SCPuser --shell /bin/bash SCPuser
```

**Explanation:**
- `--system`: Creates a system user (UID < 1000)
- `--group`: Creates a group with the same name
- `--home /home/SCPuser`: Sets home directory
- `--shell /bin/bash`: Allows SSH access

**Alternative** (for non-system user):
```bash
sudo adduser SCPuser
```
This will prompt for password and user details interactively.

### Step 2: Set a Strong Password

Set a secure password for the account:

```bash
sudo passwd SCPuser
```

**Password Requirements:**
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, and symbols
- Example: `SCP#Upload2024!Secure@Images`

**Security Note:** For production environments, SSH key authentication is strongly recommended over password authentication (see Section 7).

### Step 3: Add SCPuser to www-data Group

This allows uploaded files to be readable by Apache:

```bash
sudo usermod -aG www-data SCPuser
```

Verify group membership:
```bash
groups SCPuser
```

Expected output: `SCPuser : SCPuser www-data`

### Step 4: Configure User's Home Directory

Set proper permissions on home directory:

```bash
sudo chmod 755 /home/SCPuser
sudo chown SCPuser:SCPuser /home/SCPuser
```

---

## Directory Structure

### Step 5: Create Upload Directories

Based on the default `config.json` profiles, create the following directories:

```bash
# Default profile directory
sudo mkdir -p /var/www/html/images

# Production profile directory
sudo mkdir -p /var/www/production/gallery

# Testing profile directory (optional)
sudo mkdir -p /tmp/comfyui/test

# Portfolio profile directory (optional)
sudo mkdir -p /home/SCPuser/portfolio/images

# Backup profile directory (optional)
sudo mkdir -p /mnt/backup/images
```

**Note:** Adjust paths based on your specific `config.json` configuration.

### Step 6: Set Directory Ownership

Set SCPuser as owner with www-data group:

```bash
# For web-accessible directories
sudo chown -R SCPuser:www-data /var/www/html/images
sudo chown -R SCPuser:www-data /var/www/production/gallery

# For user-specific directories
sudo chown -R SCPuser:SCPuser /home/SCPuser/portfolio/images

# For temporary/testing
sudo chown -R SCPuser:SCPuser /tmp/comfyui/test

# For backup (adjust based on backup location requirements)
sudo chown -R SCPuser:www-data /mnt/backup/images
```

### Step 7: Set Directory Permissions

Apply proper permissions to allow uploads and web serving:

```bash
# Web-accessible directories: SCPuser can write, Apache can read
sudo chmod 775 /var/www/html/images
sudo chmod 775 /var/www/production/gallery

# User-specific directories
sudo chmod 755 /home/SCPuser/portfolio/images

# Testing directory
sudo chmod 755 /tmp/comfyui/test

# Backup directory
sudo chmod 775 /mnt/backup/images
```

**Permission Breakdown:**
- `7` (owner/SCPuser): Read, write, execute
- `7` (group/www-data): Read, write, execute
- `5` (others): Read, execute

---

## File Permissions & Ownership

### Step 8: Configure Default File Permissions with ACLs

Set default ACLs to ensure new files have correct permissions:

```bash
# Install ACL tools if not present
sudo apt-get update
sudo apt-get install acl -y

# Set default ACLs for web directories
sudo setfacl -d -m u::rwx /var/www/html/images
sudo setfacl -d -m g::rwx /var/www/html/images
sudo setfacl -d -m o::r-x /var/www/html/images

sudo setfacl -d -m u::rwx /var/www/production/gallery
sudo setfacl -d -m g::rwx /var/www/production/gallery
sudo setfacl -d -m o::r-x /var/www/production/gallery
```

**Explanation:**
- `-d`: Sets default ACL (affects new files/directories)
- `-m u::rwx`: User gets read, write, execute
- `-m g::rwx`: Group gets read, write, execute
- `-m o::r-x`: Others get read, execute only

Verify ACLs:
```bash
getfacl /var/www/html/images
```

### Step 9: Set Umask for SCPuser (Optional)

Configure umask in SCPuser's profile to ensure uploaded files have correct permissions:

```bash
sudo -u SCPuser bash -c 'echo "umask 002" >> /home/SCPuser/.bashrc'
```

**Umask 002** means:
- Files created: 664 (rw-rw-r--)
- Directories created: 775 (rwxrwxr-x)

---

## Apache Configuration

### Step 10: Configure Apache Directory Directives

Create a configuration file for the image directories:

```bash
sudo nano /etc/apache2/conf-available/comfyui-images.conf
```

Add the following configuration:

```apache
# ComfyUI SaveImageSCP Directory Configuration

<Directory /var/www/html/images>
    Options -Indexes +FollowSymLinks
    AllowOverride None
    Require all granted
    
    # Security: Prevent PHP execution
    <FilesMatch "\.php$">
        Require all denied
    </FilesMatch>
    
    # Only allow image files
    <FilesMatch "\.(jpg|jpeg|png|gif|webp|svg)$">
        Require all granted
    </FilesMatch>
</Directory>

<Directory /var/www/production/gallery>
    Options -Indexes +FollowSymLinks
    AllowOverride None
    Require all granted
    
    # Security: Prevent PHP execution
    <FilesMatch "\.php$">
        Require all denied
    </FilesMatch>
    
    # Only allow image files
    <FilesMatch "\.(jpg|jpeg|png|gif|webp|svg)$">
        Require all granted
    </FilesMatch>
    
    # Optional: CORS headers for external access
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, OPTIONS"
</Directory>
```

**Security Features:**
- `-Indexes`: Prevents directory listing
- `+FollowSymLinks`: Allows symbolic links
- Blocks PHP execution to prevent uploaded script execution
- Restricts access to image file types only
- Optional CORS headers for cross-origin requests

### Step 11: Enable Configuration and Required Modules

```bash
# Enable headers module (for CORS)
sudo a2enmod headers

# Enable the configuration
sudo a2enconf comfyui-images

# Test Apache configuration
sudo apache2ctl configtest
```

Expected output: `Syntax OK`

### Step 12: Restart Apache

```bash
sudo systemctl restart apache2
```

Verify Apache is running:
```bash
sudo systemctl status apache2
```

---

## SSH Security Hardening

### Step 13: Configure SSH Key Authentication (Recommended)

**On the ComfyUI client machine**, generate SSH key pair:

```bash
ssh-keygen -t ed25519 -C "comfyui-scp-upload"
```

Save to: `/home/user/.ssh/comfyui_scp_key`

**Copy public key to server:**

```bash
ssh-copy-id -i ~/.ssh/comfyui_scp_key.pub SCPuser@your.server.com
```

**On the server**, verify key was added:

```bash
sudo cat /home/SCPuser/.ssh/authorized_keys
```

### Step 14: Restrict SCPuser SSH Access (Optional)

For enhanced security, restrict SCPuser to SFTP only:

```bash
sudo nano /etc/ssh/sshd_config
```

Add at the end:

```bash
# Restrict SCPuser to SFTP only
Match User SCPuser
    ForceCommand internal-sftp
    ChrootDirectory /home/SCPuser
    PermitTunnel no
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
```

**Important:** If using chroot, the directory structure must be owned by root:

```bash
sudo chown root:root /home/SCPuser
sudo chmod 755 /home/SCPuser

# Create upload directory within chroot
sudo mkdir -p /home/SCPuser/uploads
sudo chown SCPuser:SCPuser /home/SCPuser/uploads
```

**Then update `config.json` paths** to use: `/uploads/` instead of `/var/www/html/images`

**Alternative:** Skip chroot restriction if you need full SCP access to `/var/www/` directories.

### Step 15: Disable Password Authentication (Production)

After confirming SSH key authentication works:

```bash
sudo nano /etc/ssh/sshd_config
```

Find and modify:

```bash
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:

```bash
sudo systemctl restart ssh
```

### Step 16: Configure Fail2Ban (Optional)

Protect against brute force attacks:

```bash
sudo apt-get install fail2ban -y

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

Configure SSH jail:

```bash
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
```

Restart fail2ban:

```bash
sudo systemctl restart fail2ban
```

---

## Testing & Verification

### Step 17: Test SSH/SCP Connection

From the ComfyUI client machine:

```bash
# Test SSH connection
ssh SCPuser@your.server.com

# If successful, exit
exit
```

### Step 18: Test File Upload

Create a test image:

```bash
# On client machine
echo "Test" > /tmp/test-upload.txt
```

Upload via SCP:

```bash
scp /tmp/test-upload.txt SCPuser@your.server.com:/var/www/html/images/
```

### Step 19: Verify File Permissions

On the server:

```bash
ls -la /var/www/html/images/test-upload.txt
```

Expected output:
```
-rw-rw-r-- 1 SCPuser www-data 5 Nov 09 01:30 test-upload.txt
```

**Check:**
- Owner: `SCPuser`
- Group: `www-data`
- Permissions: `664` (rw-rw-r--)

### Step 20: Test Web Access

Access the file via browser:

```
http://your.server.com/images/test-upload.txt
```

Should display or download the file.

### Step 21: Test ComfyUI Integration

1. Update ComfyUI `.env` file with server credentials
2. Configure `config.json` with correct server paths
3. Run a ComfyUI workflow with SaveImageSCP node
4. Check ComfyUI console for upload confirmation
5. Verify file appears on server in correct directory
6. Verify file is accessible via web browser

---

## Maintenance & Best Practices

### Regular Maintenance Tasks

#### Monitor Disk Space

Set up alerts for disk usage:

```bash
sudo apt-get install smartmontools -y

# Check disk space
df -h /var/www/html/images
```

**Recommendation:** Set up automated alerts when usage exceeds 80%.

#### Log Monitoring

Monitor upload activity:

```bash
# SSH authentication logs
sudo tail -f /var/log/auth.log | grep SCPuser

# Apache access logs
sudo tail -f /var/log/apache2/access.log | grep images
```

#### Automated Cleanup

Create a cleanup script for old images:

```bash
sudo nano /usr/local/bin/cleanup-old-images.sh
```

Add:

```bash
#!/bin/bash
# Clean up images older than 90 days

find /var/www/html/images -type f -mtime +90 -delete
find /var/www/production/gallery -type f -mtime +180 -delete

echo "Cleanup completed: $(date)" >> /var/log/image-cleanup.log
```

Make executable:

```bash
sudo chmod +x /usr/local/bin/cleanup-old-images.sh
```

Schedule with cron:

```bash
sudo crontab -e
```

Add:

```bash
# Run cleanup weekly on Sunday at 2 AM
0 2 * * 0 /usr/local/bin/cleanup-old-images.sh
```

### Backup Strategy

#### Daily Incremental Backups

```bash
# Install rsync
sudo apt-get install rsync -y

# Backup script
sudo nano /usr/local/bin/backup-images.sh
```

Add:

```bash
#!/bin/bash
# Backup ComfyUI images

BACKUP_DIR="/mnt/backup/images"
SOURCE_DIRS="/var/www/html/images /var/www/production/gallery"
DATE=$(date +%Y%m%d)

for SOURCE in $SOURCE_DIRS; do
    rsync -av --delete "$SOURCE/" "$BACKUP_DIR/$(basename $SOURCE)-$DATE/"
done

# Keep only last 30 days of backups
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $(date)" >> /var/log/image-backup.log
```

Schedule:

```bash
# Daily at 3 AM
0 3 * * * /usr/local/bin/backup-images.sh
```

### Security Auditing

#### Regular Security Checks

```bash
# Check for unauthorized changes to upload directories
sudo find /var/www/html/images -type f -mtime -1

# Check SCPuser login attempts
sudo lastlog -u SCPuser

# Review file permissions
sudo find /var/www/html/images -type f ! -perm 664
sudo find /var/www/html/images -type d ! -perm 775
```

#### Update Schedule

```bash
# Weekly security updates (automated)
sudo apt-get update
sudo apt-get upgrade -y

# Monthly review of:
# - SSH logs
# - Fail2ban bans
# - Disk usage trends
# - Unusual file uploads
```

### Performance Optimization

#### Image Optimization

Install image optimization tools:

```bash
sudo apt-get install optipng jpegoptim -y
```

Create optimization script:

```bash
sudo nano /usr/local/bin/optimize-images.sh
```

Add:

```bash
#!/bin/bash
# Optimize uploaded images

find /var/www/html/images -type f -name "*.png" -mtime -1 -exec optipng -o2 {} \;
find /var/www/html/images -type f -name "*.jpg" -mtime -1 -exec jpegoptim --max=85 {} \;
```

**Note:** Run during off-peak hours to avoid high CPU usage.

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Permission Denied on Upload

**Symptoms:**
```
scp: /var/www/html/images/file.png: Permission denied
```

**Solutions:**

1. Check directory ownership:
```bash
ls -ld /var/www/html/images
```
Should show: `drwxrwxr-x SCPuser www-data`

2. Fix ownership:
```bash
sudo chown SCPuser:www-data /var/www/html/images
sudo chmod 775 /var/www/html/images
```

3. Check parent directory permissions:
```bash
ls -ld /var/www/html
sudo chmod 755 /var/www/html
```

#### Issue 2: Files Not Accessible via Web

**Symptoms:**
- Browser shows 403 Forbidden
- Files exist but can't be accessed

**Solutions:**

1. Check file permissions:
```bash
ls -l /var/www/html/images/file.png
```
Should be: `rw-rw-r--` (664)

2. Fix file permissions:
```bash
sudo chmod 664 /var/www/html/images/file.png
```

3. Check Apache configuration:
```bash
sudo apache2ctl configtest
sudo systemctl restart apache2
```

4. Check Apache error logs:
```bash
sudo tail -f /var/log/apache2/error.log
```

#### Issue 3: SSH Connection Refused

**Symptoms:**
```
ssh: connect to host server.com port 22: Connection refused
```

**Solutions:**

1. Verify SSH is running:
```bash
sudo systemctl status ssh
```

2. Start SSH if stopped:
```bash
sudo systemctl start ssh
sudo systemctl enable ssh
```

3. Check firewall:
```bash
sudo ufw status
sudo ufw allow 22/tcp
```

4. Check SSH configuration:
```bash
sudo nano /etc/ssh/sshd_config
# Ensure Port 22 is not commented out
sudo systemctl restart ssh
```

#### Issue 4: Directory Not Found

**Symptoms:**
```
No such file or directory: /var/www/html/images
```

**Solutions:**

1. Create missing directory:
```bash
sudo mkdir -p /var/www/html/images
```

2. Set proper ownership and permissions:
```bash
sudo chown SCPuser:www-data /var/www/html/images
sudo chmod 775 /var/www/html/images
```

3. Update `config.json` to match server paths

#### Issue 5: Wrong File Ownership After Upload

**Symptoms:**
- Files owned by `root` instead of `SCPuser`
- Files not readable by Apache

**Solutions:**

1. Check umask setting:
```bash
sudo -u SCPuser bash -c 'umask'
```
Should be: `0002`

2. Fix existing files:
```bash
sudo chown -R SCPuser:www-data /var/www/html/images
sudo chmod -R 664 /var/www/html/images/*.png
sudo chmod 775 /var/www/html/images
```

3. Set default ACLs (see Step 8)

#### Issue 6: Disk Space Full

**Symptoms:**
```
No space left on device
```

**Solutions:**

1. Check disk usage:
```bash
df -h /var/www
```

2. Find large files:
```bash
sudo du -sh /var/www/html/images/* | sort -h
```

3. Clean up old files:
```bash
sudo find /var/www/html/images -mtime +90 -delete
```

4. Implement cleanup automation (see Maintenance section)

#### Issue 7: SELinux/AppArmor Blocking Access

**Symptoms:**
- Permissions look correct but access denied
- SELinux or AppArmor errors in logs

**Solutions (Ubuntu with AppArmor):**

1. Check AppArmor status:
```bash
sudo aa-status
```

2. If Apache profile is enforcing:
```bash
sudo aa-complain apache2
```

3. Or add custom profile for upload directories:
```bash
sudo nano /etc/apparmor.d/local/usr.sbin.apache2
```

Add:
```
/var/www/html/images/** rw,
```

Reload:
```bash
sudo systemctl reload apparmor
```

---

## Quick Reference Commands

### User Management
```bash
# Create user
sudo adduser --system --group --home /home/SCPuser --shell /bin/bash SCPuser

# Set password
sudo passwd SCPuser

# Add to www-data group
sudo usermod -aG www-data SCPuser
```

### Directory Setup
```bash
# Create directories
sudo mkdir -p /var/www/html/images

# Set ownership
sudo chown SCPuser:www-data /var/www/html/images

# Set permissions
sudo chmod 775 /var/www/html/images
```

### Testing
```bash
# Test SSH
ssh SCPuser@server.com

# Test upload
scp test.png SCPuser@server.com:/var/www/html/images/

# Check file
ls -la /var/www/html/images/
```

### Monitoring
```bash
# View upload logs
sudo tail -f /var/log/auth.log | grep SCPuser

# Check disk usage
df -h /var/www/html/images

# View web access
sudo tail -f /var/log/apache2/access.log | grep images
```

---

## Security Checklist

Before going to production, verify:

- [ ] Strong password set for SCPuser (or SSH key auth enabled)
- [ ] SCPuser added to www-data group
- [ ] All upload directories created with correct ownership
- [ ] Directory permissions set to 775
- [ ] Default ACLs configured for automatic permission inheritance
- [ ] Apache configuration prevents PHP execution in upload directories
- [ ] Apache configuration prevents directory listing
- [ ] SSH key authentication configured (recommended)
- [ ] Password authentication disabled (recommended)
- [ ] Fail2Ban installed and configured
- [ ] Firewall configured (UFW)
- [ ] File permissions are 664 for uploaded files
- [ ] Test upload successful
- [ ] Test web access successful
- [ ] Backup script configured and scheduled
- [ ] Cleanup script configured and scheduled
- [ ] Monitoring and alerting set up

---

## Additional Resources

- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [Apache2 Documentation](https://httpd.apache.org/docs/2.4/)
- [OpenSSH Documentation](https://www.openssh.com/manual.html)
- [Linux File Permissions Guide](https://wiki.archlinux.org/title/File_permissions_and_attributes)

---

## Support

For issues specific to the SaveImageSCP ComfyUI node, refer to the main README.md.

For server-specific issues:
1. Check the Troubleshooting section above
2. Review system logs: `sudo journalctl -xe`
3. Review Apache logs: `/var/log/apache2/error.log`
4. Review SSH logs: `/var/log/auth.log`

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** System Administration Team
