# SaveImageSCP - Quick Setup Guide

## 📦 Files Included

1. **SaveImageSCP.py** - Main node file
2. **__init__.py** - Python module initialization
3. **config.json** - Profile configuration (remote paths)
4. **.env.example** - Environment variables template
5. **requirements.txt** - Python dependencies
6. **README.md** - Complete documentation
7. **install.sh** - Automated installation script (Linux/Mac)

## 🚀 Quick Install (Automated)

### Linux/Mac:
```bash
cd /path/to/downloaded/files
chmod +x install.sh
./install.sh
```

### Windows:
Follow manual installation steps below.

## 📝 Manual Installation

### Step 1: Copy Files
```bash
# Navigate to ComfyUI custom_nodes directory
cd /path/to/ComfyUI/custom_nodes

# Create directory
mkdir SaveImageSCP
cd SaveImageSCP

# Copy all files here
```

### Step 2: Install Dependencies
```bash
pip install paramiko python-dotenv
```

### Step 3: Configure .env
Create `.env` in ComfyUI root directory:
```bash
cd /path/to/ComfyUI
nano .env
```

Add your credentials:
```env
SCP_HOST=192.168.1.100
SCP_PORT=22
SCP_USERNAME=myuser
SCP_PASSWORD=mypassword
```

### Step 4: Configure Profiles
Edit `config.json` in the SaveImageSCP directory:
```json
{
  "profiles": {
    "web": "/var/www/html/images/",
    "backup": "/mnt/backup/comfyui/"
  }
}
```

### Step 5: Restart ComfyUI
Restart ComfyUI to load the new node.

## 🎯 Usage

1. In ComfyUI, find **Save Image (SCP Upload)** node
2. Connect your image output to it
3. Select a profile from the dropdown
4. Set filename prefix
5. Run your workflow!

## ⚙️ Node Inputs

- **images** (required) - Image tensor input
- **filename_prefix** - Name prefix for saved files
- **profile** - Dropdown list of configured profiles
- **upload_enabled** - Toggle to enable/disable upload

## 📁 Directory Structure

```
ComfyUI/
├── .env                          # ← Your SCP credentials here
├── custom_nodes/
│   └── SaveImageSCP/
│       ├── __init__.py
│       ├── SaveImageSCP.py
│       ├── config.json           # ← Your profiles here
│       ├── requirements.txt
│       └── README.md
└── output/                       # ← Local images saved here
```

## 🔍 Testing Your Setup

1. Create a simple workflow with image generation
2. Add SaveImageSCP node
3. Set profile to "default" (or your first profile)
4. Run workflow
5. Check:
   - Local: `ComfyUI/output/` for saved image
   - Remote: Your configured remote path
   - Console: For success/error messages

## ⚠️ Common Issues

### "SCP configuration incomplete"
→ Check `.env` file exists in ComfyUI root and contains all fields

### "Profile not found"
→ Check `config.json` syntax, restart ComfyUI

### "Upload failed"
→ Test SSH access: `ssh username@hostname`
→ Check remote directory exists and is writable

### "Module not found: paramiko"
→ Install dependencies: `pip install paramiko python-dotenv`

## 🔐 Security Tips

1. **Use SSH Keys** instead of passwords (see README.md)
2. **Restrict .env permissions**: `chmod 600 .env`
3. **Don't commit .env** to version control
4. **Use strong passwords** or key authentication
5. **Enable firewall rules** on remote server

## 🎨 Example config.json

```json
{
  "profiles": {
    "default": "/var/www/html/images/",
    "portfolio": "/home/user/portfolio/renders/",
    "client_a": "/mnt/storage/clients/clientA/images/",
    "testing": "/tmp/comfyui/test/",
    "archive": "/mnt/backup/images/archive/"
  }
}
```

## 🔄 Workflow Example

```
┌─────────────────┐
│ Load Checkpoint │
└────────┬────────┘
         │
┌────────▼────────┐
│  KSampler       │
└────────┬────────┘
         │
┌────────▼────────┐
│ VAE Decode      │
└────────┬────────┘
         │
┌────────▼────────────────┐
│ Save Image (SCP Upload) │
│ • prefix: "artwork"     │
│ • profile: "portfolio"  │
│ • upload: ✓             │
└─────────────────────────┘
```

## 📚 Additional Resources

- Full documentation: See **README.md**
- ComfyUI docs: https://github.com/comfyanonymous/ComfyUI
- Paramiko docs: https://www.paramiko.org/

## 💡 Pro Tips

1. **Create profile per project** for organized uploads
2. **Use descriptive prefixes** like "character_concept_" 
3. **Test with upload_enabled=False** first
4. **Check server disk space** regularly
5. **Backup your config.json** when adding new profiles

## 🆘 Need Help?

1. Check console output for detailed errors
2. Test SSH connection independently
3. Verify file permissions on remote server
4. Review README.md troubleshooting section
5. Check ComfyUI logs: `ComfyUI/comfyui.log`

---

**Ready to use!** Your images will now automatically upload to your configured servers. 🚀
