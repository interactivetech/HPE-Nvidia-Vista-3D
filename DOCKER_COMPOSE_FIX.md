# Docker Compose Version Fix

## The Problem

If you see this error:
```
docker-compose: command not found
```

This means you have **Docker Compose V2** installed (which is the new version), but the startup scripts were looking for the old V1 command.

## The Solution

### Option 1: Regenerate Scripts (Recommended)

The setup scripts have been updated to auto-detect both Docker Compose V1 and V2.

**On your Ubuntu server:**
```bash
cd ~/HPE-Nvidia-Vista-3D
git pull
cd backend
python3 setup_backend_remote.py
```

This will regenerate the startup script with proper V1/V2 detection.

### Option 2: Manual Fix

If you already have a `start_backend.sh` or `start_remote_backend.sh` file, you can edit it:

**Find this line:**
```bash
docker-compose up -d
```

**Replace with:**
```bash
# Detect docker-compose command (V1 vs V2)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

$COMPOSE_CMD up -d
```

### Option 3: Use docker compose directly

Just use the new Docker Compose V2 command directly:

```bash
cd ~/HPE-Nvidia-Vista-3D/backend
docker compose up -d
```

## Understanding Docker Compose Versions

### V1 (Old - Standalone)
- Command: `docker-compose` (with hyphen)
- Installed separately from Docker
- Being deprecated

### V2 (New - Plugin)
- Command: `docker compose` (with space)
- Built into Docker as a plugin
- Current standard

Both versions work identically, just different commands.

## Quick Commands

### Start Backend

**V2 (new):**
```bash
cd ~/HPE-Nvidia-Vista-3D/backend
docker compose up -d
```

**V1 (old):**
```bash
cd ~/HPE-Nvidia-Vista-3D/backend
docker-compose up -d
```

### Stop Backend

**V2:**
```bash
docker compose down
```

**V1:**
```bash
docker-compose down
```

### View Logs

**V2:**
```bash
docker compose logs -f
```

**V1:**
```bash
docker-compose logs -f
```

## Check Which Version You Have

```bash
# Check for V2 (plugin)
docker compose version

# Check for V1 (standalone)
docker-compose version
```

## Your Next Steps

1. **Pull the latest code** on your Ubuntu server:
   ```bash
   cd ~/HPE-Nvidia-Vista-3D
   git pull
   ```

2. **Regenerate the startup script**:
   ```bash
   cd backend
   python3 setup_backend_remote.py
   ```

3. **Start the backend**:
   ```bash
   ./start_remote_backend.sh
   # Or manually:
   docker compose up -d
   ```

The new scripts will automatically detect which version you have and use the correct command!

