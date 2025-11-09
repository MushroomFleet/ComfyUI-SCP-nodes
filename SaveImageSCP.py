"""
SaveImageSCP - Custom ComfyUI Node
Saves images locally and uploads them to a remote server via SCP
"""

import os
import json
import socket
from datetime import datetime
import folder_paths
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import paramiko
from dotenv import load_dotenv
from pathlib import Path

# Find and load .env file with force reload
print("\n" + "="*60)
print("SaveImageSCP - Loading Environment Configuration")
print("="*60)

# Try multiple locations for .env file
env_locations = [
    Path(__file__).parent / ".env",  # Custom node directory
    Path(__file__).parent.parent.parent / ".env",  # ComfyUI root
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        print(f"Found .env at: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        break

if not env_loaded:
    print("⚠️  WARNING: No .env file found in expected locations:")
    for loc in env_locations:
        print(f"   - {loc}")
    load_dotenv(override=True)  # Try default locations
else:
    print(f"✅ Environment variables loaded (with override)")

print("="*60 + "\n")


class SaveImageSCP:
    """
    A custom node that saves images and uploads them via SCP to predefined server locations
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        
        # Load SCP configuration from .env
        self.scp_host = os.getenv('SCP_HOST')
        self.scp_port = int(os.getenv('SCP_PORT', '22'))
        self.scp_username = os.getenv('SCP_USERNAME')
        self.scp_password = os.getenv('SCP_PASSWORD')
        
        # Debug: Print loaded configuration (without password)
        print("\n" + "="*60)
        print("SaveImageSCP - Configuration Loaded:")
        print("="*60)
        print(f"SCP Host: {self.scp_host}")
        print(f"SCP Port: {self.scp_port}")
        print(f"SCP Username: {self.scp_username}")
        print(f"SCP Password: {'*' * len(self.scp_password) if self.scp_password else 'NOT SET'}")
        print("="*60 + "\n")
        
        # Load profiles from config.json
        self.profiles = self._load_profiles()
    
    def _load_profiles(self):
        """Load SCP profiles from config.json"""
        config_path = Path(__file__).parent / "config.json"
        
        if not config_path.exists():
            print(f"Warning: config.json not found at {config_path}")
            return {"default": "/tmp/"}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('profiles', {"default": "/tmp/"})
        except Exception as e:
            print(f"Error loading config.json: {e}")
            return {"default": "/tmp/"}
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the node"""
        # Create temporary instance to load profiles
        temp_instance = cls()
        profile_names = list(temp_instance.profiles.keys())
        
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "profile": (profile_names, {"default": profile_names[0] if profile_names else "default"}),
            },
            "optional": {
                "upload_enabled": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "save_and_upload"
    OUTPUT_NODE = True
    CATEGORY = "image"
    
    def save_and_upload(self, images, filename_prefix="ComfyUI", profile="default", upload_enabled=True):
        """
        Save images locally and upload via SCP
        
        Args:
            images: Tensor of images to save
            filename_prefix: Prefix for saved filenames
            profile: Profile name from config.json
            upload_enabled: Whether to upload via SCP
        """
        results = []
        
        # Get remote path from profile
        remote_path = self.profiles.get(profile, "/tmp/")
        
        for i, image in enumerate(images):
            # Convert tensor to PIL Image
            img_array = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
            
            # Generate filename with timestamp
            counter = self._get_next_counter(filename_prefix)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Local filename (without timestamp for ComfyUI compatibility)
            local_filename = f"{filename_prefix}_{counter:05d}.png"
            local_filepath = os.path.join(self.output_dir, local_filename)
            
            # Remote filename (with timestamp to prevent collisions)
            remote_filename = f"{filename_prefix}_{counter:05d}_{timestamp}.png"
            
            # Add metadata
            metadata = PngInfo()
            metadata.add_text("parameters", f"Profile: {profile}, Remote: {remote_path}")
            metadata.add_text("timestamp", timestamp)
            metadata.add_text("remote_filename", remote_filename)
            
            # Save image locally
            img.save(local_filepath, pnginfo=metadata, compress_level=4)
            print(f"Saved locally: {local_filepath}")
            
            # Upload via SCP if enabled (use timestamped filename for remote)
            if upload_enabled and self._validate_scp_config():
                try:
                    self._upload_via_scp(local_filepath, remote_filename, remote_path)
                    print(f"Uploaded: {remote_filename} to {self.scp_host}:{remote_path}")
                except Exception as e:
                    print(f"Upload failed for {remote_filename}: {e}")
            elif upload_enabled:
                print("Warning: SCP configuration incomplete. Skipping upload.")
            
            results.append({
                "filename": local_filename,
                "subfolder": "",
                "type": self.type
            })
        
        return {"ui": {"images": results}}
    
    def _validate_scp_config(self):
        """Check if SCP configuration is valid"""
        is_valid = all([
            self.scp_host,
            self.scp_username,
            self.scp_password
        ])
        
        if not is_valid:
            missing = []
            if not self.scp_host: missing.append("SCP_HOST")
            if not self.scp_username: missing.append("SCP_USERNAME")
            if not self.scp_password: missing.append("SCP_PASSWORD")
            print(f"⚠️  WARNING: Missing SCP configuration: {', '.join(missing)}")
        
        return is_valid
    
    def _test_dns_resolution(self, hostname):
        """Test if hostname can be resolved to IP address"""
        try:
            print(f"🔍 Testing DNS resolution for: {hostname}")
            ip_address = socket.gethostbyname(hostname)
            print(f"✅ DNS Resolution successful: {hostname} → {ip_address}")
            return True, ip_address
        except socket.gaierror as e:
            print(f"❌ DNS Resolution FAILED for: {hostname}")
            print(f"   Error: {e}")
            print(f"\n💡 Troubleshooting Tips:")
            print(f"   1. Verify hostname is correct (check for typos)")
            print(f"   2. Try using IP address instead in .env file:")
            print(f"      SCP_HOST=192.168.1.100")
            print(f"   3. Test DNS with: ping {hostname}")
            print(f"   4. Test DNS with: nslookup {hostname}")
            print(f"   5. Check your internet/network connection")
            print(f"   6. Check firewall/DNS settings")
            return False, str(e)
    
    def _upload_via_scp(self, local_path, filename, remote_path):
        """
        Upload file via SCP using paramiko
        
        Args:
            local_path: Local file path
            filename: Name of the file
            remote_path: Remote directory path
        """
        print(f"\n{'='*60}")
        print(f"Starting SCP Upload: {filename}")
        print(f"{'='*60}")
        
        # Step 1: Test DNS resolution first
        print(f"Step 1: DNS Resolution Test")
        dns_ok, dns_result = self._test_dns_resolution(self.scp_host)
        
        if not dns_ok:
            raise Exception(f"DNS resolution failed for {self.scp_host}: {dns_result}")
        
        # Step 2: Create SSH client
        print(f"\nStep 2: Creating SSH connection")
        print(f"   Host: {self.scp_host} ({dns_result})")
        print(f"   Port: {self.scp_port}")
        print(f"   Username: {self.scp_username}")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Step 3: Connect to server
            print(f"\nStep 3: Attempting SSH connection...")
            ssh.connect(
                hostname=self.scp_host,
                port=self.scp_port,
                username=self.scp_username,
                password=self.scp_password,
                timeout=10
            )
            print(f"✅ SSH connection successful!")
            
            # Step 4: Open SFTP session
            print(f"\nStep 4: Opening SFTP session...")
            sftp = ssh.open_sftp()
            print(f"✅ SFTP session opened")
            
            # Step 5: Ensure remote directory exists
            print(f"\nStep 5: Checking remote directory: {remote_path}")
            self._ensure_remote_directory(sftp, remote_path)
            
            # Step 6: Upload file
            print(f"\nStep 6: Uploading file...")
            remote_file = os.path.join(remote_path, filename).replace('\\', '/')
            print(f"   Local:  {local_path}")
            print(f"   Remote: {remote_file}")
            
            sftp.put(local_path, remote_file)
            print(f"✅ Upload completed successfully!")
            
            # Close connections
            sftp.close()
            print(f"\n{'='*60}")
            print(f"Upload Summary: SUCCESS")
            print(f"{'='*60}\n")
            
        except paramiko.AuthenticationException as e:
            print(f"\n❌ Authentication FAILED")
            print(f"   Error: {e}")
            print(f"\n💡 Troubleshooting Tips:")
            print(f"   1. Verify username in .env: SCP_USERNAME={self.scp_username}")
            print(f"   2. Verify password is correct")
            print(f"   3. Check if user exists on server")
            print(f"   4. Try manual SSH: ssh {self.scp_username}@{self.scp_host}")
            raise
        except paramiko.SSHException as e:
            print(f"\n❌ SSH Connection FAILED")
            print(f"   Error: {e}")
            print(f"\n💡 Troubleshooting Tips:")
            print(f"   1. Verify SSH server is running on {self.scp_host}:{self.scp_port}")
            print(f"   2. Check firewall allows port {self.scp_port}")
            print(f"   3. Try manual SSH: ssh -p {self.scp_port} {self.scp_username}@{self.scp_host}")
            raise
        except socket.timeout:
            print(f"\n❌ Connection TIMEOUT")
            print(f"\n💡 Troubleshooting Tips:")
            print(f"   1. Verify server is online: ping {self.scp_host}")
            print(f"   2. Check network connectivity")
            print(f"   3. Verify port {self.scp_port} is not blocked by firewall")
            raise
        except Exception as e:
            print(f"\n❌ Upload FAILED")
            print(f"   Error Type: {type(e).__name__}")
            print(f"   Error Message: {e}")
            raise
        finally:
            ssh.close()
    
    def _ensure_remote_directory(self, sftp, remote_path):
        """Ensure remote directory exists, create if it doesn't"""
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            # Directory doesn't exist, try to create it
            try:
                sftp.mkdir(remote_path)
            except Exception as e:
                print(f"Warning: Could not create remote directory {remote_path}: {e}")
    
    def _get_next_counter(self, prefix):
        """Get next available counter for filename"""
        counter = 1
        while True:
            filename = f"{prefix}_{counter:05d}.png"
            if not os.path.exists(os.path.join(self.output_dir, filename)):
                return counter
            counter += 1


# Node registration
NODE_CLASS_MAPPINGS = {
    "SaveImageSCP": SaveImageSCP
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageSCP": "Save Image (SCP Upload)"
}
