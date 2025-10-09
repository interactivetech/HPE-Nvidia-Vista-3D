# Remote Ubuntu Server Setup Instructions

## After `git pull` on Ubuntu Server

### 1. Restart Vista3D Container

The updated `backend/docker-compose.yml` includes the fix for Docker networking on Linux:

```bash
cd /path/to/HPE-Nvidia-Vista-3D/backend
docker compose down
docker compose up -d
```

### 2. Verify the Configuration

Check that the container is running with the host mapping:

```bash
# Check container is running
docker compose ps

# Verify the extra_hosts configuration
docker inspect vista3d-server-standalone | grep -A 5 ExtraHosts
```

You should see `host.docker.internal` mapped to the gateway IP.

### 3. Test the Setup

From the Vista3D container, test that it can reach the SSH reverse tunnel:

```bash
# Test from within the container
docker exec vista3d-server-standalone curl -I http://host.docker.internal:8888
```

This should return a 200 OK response from your Mac's image server (via SSH tunnel).

## What Changed

- **`backend/docker-compose.yml`**: Added `extra_hosts` mapping for `host.docker.internal`
- This enables Vista3D on Linux to access `http://host.docker.internal:8888`
- The hostname resolves to the Ubuntu host machine (where SSH tunnel port 8888 is listening)
- The SSH reverse tunnel (`-R 8888:localhost:8888`) forwards to your Mac's image server

## Network Flow

```
Mac Frontend → SSH Tunnel (8000) → Ubuntu Vista3D
                                       ↓
                                  host.docker.internal:8888
                                       ↓
                                  Ubuntu Host:8888
                                       ↓
                                  SSH Reverse Tunnel
                                       ↓
                                  Mac Image Server
```

## Troubleshooting

If segmentation still fails after restart:

1. **Check SSH tunnels are active:**
   ```bash
   # On your Mac
   ps aux | grep ssh
   # Should show: -R 8888:localhost:8888 -L 8000:localhost:8000
   ```

2. **Verify image server is accessible:**
   ```bash
   # On Ubuntu server
   curl http://localhost:8888
   # Should return HTML from image server
   ```

3. **Test from inside Vista3D container:**
   ```bash
   # On Ubuntu server
   docker exec vista3d-server-standalone curl http://host.docker.internal:8888
   # Should return HTML from image server
   ```

4. **Check Vista3D logs:**
   ```bash
   docker compose logs vista3d-server
   ```

## Additional Notes

- Your `.env` files are not tracked in git (they're in `.gitignore`)
- The setup scripts will generate correct `.env` files with `VISTA3D_IMAGE_SERVER_URL="http://host.docker.internal:8888"`
- If you manually created `.env`, ensure it has the correct value

