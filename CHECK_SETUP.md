# Vista3D Connectivity Diagnostic Results

## ✅ What's Working

1. **Frontend → Backend**: ✅ WORKING
   - Frontend container can reach Vista3D backend at `http://host.docker.internal:8000`
   - SSH forward tunnel is working correctly

2. **Environment Variables**: ✅ CORRECT
   - `VISTA3D_SERVER=http://host.docker.internal:8000`
   - `VISTA3D_IMAGE_SERVER_URL=http://localhost:8888`

3. **Image Server**: ✅ RUNNING
   - Image server is accessible at `http://image-server:8888` from frontend container
   - Files are available and accessible

## ❌ What's NOT Working

### CRITICAL ISSUE: Reverse SSH Tunnel

The Vista3D backend (on Ubuntu) **cannot reach the image server** at `localhost:8888`.

**Error from backend:**
```
Failed to fetch image: HTTPConnectionPool(host='localhost', port=8888): 
Max retries exceeded... Connection refused
```

This means the **reverse SSH tunnel is not working** on the Ubuntu server.

## 🔧 Fix: Check Reverse SSH Tunnel on Ubuntu

### On Your Ubuntu Server

SSH into your Ubuntu server and run:

```bash
# Check if port 8888 is listening
netstat -tln | grep 8888

# Or
lsof -nP -iTCP:8888 -sTCP:LISTEN
```

**Expected**: You should see port 8888 listening (from the SSH reverse tunnel)

**If you see nothing**: The reverse tunnel isn't active.

### SSH Tunnel Command Requirements

Your SSH command must have:
```bash
-R 8888:0.0.0.0:8888
```

**NOT:**
- `-R 8888:localhost:8888` (won't work from Docker container)
- `-R 8888:127.0.0.1:8888` (won't work from Docker container)

**Full command from your Mac:**
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```

The **`0.0.0.0`** part is crucial - it allows the Docker container on Ubuntu to reach the tunneled port.

### Ubuntu Server SSH Configuration

Your Ubuntu server's `/etc/ssh/sshd_config` must have:

```
GatewayPorts yes
```

Or:

```
GatewayPorts clientspecified
```

Without this, the `-R 8888:0.0.0.0:8888` won't bind to 0.0.0.0 and Docker containers won't be able to reach it.

**To fix:**

1. Edit SSH config on Ubuntu:
   ```bash
   sudo nano /etc/ssh/sshd_config
   ```

2. Add or change:
   ```
   GatewayPorts clientspecified
   ```

3. Restart SSH:
   ```bash
   sudo systemctl restart sshd
   ```

4. Reconnect your SSH tunnel from your Mac

### Quick Test on Ubuntu

Once you've fixed the SSH config and reconnected, test from Ubuntu:

```bash
# Should return OK
curl http://localhost:8888/health

# Should return health status from your Mac's image server
curl http://0.0.0.0:8888/health
```

## 📋 Quick Test Script

Save this as `/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/frontend/quick_test.sh`:

```bash
#!/bin/bash
echo "Testing Vista3D connectivity..."
echo ""
echo "1. Frontend → Backend:"
docker exec vista3d-frontend-standalone curl -s -o /dev/null -w "HTTP %{http_code}\n" http://host.docker.internal:8000/v1/vista3d/info
echo ""
echo "2. SSH Tunnel Status:"
ps aux | grep "[s]sh.*8000.*8888" && echo "✅ SSH tunnel running" || echo "❌ No SSH tunnel"
echo ""
echo "3. Backend accessibility (from Mac):"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/v1/vista3d/info
echo ""
echo "If test 1 and 3 pass, the issue is the reverse SSH tunnel on Ubuntu."
echo "Check Ubuntu server: netstat -tln | grep 8888"
```

Run: `bash /Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/frontend/quick_test.sh`

## 🎯 Summary

The setup is 95% correct! The only issue is:

**The reverse SSH tunnel on Ubuntu needs `GatewayPorts` enabled so Docker containers can reach the tunneled port.**

Once that's fixed, everything will work!

