# SSH Tunnel Configuration Guide

## Overview

This guide explains the SSH tunnel configuration for connecting a local Mac frontend to a remote Ubuntu Vista3D backend.

## The SSH Tunnel Command

```bash
ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

## Command Breakdown

### Forward Tunnel: `-L 8000:localhost:8000`

**What it does:**
- Forwards local port 8000 to remote server's localhost:8000
- Allows your Mac to access the remote Vista3D backend

**How it works:**
```
Mac Application → localhost:8000 → SSH → Remote Server localhost:8000 → Vista3D
```

**Example:**
```bash
# On Mac, this connects to the remote Vista3D:
curl http://localhost:8000/v1/vista3d/info

# Actually reaches:
# remote-server:8000 → Vista3D Docker container
```

### Reverse Tunnel: `-R 8888:localhost:8888`

**What it does:**
- Forwards remote server's port 8888 to your Mac's localhost:8888
- Allows Vista3D backend to access your Mac's image server

**How it works:**
```
Vista3D → localhost:8888 → SSH → Mac localhost:8888 → Image Server
```

**Example:**
```bash
# Vista3D backend requests:
# http://localhost:8888/output/patient/file.nii.gz

# Actually reaches:
# Mac image server → serves local file
```

## Full Connection Flow

### Segmentation Request Flow

```
1. User clicks "Segment" in browser
   ↓
2. Frontend (Mac) → http://localhost:8000/v1/vista3d/inference
   ↓ (SSH Forward Tunnel)
3. Remote Vista3D receives request
   ↓
4. Vista3D needs image → http://localhost:8888/output/patient/file.nii.gz
   ↓ (SSH Reverse Tunnel)
5. Mac Image Server serves file
   ↓ (SSH Reverse Tunnel)
6. Vista3D processes image
   ↓ (SSH Forward Tunnel)
7. Frontend receives result
   ↓
8. User sees segmentation in browser
```

## Verifying the Tunnels

### Test Forward Tunnel (Mac → Remote)

**On Mac:**
```bash
# Should return Vista3D info
curl http://localhost:8000/v1/vista3d/info

# Expected response:
{
  "name": "vista3d",
  "version": "1.0.0",
  ...
}
```

**If it fails:**
1. Check SSH tunnel is active: `lsof -i :8000`
2. Check remote backend is running: SSH to server and run `docker ps`
3. Check tunnel logs: Look at SSH terminal for errors

### Test Reverse Tunnel (Remote → Mac)

**On Remote Server:**
```bash
# Should return image server health check
curl http://localhost:8888/health

# Expected response:
{
  "status": "healthy",
  "service": "image-server"
}
```

**If it fails:**
1. Check SSH tunnel is active (on Mac): `lsof -i :8888`
2. Check image server is running (on Mac): `curl http://localhost:8888/health`
3. Check tunnel in both directions

### Test End-to-End

**From Vista3D container on remote server:**
```bash
# Test that Vista3D can reach the image server
docker exec vista3d-server-standalone curl -I http://localhost:8888/health

# Expected: HTTP 200 OK
```

## SSH Tunnel Options

### Basic Tunnel (Interactive)

```bash
ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

**Pros:**
- Easy to see connection status
- Easy to disconnect (Ctrl+C)
- Can run commands on remote server

**Cons:**
- Terminal stays open
- Disconnects if you close terminal

### Background Tunnel

```bash
ssh -f -N -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

**Options:**
- `-f`: Fork to background after authentication
- `-N`: Don't execute remote commands

**To disconnect:**
```bash
# Find the SSH process
ps aux | grep "ssh.*8000.*8888"

# Kill it
pkill -f "ssh.*8000.*8888"
```

### Persistent Tunnel with Auto-Reconnect

**Using SSH Config** (`~/.ssh/config`):
```
Host vista3d-remote
    HostName your-server.com
    User your-username
    LocalForward 8000 localhost:8000
    RemoteForward 8888 localhost:8888
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
    TCPKeepAlive yes
```

**Connect:**
```bash
ssh vista3d-remote
```

**Using autossh** (recommended for production):
```bash
# Install autossh
brew install autossh  # macOS
sudo apt install autossh  # Ubuntu

# Run with auto-reconnect
autossh -M 0 -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -L 8000:localhost:8000 \
    -R 8888:localhost:8888 \
    user@remote-server
```

## Common Issues and Solutions

### Issue: "Address already in use"

**Error:**
```
bind: Address already in use
channel_setup_fwd_listener_tcpip: cannot listen to port: 8000
```

**Solution:**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
ssh -L 8001:localhost:8000 -R 8888:localhost:8888 user@remote-server
# Then configure frontend to use 8001
```

### Issue: Tunnel disconnects frequently

**Solution 1 - Keep-alive:**
```bash
ssh -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -L 8000:localhost:8000 \
    -R 8888:localhost:8888 \
    user@remote-server
```

**Solution 2 - Use autossh:**
```bash
autossh -M 0 -f -N \
    -o ServerAliveInterval=60 \
    -L 8000:localhost:8000 \
    -R 8888:localhost:8888 \
    user@remote-server
```

**Solution 3 - SSH config:**
Add to `~/.ssh/config`:
```
ServerAliveInterval 60
ServerAliveCountMax 3
TCPKeepAlive yes
```

### Issue: "Permission denied (publickey)"

**Solution - Set up SSH keys:**
```bash
# Generate key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy to remote server
ssh-copy-id user@remote-server

# Test connection
ssh user@remote-server
```

### Issue: Remote server firewall blocks tunnels

**This shouldn't happen** because:
- Tunnels use the SSH connection (port 22)
- No additional ports need to be open
- All traffic goes through the encrypted SSH connection

**But if SSH itself is blocked:**
```bash
# Try different SSH port (if configured)
ssh -p 2222 -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server

# Or use VPN first
```

### Issue: "channel 3: open failed: connect failed: Connection refused"

**This means the remote service isn't running.**

**For forward tunnel error:**
```bash
# Vista3D not running on remote server
# SSH to server and start it:
ssh user@remote-server
cd ~/HPE-Nvidia-Vista-3D/backend
docker-compose up -d
```

**For reverse tunnel error:**
```bash
# Image server not running on Mac
# Start it:
cd ~/HPE-Nvidia-Vista-3D/image_server
docker-compose up -d
```

## Security Considerations

### Use SSH Keys (Not Passwords)

```bash
# Generate key
ssh-keygen -t ed25519

# Copy to server
ssh-copy-id user@remote-server

# Restrict permissions
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

### Limit SSH Key Usage

Add to `~/.ssh/config`:
```
Host vista3d-remote
    HostName your-server.com
    User your-username
    IdentityFile ~/.ssh/vista3d_key
    IdentitiesOnly yes
```

### Firewall Configuration

**On Remote Server:**
```bash
# Only allow SSH (22)
# Ports 8000 and 8888 should NOT be open externally
sudo ufw status

# Should show:
# 22/tcp ALLOW
# 8000/tcp DENY  (or not listed)
# 8888/tcp DENY  (or not listed)
```

**Why:** All traffic goes through SSH tunnel, no need to expose ports.

### Jump Host / Bastion

If your server is behind a bastion:
```bash
ssh -J bastion-host \
    -L 8000:localhost:8000 \
    -R 8888:localhost:8888 \
    user@remote-server
```

Or in `~/.ssh/config`:
```
Host vista3d-remote
    HostName internal-server.local
    User your-username
    ProxyJump bastion-host
    LocalForward 8000 localhost:8000
    RemoteForward 8888 localhost:8888
```

## Performance Optimization

### Enable Compression

For large file transfers:
```bash
ssh -C -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

**Note:** May increase CPU usage but reduces bandwidth.

### Adjust Buffer Sizes

For high-latency connections:
```bash
ssh -o "TCPRcvBuf=524288" \
    -o "TCPSndBuf=524288" \
    -L 8000:localhost:8000 \
    -R 8888:localhost:8888 \
    user@remote-server
```

## Monitoring Tunnels

### Check Active Tunnels

```bash
# Mac: Check what ports are listening
lsof -i :8000  # Forward tunnel
lsof -i :8888  # Reverse tunnel endpoint

# Both should show ssh process
```

### Monitor Connection

```bash
# Watch SSH connection
watch -n 1 'netstat -an | grep :8000'

# Or use continuous ping through tunnel
while true; do
    curl -s http://localhost:8000/v1/vista3d/info > /dev/null && echo "✅ Connected" || echo "❌ Disconnected"
    sleep 5
done
```

### Log SSH Tunnel

```bash
# Run with verbose logging
ssh -v -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server

# More verbose
ssh -vv -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server

# Very verbose
ssh -vvv -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

## Alternative: VPN

If SSH tunnels are problematic, consider a VPN:

### WireGuard (Recommended)

```bash
# Setup WireGuard on both Mac and Ubuntu server
# Then access directly:
# Vista3D: http://10.0.0.2:8000
# Image Server: http://10.0.0.1:8888
```

**Pros:**
- Better performance
- More stable
- Simpler configuration

**Cons:**
- Requires VPN setup on both sides
- May need admin access to install

## Summary

**Standard command:**
```bash
ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

**Recommended for daily use:**
```bash
# Setup once: Add to ~/.ssh/config
Host vista3d
    HostName your-server.com
    User your-username
    LocalForward 8000 localhost:8000
    RemoteForward 8888 localhost:8888
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Then just:
ssh vista3d
```

**Recommended for production:**
```bash
# Install autossh
brew install autossh

# Run with auto-reconnect
autossh -M 0 -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -L 8000:localhost:8000 \
    -R 8888:localhost:8888 \
    user@remote-server
```

## Quick Reference

| Task | Command |
|------|---------|
| Connect | `ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@server` |
| Test forward | `curl http://localhost:8000/v1/vista3d/info` |
| Test reverse | `ssh server "curl http://localhost:8888/health"` |
| Check tunnel | `lsof -i :8000` |
| Disconnect | `Ctrl+C` or `pkill -f "ssh.*8000"` |
| Background | Add `-f -N` flags |
| Auto-reconnect | Use `autossh` |

## See Also

- [REMOTE_SETUP_QUICK_START.md](../REMOTE_SETUP_QUICK_START.md) - Quick setup guide
- [REMOTE_BACKEND_SETUP.md](REMOTE_BACKEND_SETUP.md) - Detailed setup guide
- [OpenSSH Manual](https://man.openbsd.org/ssh) - SSH documentation

