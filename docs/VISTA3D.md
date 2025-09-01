# Vista3D Docker Management Script

## Overview

The `vista3d.py` script is a comprehensive Python-based management tool for deploying and managing Vista3D Docker containers with external image server access. This script provides enhanced error handling, monitoring capabilities, and automated setup for the Vista3D medical imaging platform.

## Features

### 🐳 **Docker Container Management**
- Automated Vista3D container startup and shutdown
- GPU support with NVIDIA runtime
- Volume mounting for persistent data
- Environment variable configuration
- Container health monitoring

### 🌐 **External Image Server Integration**
- Starts external HTTPS image server (`image_server.py`)
- Automatic SSL certificate generation
- CORS support for cross-origin requests
- File serving from outputs directory
- Health monitoring and auto-restart capabilities

### 🔧 **Advanced Configuration**
- Environment variable management
- Domain whitelist configuration
- Supported image format handling
- SSL certificate management
- Network access control

### 📊 **Monitoring & Logging**
- Comprehensive logging system
- Health check functionality
- Monitoring script generation
- Systemd service creation
- Error handling and recovery

## Prerequisites

### System Requirements
- Linux operating system
- Docker installed and running
- NVIDIA GPU with CUDA support
- Python 3.7+
- Root access (for systemd service creation)

### Dependencies
```bash
# Python packages
pip install requests cryptography

# System packages
sudo apt-get install openssl
```

### Docker Requirements
- Docker daemon running
- NVIDIA Container Runtime
- Access to NGC registry

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Set up environment**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Edit environment variables
   nano .env
   ```

3. **Make script executable**
   ```bash
   chmod +x utils/vista3d.py
   ```

## Usage

### Basic Usage

#### Start Vista3D Container
```bash
python3 utils/vista3d.py
```

This command will:
- Check Docker availability
- Create outputs directory
- Start external image server
- Launch Vista3D Docker container
- Configure networking and volumes
- Perform health checks

#### Create Systemd Service
```bash
sudo python3 utils/vista3d.py --create-service
```

Creates a systemd service for automatic startup on boot.

#### Create Monitoring Script
```bash
python3 utils/vista3d.py --create-monitor
```

Generates a monitoring script for continuous health checks.

#### Health Check
```bash
python3 utils/vista3d.py --health-check
```

Checks external image server health and restarts if needed.

### Advanced Usage

#### Custom Configuration
```bash
# Start with custom outputs directory
python3 utils/vista3d.py --outputs-dir /path/to/outputs

# Start with custom image server port
IMAGE_SERVER_PORT=9999 python3 utils/vista3d.py
```

#### Service Management
```bash
# Start systemd service
sudo systemctl start vista3d

# Check service status
sudo systemctl status vista3d

# View service logs
sudo journalctl -u vista3d -f

# Stop service
sudo systemctl stop vista3d
```

## Configuration

### Environment Variables

The script uses several environment variables for configuration:

#### Docker Container Settings
```bash
NGC_API_KEY=nvapi-<your-api-key>
NGC_ORG_ID=<your-org-id>
CUDA_VISIBLE_DEVICES=1
NVIDIA_VISIBLE_DEVICES=1
```

#### Image Server Configuration
```bash
EXTERNAL_IMAGE_SERVER=https://host.docker.internal:8888
EXTERNAL_IMAGE_SERVER_HOST=host.docker.internal
EXTERNAL_IMAGE_SERVER_PORT=8888
```

#### File Access Settings
```bash
ALLOW_LOCAL_FILES=True
ENABLE_FILE_ACCESS=True
ALLOW_FILE_PROTOCOL=True
WORKSPACE_IMAGES_PATH=/workspace/outputs/nifti
```

#### Security Settings
```bash
IGNORE_SSL_ERRORS=True
DISABLE_URL_VALIDATION=False
```

### Domain Whitelist

The script maintains a comprehensive domain whitelist for security:

```python
domain_whitelist = [
    "https://host.docker.internal:8888",  # External image server
    "file://*",                           # Local file access
    "/workspace/*",                       # Container paths
    "localhost",                          # Local access
    "127.0.0.1",                         # Loopback
    "*"                                   # Wildcard (use with caution)
]
```

### Supported Image Formats

The script supports various medical imaging formats:
- `.nrrd` - Nearly Raw Raster Data
- `.nii` - NIFTI-1 format
- `.nii.gz` - Compressed NIFTI-1
- `.dcm` - DICOM format

## Architecture

### Component Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   vista3d.py   │───▶│  External Image  │───▶│  Vista3D       │
│   (Manager)    │    │  Server          │    │  Container      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Systemd       │    │   SSL Certs      │    │   GPU Runtime   │
│   Service       │    │   Generation     │    │   (NVIDIA)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Script Initialization**
   - Load configuration
   - Check prerequisites
   - Set up logging

2. **External Image Server**
   - Generate SSL certificates
   - Start HTTPS server
   - Serve files from outputs directory

3. **Docker Container**
   - Pull Vista3D image
   - Configure networking
   - Mount volumes
   - Set environment variables

4. **Health Monitoring**
   - Check server accessibility
   - Monitor container status
   - Auto-restart on failure

## File Structure

```
utils/
├── vista3d.py              # Main management script
├── image_server.py         # External image server
└── monitor_image_server.py # Monitoring script (generated)

outputs/
├── nifti/            # Medical image files
└── certs/                 # SSL certificates

logs/
├── start_vista.log        # Script execution logs
└── image_server_monitor.log # Monitoring logs
```

## Monitoring

### Health Checks

The script performs several health checks:

1. **Docker Availability**
   - Docker daemon status
   - Container runtime availability

2. **External Image Server**
   - Process status
   - HTTP response validation
   - SSL certificate validity

3. **Vista3D Container**
   - Container status
   - Port accessibility
   - Log analysis

### Monitoring Script

Generated monitoring script provides:
- Continuous health monitoring
- Automatic restart on failure
- Log rotation
- Email notifications (configurable)

## Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tlnp | grep :8888
sudo netstat -tlnp | grep :8000

# Kill conflicting processes
sudo fuser -k 8888/tcp
sudo fuser -k 8000/tcp
```

#### SSL Certificate Issues
```bash
# Regenerate certificates
rm -f outputs/certs/server.crt outputs/certs/server.key
python3 utils/image_server.py

# Check certificate validity
openssl x509 -in outputs/certs/server.crt -text -noout
```

#### Permission Issues
```bash
# Fix output directory permissions
sudo chown -R $USER:$USER outputs/
chmod -R 755 outputs/

# Fix script permissions
chmod +x utils/vista3d.py
```

### Debug Mode

Enable verbose logging:
```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run with debug output
python3 utils/vista3d.py --verbose
```

### Log Analysis

```bash
# View script logs
tail -f start_vista.log

# View image server logs
tail -f /tmp/image_server.log

# View container logs
docker logs -f vista3d

# View systemd service logs
sudo journalctl -u vista3d -f
```

## Security Considerations

### SSL/TLS Configuration
- Self-signed certificates for development
- Production: Use proper CA-signed certificates
- Regular certificate rotation

### Network Security
- Domain whitelist enforcement
- Port exposure minimization
- Firewall configuration

### File Access Control
- Restricted file protocol access
- Path validation
- User permission management

## Performance Optimization

### Resource Allocation
```bash
# Adjust shared memory
--shm-size=16G

# GPU memory limits
--gpus '"device=0,capabilities=compute,utility"'

# CPU limits
--cpus=4
```

### Monitoring Tuning
- Health check intervals
- Log rotation policies
- Resource usage thresholds

## Development

### Adding New Features

1. **Extend Vista3DManager class**
2. **Add new command-line arguments**
3. **Implement new methods**
4. **Update documentation**

### Testing

```bash
# Run basic tests
python3 utils/vista3d.py --health-check

# Test external image server
curl -k https://localhost:8888/

# Test Vista3D endpoint
curl http://localhost:8000/v1/vista3d/inference
```

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Add type hints
- Include docstrings
- Write unit tests

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

## License

[Add your license information here]

## Support

### Documentation
- [Vista3D Documentation](https://docs.ngc.nvidia.com/vista3d/)
- [Docker Documentation](https://docs.docker.com/)
- [NVIDIA Container Runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

### Community
- [GitHub Issues](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)
- [Wiki](https://github.com/your-repo/wiki)

### Contact
- **Maintainer**: [Your Name]
- **Email**: [your.email@example.com]
- **GitHub**: [@your-username]

---

*Last updated: [Current Date]*
*Version: [Script Version]*

