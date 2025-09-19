# Vista-3D GUI Startup Script

The `start_gui.py` script provides an easy way to start the Vista-3D GUI containers (Streamlit app and image server) using Docker Compose.

## Features

- **Automated Container Management**: Starts both Streamlit app and image server containers
- **Health Checks**: Monitors container health and readiness
- **Comprehensive Logging**: Detailed logs for troubleshooting
- **Systemd Integration**: Optional systemd service creation for auto-startup
- **Environment Configuration**: Supports custom ports and configuration via environment variables
- **Graceful Shutdown**: Proper cleanup on exit

## Usage

### Basic Usage

```bash
# Start the GUI containers
python3 utils/start_gui.py

# Or make it executable and run directly
chmod +x utils/start_gui.py
./utils/start_gui.py
```

### Create Systemd Service (Auto-startup)

```bash
# Create systemd service for automatic startup on boot
sudo python3 utils/start_gui.py --create-service

# Then start the service
sudo systemctl start vista3d-gui

# Check status
sudo systemctl status vista3d-gui

# View logs
sudo journalctl -u vista3d-gui -f
```

## Environment Variables

The script supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | `8501` | Port for the Streamlit app |
| `IMAGE_SERVER_PORT` | `8888` | Port for the image server |
| `USE_HOST_NETWORKING` | `False` | Use host networking (allows all interfaces) |
| `IMAGE_SERVER` | `http://image-server:8888` | Image server URL |
| `VISTA3D_SERVER` | `http://vista3d-server:8000` | Vista3D server URL |
| `VISTA3D_API_KEY` | - | API key for Vista3D server |
| `HPE_CLUSTER_ENDPOINT` | - | HPE cluster endpoint |
| `HPE_API_KEY` | - | HPE API key |

## Container Details

The script starts two containers:

### 1. Streamlit App (`hpe-nvidia-vista3d-app`)
- **Port**: 8501 (default)
- **Purpose**: Main GUI application
- **Health Check**: `http://localhost:8501/_stcore/health`

### 2. Image Server (`vista3d-image-server`)
- **Port**: 8888 (default)
- **Purpose**: Serves medical imaging files
- **Health Check**: `http://localhost:8888/health`

## Prerequisites

- Docker installed and running
- Docker Compose available
- Python 3.7+ with required dependencies
- `.env` file with configuration (optional)

## Troubleshooting

### Check Container Status
```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f

# View specific container logs
docker logs -f hpe-nvidia-vista3d-app
docker logs -f vista3d-image-server
```

### Common Issues

1. **Port Already in Use**: Change ports using environment variables
   ```bash
   STREAMLIT_SERVER_PORT=8502 IMAGE_SERVER_PORT=8889 python3 utils/start_gui.py
   ```

2. **Docker Not Running**: Start Docker daemon
   ```bash
   sudo systemctl start docker
   ```

3. **Permission Issues**: Ensure user is in docker group
   ```bash
   sudo usermod -aG docker $USER
   ```

### Stop Containers

```bash
# Stop using docker compose
docker compose down

# Or stop individual containers
docker stop hpe-nvidia-vista3d-app vista3d-image-server
```

## Logs

Logs are written to:
- Console output (stdout)

## Integration with Vista3D

This script is designed to work alongside the Vista3D server. To run the complete system:

1. Start Vista3D server: `python3 utils/start_vista3d.py`
2. Start GUI containers: `python3 utils/start_gui.py`
3. Access the GUI at: `http://localhost:8501`
