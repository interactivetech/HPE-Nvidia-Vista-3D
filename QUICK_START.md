# 🚀 HPE NVIDIA Vista3D - Quick Start Guide

**Get up and running in 3 simple steps!**

## Prerequisites

### For Backend Setup (Vista3D Server):
- **OS**: Ubuntu Linux (18.04+) or macOS
- **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- **Memory**: 16GB+ RAM
- **Docker**: Docker and NVIDIA Container Toolkit installed
- **NVIDIA NGC**: Account and API key (free at [ngc.nvidia.com](https://ngc.nvidia.com/))

### For Frontend Setup (Web Interface):
- **OS**: Ubuntu Linux (18.04+) or macOS
- **Memory**: 8GB+ RAM (minimum)
- **Docker**: Docker installed
- **NVIDIA NGC**: Not required (connects to remote Vista3D server)

## Architecture Overview

**Typical Setup:**
- **Backend**: Ubuntu server with NVIDIA GPU
- **Frontend**: Mac or any machine with Docker
- **Connection**: SSH tunnels for secure communication

## Step 1: Setup

### Option A: Local Setup (All on One Machine)

If you have a GPU-enabled machine and want everything local:

```bash
# Clone the repository
gh repo clone dw-flyingw/HPE-Nvidia-Vista-3D
cd HPE-Nvidia-Vista-3D

# Setup backend (requires GPU)
cd backend
python3 setup.py

# Setup frontend
cd ../frontend
python3 setup.py
```

### Option B: Remote Backend Setup (Recommended)

**Most common scenario: Backend on remote Ubuntu server, Frontend on your Mac**

#### On Ubuntu Server (Backend):
```bash
# Clone and setup backend
gh repo clone dw-flyingw/HPE-Nvidia-Vista-3D
cd HPE-Nvidia-Vista-3D/backend
python3 setup.py
```

**The backend setup will:**
- ✅ Check system requirements (Docker, NVIDIA GPU, NVIDIA Container Toolkit)
- ✅ Request your NVIDIA NGC API key
- ✅ Create necessary directories
- ✅ Pull Vista3D Docker image (~30GB)
- ✅ Create `.env` configuration file

#### On Your Mac (Frontend):
```bash
# Clone and setup frontend
gh repo clone dw-flyingw/HPE-Nvidia-Vista-3D
cd HPE-Nvidia-Vista-3D/frontend
python3 setup.py
```

**The frontend setup will:**
- ✅ Check Docker installation
- ✅ Create necessary directories
- ✅ Pull Docker images for frontend and image server
- ✅ Create `.env` configuration file
- ✅ Configure for SSH tunnel connection (localhost:8000 and localhost:8888)

## Step 2: Start Services

### For Remote Backend Setup (Most Common):

#### 1. Start Backend (on Ubuntu Server):
```bash
cd backend
docker compose up -d
```

This starts the Vista3D AI Server on port 8000.

#### 2. Create SSH Tunnel (from Your Mac):

Open a terminal and run:
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```

**What this does:**
- `-L 8000:localhost:8000` - Forward tunnel: Access remote Vista3D at localhost:8000
- `-R 8888:0.0.0.0:8888` - Reverse tunnel: Backend can access your image server

**Keep this terminal open!**

#### 3. Start Frontend & Image Server (on Your Mac):

Open a new terminal and run:
```bash
cd frontend
docker compose up -d
```

This starts both the frontend and image server together.

#### 4. Access the Web Interface:

Open your browser to: **http://localhost:8501**

### For Local Setup (All on One Machine):

```bash
# Start backend
cd backend
docker compose up -d

# Start frontend (in a new terminal)
cd frontend
docker compose up -d
```

**What's Running:**
- 🧠 **Vista3D AI Server** (http://localhost:8000)
- 🌐 **Streamlit Web Interface** (http://localhost:8501)
- 🖼️ **Image Server** (http://localhost:8888)

**Note**: The Vista3D server takes 1-2 minutes to initialize.

## Step 3: Process Your Images

**Note**: This step requires the frontend web interface to be running.

```bash
# Sample data is automatically installed during setup (if available)
# The setup script installs sample medical imaging data for patient SAMPLE_DATA_001

# For your own data:
# Option A: Place DICOM files in dicom/ folder
# The dicom/ folder contains patient folders (e.g., SAMPLE_DATA_001, PA00000001)
mkdir -p dicom
# Copy your DICOM files to dicom/PA00000001/

# Option B: Place NIFTI files directly
mkdir -p output/nifti
# Copy your .nii.gz files to output/nifti/

# Open your browser to http://localhost:8501
# Use the Tools page in the web interface to:
# - Convert DICOM to NIFTI
# - Run AI segmentation
# - View 3D visualizations
```

**If you only set up the backend**: You can use the API directly or set up the frontend later.

## Step 4: View Sample Data

**Now let's explore the sample data that was automatically installed!**

### 1. Open the Web Interface
Open your browser and navigate to: **http://localhost:8501**

### 2. Select the Sample Patient
1. In the sidebar, you'll see a **"Select Patient"** dropdown
2. Click on it and select **"SAMPLE_DATA_001"** (the sample patient)
3. This will load the available scans for this patient

### 3. Select a Scan to View
1. In the **"Select Scan"** dropdown, you'll see several available scans:
   - `2.5MM_ARTERIAL_3` - CT scan with arterial contrast
   - `SAGITTAL_ABDOMEN_602_i00002` - Sagittal abdominal view
   - `CORONAL_ABDOMEN_601_i00002` - Coronal abdominal view
   - And more...

2. Select **`2.5MM_ARTERIAL_3`** for the best example

### 4. Explore the 3D Viewer
Once you've selected a patient and scan:
- The **NiiVue viewer** will load the medical image
- Use your mouse to:
  - **Rotate**: Click and drag to rotate the 3D view
  - **Zoom**: Scroll wheel to zoom in/out
  - **Pan**: Right-click and drag to move around
- Try different **slice types** in the sidebar:
  - **Axial**: Horizontal slices
  - **Coronal**: Front-to-back slices  
  - **Sagittal**: Left-to-right slices
  - **Multiplanar**: All three views at once
  - **3D Render**: 3D volume rendering

### 5. Try the Tools Page
1. Click on the **"Tools"** tab in the sidebar
2. Here you can:
   - Convert DICOM to NIFTI (if needed)
   - Run AI segmentation on the sample data
   - View 3D visualizations with overlays
   - Download results

## 🎉 You're Done!

You now have a fully functional medical AI platform running with sample data ready to explore!

## 🌐 Understanding the SSH Tunnel

The SSH tunnel creates a secure bridge between your Mac and the Ubuntu server:

```
┌─────────── Mac ───────────┐
│  Browser :8501             │
│     ↓                      │
│  Frontend Container        │
│     ↓                      │
│  localhost:8000 (forward)  │
│  localhost:8888 (reverse)  │
└────────┼──────────────────┘
         │ SSH Tunnel
┌────────┼─── Ubuntu ────────┐
│        ↓                   │
│  Vista3D Backend :8000     │
│        ↓                   │
│  Fetches images from       │
│  localhost:8888 (tunnel)   │
└────────────────────────────┘
```

### SSH Tunnel Explained

**Command:**
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```

**What each part does:**
- `-L 8000:localhost:8000` - **Forward tunnel**: Maps your Mac's localhost:8000 to Ubuntu's localhost:8000
  - Lets your browser/frontend access the remote Vista3D backend
- `-R 8888:0.0.0.0:8888` - **Reverse tunnel**: Maps Ubuntu's localhost:8888 back to your Mac's port 8888
  - Lets the remote backend fetch images from your Mac's image server
  - Must use `0.0.0.0` (not `localhost`) so Docker containers can access it

### VPN/Firewall Access

If the Ubuntu server is behind a VPN or firewall, the SSH tunnel works perfectly:

```bash
# 1. Connect to your organization's VPN first
# 2. Then establish SSH tunnel
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@vpn-server
```

**Benefits:**
- ✅ Encrypts all traffic between frontend and backend
- ✅ Works through corporate firewalls and VPNs
- ✅ No need to open additional firewall ports
- ✅ Secure access to backend services

### Configuration Details

The setup scripts automatically configure the correct URLs:

**Frontend `.env`:**
```bash
VISTA3D_SERVER=http://host.docker.internal:8000
VISTA3D_IMAGE_SERVER_URL=http://host.docker.internal:8888
IMAGE_SERVER=http://localhost:8888
```

**Backend `.env`:**
```bash
VISTA3D_SERVER=http://localhost:8000
IMAGE_SERVER=http://localhost:8888
```

These are pre-configured to work with the SSH tunnel setup!

## 🛠️ Using the Tools Page

The web interface includes a powerful **Tools page** where you can:

- **Convert DICOM to NIFTI**: Upload DICOM files and convert them to NIFTI format
- **Run AI Segmentation**: Process NIFTI files with the Vista3D AI model
- **View 3D Visualizations**: Interactive 3D medical viewer with multi-planar views
- **Batch Processing**: Process multiple patients and studies at once
- **Download Results**: Export segmentation results and 3D models

**Access the Tools page**: Navigate to http://localhost:8501 and click on the "Tools" tab in the sidebar.

## 🔧 Management Commands

### Backend (Vista3D AI Server)
```bash
cd backend

# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Check status
docker ps
```

### Frontend (Web Interface + Image Server)
```bash
cd frontend

# Start (starts both frontend and image server)
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f vista3d-frontend-standalone
docker compose logs -f vista3d-image-server-for-frontend
```

### Quick Diagnostics

Run this anytime to check connectivity:
```bash
cd frontend
bash quick_test.sh
```

This will test:
- Frontend → Backend connection
- SSH tunnel status
- Backend accessibility
- Image server accessibility

## 🔍 Troubleshooting

### Quick Diagnostic
```bash
# Run the built-in connectivity test
cd frontend
bash quick_test.sh
```

### Services Not Starting

**Backend:**
```bash
# Check Docker
docker info

# Check GPU
nvidia-smi

# Check logs
cd backend
docker compose logs -f
```

**Frontend:**
```bash
# Check logs
cd frontend
docker compose logs -f

# Check if containers are running
docker ps
```

### SSH Tunnel Issues

**Symptoms:** Segmentation fails with "Connection refused" errors

**Check tunnel is running:**
```bash
ps aux | grep "ssh.*8000.*8888"
```

**Reconnect if needed:**
```bash
# Kill old tunnel
pkill -f "ssh.*8000.*8888"

# Reconnect
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```

**Important:** The reverse tunnel must use `-R 8888:0.0.0.0:8888` (not `localhost`)

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :8501  # Frontend
lsof -i :8888  # Image server
lsof -i :8000  # Backend (via tunnel)

# Kill process using port
kill <PID>
```

### Permission Issues
```bash
# Fix data folder permissions
sudo chown -R $USER:$USER output/
sudo chown -R $USER:$USER dicom/
sudo chmod -R 755 output/ dicom/
```

### Backend Can't Fetch Images

This usually means the reverse SSH tunnel isn't working properly.

**On Ubuntu server, test:**
```bash
# Should show port 8888 listening on 0.0.0.0
netstat -tln | grep 8888

# Should return HTTP 200
curl http://localhost:8888/health

# Should return HTTP 200 (critical test)
docker exec vista3d-server-standalone curl http://localhost:8888/health
```

**If the Docker test fails:**
- Ensure SSH tunnel uses `-R 8888:0.0.0.0:8888` (the `0.0.0.0` is critical)
- Check Ubuntu SSH config has `GatewayPorts clientspecified` in `/etc/ssh/sshd_config`
- Restart sshd: `sudo systemctl restart sshd`
- Reconnect SSH tunnel from Mac

## 📚 Next Steps

1. **Explore the Sample Data**: Follow Step 4 above to view the pre-installed sample data
2. **Try AI Segmentation**: Use the Tools page to run segmentation on the sample data
3. **Upload Your Own Data**: Add DICOM or NIFTI files through the web interface
4. **Experiment with Visualization**: Try different slice types and rendering modes
5. **Process Multiple Studies**: Use batch processing features in the GUI

## 🆘 Need Help?

- Check the full [README.md](README.md) for detailed documentation
- See the [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for comprehensive setup guide and options
- Check the troubleshooting section above for common issues

---

**Ready to Go?** Follow the 3 steps above and you'll be up and running in 10 minutes! 🚀
