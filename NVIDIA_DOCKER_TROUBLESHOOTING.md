# NVIDIA Docker Troubleshooting - Exit Code 125

## Problem
`docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi` fails with exit code 125

## Common Causes & Solutions

### 1. Docker Daemon Not Restarted After NVIDIA Toolkit Installation

**Solution:**
```bash
sudo systemctl restart docker
```

Then test again:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. NVIDIA Container Runtime Not Configured

**Check current Docker configuration:**
```bash
sudo cat /etc/docker/daemon.json
```

**If file doesn't exist or missing NVIDIA runtime, create/update it:**
```bash
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF
```

**Restart Docker:**
```bash
sudo systemctl restart docker
```

### 3. Alternative Configuration (If Above Doesn't Work)

**Configure Docker to use NVIDIA as default runtime:**
```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 4. Verify NVIDIA Container Toolkit Installation

```bash
# Check if nvidia-container-toolkit is installed
dpkg -l | grep nvidia-container-toolkit

# Check if nvidia-container-runtime is installed
which nvidia-container-runtime

# Check NVIDIA Container CLI
nvidia-container-cli --version
```

**If not installed properly, reinstall:**
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### 5. Check Docker Version Compatibility

**New Docker versions (28.x) may need different configuration:**
```bash
docker --version
```

If using Docker 28.x, try this configuration:
```bash
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
sudo systemctl restart docker
```

### 6. Test Step by Step

**Test 1: Basic Docker**
```bash
docker run --rm hello-world
```

**Test 2: NVIDIA SMI on Host**
```bash
nvidia-smi
```

**Test 3: NVIDIA Docker without --gpus flag**
```bash
docker run --rm --runtime=nvidia nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Test 4: NVIDIA Docker with --gpus flag**
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 7. Check Docker Logs

```bash
sudo journalctl -u docker.service | tail -50
```

Look for NVIDIA runtime errors.

## Quick Fix (Most Common Solution)

**For Docker 28.x on Ubuntu:**
```bash
# Configure NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default

# Restart Docker
sudo systemctl restart docker

# Test
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## After Fix - Verify Configuration

```bash
# Check Docker daemon config
cat /etc/docker/daemon.json

# Should show NVIDIA runtime configuration
```

## Run Setup Again

Once the test command works, run the setup script again:
```bash
python3 setup.py
# Choose option 2 (Backend Only)
```

## Still Not Working?

**Check user permissions:**
```bash
# Add user to docker group if not already
sudo usermod -aG docker $USER

# Log out and back in, or run
newgrp docker

# Test without sudo
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Check NVIDIA driver:**
```bash
nvidia-smi
# Should show driver version and GPUs
```

**Check kernel modules:**
```bash
lsmod | grep nvidia
# Should show nvidia modules loaded
```

