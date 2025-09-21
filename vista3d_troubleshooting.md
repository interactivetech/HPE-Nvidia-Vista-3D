# Vista3D Server SSH Port Forwarding Troubleshooting

## Current Status
✅ **Image Server**: Working perfectly with host networking
❌ **Vista3D Server**: SSH port forwarding issue

## Issue Analysis
The container can now access localhost:8888 (Image Server) but not localhost:8000 (Vista3D Server via SSH port forward).

## Troubleshooting Steps

### 1. Check SSH Port Forwarding
```bash
# Check if the SSH tunnel is active
ps aux | grep ssh

# Check if port 8000 is listening
lsof -i :8000
netstat -an | grep 8000
```

### 2. Test SSH Port Forwarding Command
Make sure your SSH command includes the correct flags:
```bash
# Example SSH port forwarding command
ssh -L 8000:localhost:8000 user@remote-server

# Or with specific bind address
ssh -L 127.0.0.1:8000:localhost:8000 user@remote-server
```

### 3. Verify Remote Vista3D Server
On the remote server, check if Vista3D is running:
```bash
# On remote server
curl http://localhost:8000/v1/vista3d/info
docker ps | grep vista3d
```

### 4. Alternative SSH Port Forwarding
Try different SSH forwarding options:
```bash
# Option 1: Bind to all interfaces
ssh -L 0.0.0.0:8000:localhost:8000 user@remote-server

# Option 2: Use different local port and update Docker config
ssh -L 8001:localhost:8000 user@remote-server
# Then update VISTA3D_SERVER=http://localhost:8001 in docker-compose.yml
```

### 5. Test Vista3D Server Endpoints
Try different endpoints:
```bash
curl http://localhost:8000/
curl http://localhost:8000/docs
curl http://localhost:8000/v1/vista3d/info
curl http://localhost:8000/health
```

### 6. Check Docker Networking
```bash
# Test from within container
docker exec hpe-nvidia-vista3d-app curl http://localhost:8000/v1/vista3d/info
```

## Current Configuration
The Docker container is now using:
- **Network Mode**: `host` (can access localhost ports directly)
- **Image Server**: `http://localhost:8888` ✅
- **Vista3D Server**: `http://localhost:8000` ❌

## Next Steps
1. Verify your SSH port forwarding is working correctly
2. Check the Vista3D server is running on the remote machine
3. Test the Vista3D endpoints directly
4. Consider using a different local port if 8000 is conflicting
