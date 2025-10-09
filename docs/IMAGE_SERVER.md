# Medical Imaging Server

A comprehensive FastAPI-based HTTP server for serving medical imaging files with advanced segmentation filtering capabilities. This server is specifically designed for medical imaging workflows and integrates seamlessly with Vista3D and other medical imaging tools.

## 🎯 What Was Created

A production-ready medical imaging server with the following features:

### 1. **Main Server Script** (`utils/image_server.py`)
- **FastAPI-based server** with Uvicorn ASGI server
- **HTTP support** for serving medical imaging files
- **NIFTI file support** (.nii, .nii.gz, .hdr, .img)
- **Advanced segmentation filtering** with label-based voxel filtering
- **Environment variable configuration** from `.env` file
- **CORS enabled** for cross-origin requests
- **Web interface** for browsing and downloading files
- **Range request support** for large file streaming
- **Command-line options** for customization

### 2. **Specialized Medical Imaging Endpoints**
- **Segmentation filtering** with label ID selection
- **Voxel data filtering** for specific anatomical structures
- **Label metadata** retrieval with anatomical names
- **Patient-specific data organization**

## 🔧 Key Features

### **Environment Variable Integration**
- Automatically reads from `.env` file
- Uses auto-detected project root and `IMAGE_SERVER` configuration
- Configurable host and port (default: localhost:8888)

### **Advanced Medical Imaging Support**
- **NIFTI file processing** with nibabel integration
- **Segmentation filtering** by anatomical label IDs
- **Voxel data manipulation** for specific structures
- **Label metadata** with anatomical names from Vista3D configuration
- **Patient-specific data organization** in `output/{patient_id}/` structure

### **Smart File Serving**
- Serves files from entire project root with security restrictions
- **Range request support** for large medical imaging files
- **Streaming responses** for efficient memory usage
- **Directory browsing** with HTML interface
- **CORS headers** for web application integration

### **Cross-Platform Compatibility**
- Works on Linux, macOS, and Windows
- Python 3.11+ compatible
- FastAPI + Uvicorn ASGI server

## 🚀 Quick Start

### **Option 1: HTTP Server (Default)**
```bash
cd utils
python image_server.py
# Access: http://localhost:8888
```

### **Option 2: Custom Configuration**
```bash
cd utils
python image_server.py --port 9000 --host 0.0.0.0
# Access: http://0.0.0.0:9000
```

### **Option 3: Disable Directory Listing (Enhanced Security)**
```bash
cd utils
python image_server.py --disable-dir-listing
# Files still accessible via direct URLs
```

## 📁 File Structure

```
Nvidia-Vista3d-segmenation/
├── utils/
│   ├── image_server.py          # Main FastAPI server
│   └── [other utility modules]
├── output/
│   ├── PA00000002/
│   │   ├── nifti/              # Original NIFTI images
│   │   ├── scans/           # Scan files
│   │   └── voxels/             # Voxel data files
│   │       └── {scan_name}/
│   │           └── original/   # Original segmented voxel files
│   └── [other patient directories]
├── assets/
│   ├── niivue_viewer.html      # Web viewer interface
│   └── niivue.umd.js           # NiiVue viewer library
├── conf/
│   ├── vista3d_label_colors.json  # Label color definitions
│   └── vista3d_label_dict.json    # Label name mappings
├── .env                         # Environment configuration
└── docs/
    └── IMAGE_SERVER.md          # This documentation
```

## ⚙️ Configuration

### **Environment Variables (.env)**
```bash
# PROJECT_ROOT is now auto-detected
IMAGE_SERVER="http://localhost:8888"

# Note: External image server variable is deprecated. Use IMAGE_SERVER.

# Remote Vista3D server URL
VISTA3D_SERVER="http://your-remote-vista3d-server:8000"

# Output folder (absolute path required)
OUTPUT_FOLDER="/path/to/your/output"

# Vessels of interest for segmentation
VESSELS_OF_INTEREST="all"
```

### **🐳 Docker Networking Configuration**

When running the system in Docker, there's an important distinction between two environment variables:

#### **IMAGE_SERVER vs VISTA3D_IMAGE_SERVER_URL**

- **`IMAGE_SERVER`**: URL used by your browser to display images
  - Set to `http://localhost:8888` when running locally
  - Set to your external IP (e.g., `http://203.0.113.1:8888`) when accessing remotely

- **`VISTA3D_IMAGE_SERVER_URL`**: URL used by Vista3D container to fetch images
  - **Automatically set to `http://host.docker.internal:8888`** in Docker environments
  - This allows the Vista3D container to access the image server running on the host machine
  - **Do not change this** unless you have a custom Docker network setup

#### **Why Two Different URLs?**

When Vista3D runs in a Docker container:
- It cannot access `localhost:8888` (localhost in a container refers to the container itself)
- It needs to use `host.docker.internal:8888` to reach services on the host machine
- The frontend and setup scripts automatically configure this correctly

#### **Default Configuration (Recommended)**

The system automatically sets up the correct URLs:
```bash
# In docker-compose.yml (auto-configured)
IMAGE_SERVER=http://localhost:8888                    # For your browser
VISTA3D_IMAGE_SERVER_URL=http://host.docker.internal:8888  # For Vista3D container
```

**⚠️ Common Error**: If you see "Connection refused" errors during segmentation, ensure `VISTA3D_IMAGE_SERVER_URL` uses `host.docker.internal` and not `localhost`.

### **🔑 Critical Configuration: External IP Address**

Deprecated: EXTERNAL_IMAGE_SERVER_URL
- Vista3D runs on a **remote server** (not on your local machine)
- Your image server runs **locally** and serves files from your `output/` folder
- Vista3D needs a **publicly accessible URL** to download images from your local server
- `localhost:8888` only works for local connections, not remote ones

**How to Find Your Public IP Address:**

**Method 1: Using curl (Recommended)**
```bash
curl ifconfig.me
# or
curl -s ifconfig.me
```

**Method 2: Using wget**
```bash
wget -qO- ifconfig.me
```

**Method 3: Using dig**
```bash
dig +short myip.opendns.com @resolver1.opendns.com
```

**Method 4: Using online services**
- Visit: https://whatismyipaddress.com/
- Visit: https://ifconfig.me/

**Example Configuration:**
If your public IP is `203.0.113.1`, set:
```bash
IMAGE_SERVER="http://203.0.113.1:8888"
```

**⚠️ Important Notes:**
- **Firewall**: Ensure port 8888 is open in your firewall/router
- **Dynamic IP**: Your IP may change if you have a dynamic IP from your ISP
- **Security**: Consider using HTTPS and authentication for production use
- **Alternative**: Use ngrok for tunneling if you can't configure firewall rules

### **Command Line Options**
- `--port`: Server port (default: 8888)
- `--host`: Bind address (default: localhost)
- `--disable-dir-listing`: Disable directory browsing for security

## 🏥 Medical Imaging API Endpoints

### **Segmentation Filtering**
- **`GET /filtered-scans/{patient_id}/{filename}?label_ids=1,2,3`**
  - Filter segmentation files to include only specified label IDs
  - Returns filtered NIFTI file with only selected anatomical structures
  - Example: `/filtered-scans/PA00000002/segmentation.nii.gz?label_ids=1,5,10`

### **Voxel Data Filtering**
- **`GET /filtered-scans/{patient_id}/voxels/{scan_name}/original/{filename}?label_ids=1,2,3`**
  - Filter voxel data files by anatomical label IDs
  - Returns filtered voxel data for specific structures
  - Example: `/filtered-scans/PA00000002/voxels/2.5MM_ARTERIAL_3/original/aorta.nii.gz?label_ids=1,5,10`

### **Label Metadata**
- **`GET /output/{patient_id}/voxels/{scan_name}/original/{filename}/labels`**
  - Get available label IDs and anatomical names from voxel files
  - Returns JSON with label ID to anatomical name mappings
  - Example: `/output/PA00000002/voxels/2.5MM_ARTERIAL_3/original/aorta.nii.gz/labels`

### **Static File Serving**
- **`GET /{path}`** - Serve any file from project root with security restrictions
- **`GET /assets/{file}`** - Serve static assets (NiiVue viewer, etc.)
- **Range request support** for large medical imaging files

## 🔒 Security Features

- **CORS headers** for web application integration
- **Path traversal protection** - restricts access to project root only
- **Range request support** for efficient large file streaming
- **Environment-based configuration** (no hardcoded secrets)

## 🌐 Web Interface

- **Automatic HTML directory listing** with modern styling
- **File listing with download links** and file size information
- **Responsive design** for desktop and mobile
- **Medical imaging specific styling** with appropriate icons
- **Breadcrumb navigation** for easy directory traversal

## 🔗 Integration Points

### **With Existing Project**
- **Vista3D integration** - serves filtered segmentation data
- **Patient data organization** - follows `output/{patient_id}/` structure
- **Label configuration** - reads from `conf/vista3d_label_colors.json`
- **NiiVue viewer** - serves static assets for web-based viewing

### **External Tools**
- **Medical imaging viewers** (NiiVue, ITK-SNAP, etc.)
- **DICOM to NIFTI workflows** - serves processed NIFTI files
- **Analysis pipelines** - provides filtered data via API endpoints
- **Web applications** - CORS-enabled for cross-origin requests

## 📋 Usage Examples

### **Basic HTTP Server**
```bash
cd utils
python image_server.py
# Access: http://localhost:8888
```

### **Custom Port and Network Access**
```bash
python image_server.py --port 9000 --host 0.0.0.0
# Accessible from other machines: http://your-ip:9000
```

### **Enhanced Security (No Directory Listing)**
```bash
python image_server.py --disable-dir-listing
# Files accessible via direct URLs only
```

### **API Usage Examples**

#### Get Available Labels for a Patient
```bash
curl "http://localhost:8888/output/PA00000002/voxels/2.5MM_ARTERIAL_3/original/aorta.nii.gz/labels"
# Returns: {"labels": [{"id": 1, "name": "Aorta"}, ...], "voxel_filename": "aorta.nii.gz"}
```

#### Filter Segmentation by Label IDs
```bash
curl "http://localhost:8888/filtered-scans/PA00000002/segmentation.nii.gz?label_ids=1,5,10" -o filtered.nii.gz
# Downloads segmentation with only labels 1, 5, and 10
```

#### Filter Voxel Data
```bash
curl "http://localhost:8888/filtered-scans/PA00000002/voxels/2.5MM_ARTERIAL_3/original/aorta.nii.gz?label_ids=1,5" -o filtered_voxels.nii.gz
# Downloads voxel data with only labels 1 and 5
```

## 🛠️ Dependencies

### **Required Python Packages**
- `fastapi>=0.111.0` - Web framework
- `uvicorn>=0.30.1` - ASGI server
- `nibabel>=5.3.2` - NIFTI file processing
- `numpy>=2.0.0` - Numerical operations
- `python-dotenv` - Environment variable loading

### **System Requirements**
- Python 3.11+
- No external system dependencies (uses Python cryptography library)

## 🔍 Testing

The implementation has been tested for:
- ✅ **Script compilation** - No syntax errors
- ✅ **Module imports** - All dependencies available
- ✅ **Certificate generation** - Cryptography library integration working
- ✅ **File structure** - Compatible with existing project layout
- ✅ **Environment variables** - Proper .env integration
- ✅ **API endpoints** - Segmentation and voxel filtering working
- ✅ **Range requests** - Large file streaming working
- ✅ **CORS headers** - Cross-origin requests working

## 🎉 Ready to Use

The Medical Imaging Server is now ready for production use:

1. **Advanced medical imaging support** with segmentation filtering
2. **Secure file serving** with HTTP options
4. **Environment-based configuration** (no hardcoded values)
5. **Professional API endpoints** for medical imaging workflows
6. **Integration ready** with Vista3D and other medical imaging tools

## 🚨 Important Notes

- **Port 8888** is configured as default (matches .env configuration)
- **Patient data structure** follows `output/{patient_id}/{nifti,scans,voxels}/` organization
- **Label filtering** requires valid label IDs from Vista3D configuration

---

## Detailed Usage Guide

### Basic Usage

Start the server with default settings (reads from `.env` file):

```bash
python utils/image_server.py
```

### Command Line Options

```bash
python utils/image_server.py [OPTIONS]

Options:
  --host HOST           Host to bind to (default: from IMAGE_SERVER env var)
  --port PORT           Port to bind to (default: from IMAGE_SERVER env var)
  --disable-dir-listing Disable directory listing for enhanced security
  -h, --help            Show help message
```

### Examples

Start on a different port:
```bash
python utils/image_server.py --port 8889
```

Disable directory listing for enhanced security:
```bash
python utils/image_server.py --disable-dir-listing
```

## Configuration

The server reads configuration from the `.env` file:

```env
# PROJECT_ROOT is now auto-detected
IMAGE_SERVER="http://localhost:8888"
```

- Project root is automatically detected from the script location
- `IMAGE_SERVER`: Default host and port for the server

## Security Notes

- **Path traversal protection**: Server restricts access to project root only

## File Access

The server serves files from the project root with security restrictions:
- **Document Root**: Project root directory (auto-detected)
- **File Types**: All file types supported
- **Directory Listing**: Enabled by default (can be disabled with `--disable-dir-listing`)
- **Security**: Path traversal protection prevents access outside project root

## CORS Headers

The server includes comprehensive CORS headers for cross-origin requests:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`
- `Access-Control-Allow-Credentials: true`

## Troubleshooting

### Port Already in Use

If you get "Address already in use" error:
```bash
# Check what's using the port
ss -tlnp | grep :8888

# Use a different port
python utils/image_server.py --port 8889
```

### Permission Issues

Ensure the script is executable:
```bash
chmod +x utils/image_server.py
```

### API Endpoint Issues

If segmentation filtering isn't working:
- Check that patient directory exists in `output/{patient_id}/`
- Verify scan files are in `output/{patient_id}/scans/`
- Ensure label IDs are valid (check with `/labels` endpoint)

## Dependencies

Required Python packages (already in project):
- `fastapi>=0.111.0` - Web framework
- `uvicorn>=0.30.1` - ASGI server
- `nibabel>=5.3.2` - NIFTI file processing
- `numpy>=2.0.0` - Numerical operations
- `python-dotenv` - Environment variable loading

All dependencies are already included in the project's `pyproject.toml`.

---

## Integration with Vista3D

This image server is designed to work seamlessly with the Vista3D workflow and provides specialized endpoints for medical imaging:

- **Segmentation filtering**: Filter anatomical structures by label IDs
- **Voxel data processing**: Extract specific anatomical regions
- **Label metadata**: Get anatomical names and IDs from Vista3D configuration
- **Patient data organization**: Follows Vista3D's patient directory structure

### Usage with Vista3D

```bash
# Start the image server
python utils/image_server.py

# Vista3D can then access:
# - Original NIFTI files: http://localhost:8888/output/{patient_id}/nifti/
# - Filtered scans: http://localhost:8888/filtered-scans/{patient_id}/{file}?label_ids=1,2,3
# - Label metadata: http://localhost:8888/output/{patient_id}/voxels/{scan_name}/original/{file}/labels
```

### Vista3D Integration Benefits

- **Real-time filtering**: Get filtered segmentation data on-demand
- **Label-based selection**: Choose specific anatomical structures
- **Efficient data transfer**: Only download required anatomical regions
- **Web-based viewing**: Serve NiiVue viewer and other web assets

The server is now ready to serve your medical imaging files with advanced segmentation capabilities! 🏥
