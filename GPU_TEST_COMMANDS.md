# GPU Test Commands for Ubuntu Server

## The Issue
The exact tag `nvidia/cuda:11.8-base-ubuntu22.04` doesn't exist in Docker Hub.

## Quick Fix - Test with Correct Image

Try one of these working CUDA base images:

```bash
# Option 1: CUDA 11.8.0 (note the .0 version)
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Option 2: CUDA 12.0.0
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Option 3: CUDA 12.2.0
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Option 4: Latest CUDA 11.8 runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-runtime-ubuntu22.04 nvidia-smi
```

## Alternative: Test NVIDIA Docker Without Downloading Large Image

```bash
# Use a smaller test image
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Or test with the actual Vista3D image you'll be using
docker run --rm --gpus all nvcr.io/nim/nvidia/vista3d:1.0.0 nvidia-smi
```

## Verify NVIDIA Runtime is Configured

```bash
# Check Docker daemon configuration
cat /etc/docker/daemon.json

# Should show something like:
# {
#     "default-runtime": "nvidia",
#     "runtimes": {
#         "nvidia": {
#             "args": [],
#             "path": "nvidia-container-runtime"
#         }
#     }
# }
```

## If GPU Test Succeeds

Once the GPU test works, proceed with the setup:

```bash
cd ~/HPE-Nvidia-Vista-3D
python3 setup.py
# Choose option 2 (Backend Only)
```

The setup script will skip the GPU test (since it uses the wrong image tag) but the actual Vista3D container will work fine.

## Manual Setup (Skip GPU Test)

If you want to skip the problematic GPU test in setup.py:

```bash
# The setup already found your NGC credentials in .env
# Just start Vista3D directly

cd ~/HPE-Nvidia-Vista-3D/backend

# Make sure .env exists with your credentials
cat .env | grep NGC_API_KEY

# Start Vista3D
docker compose up -d

# Check logs
docker compose logs -f vista3d-server

# Verify GPU is working in Vista3D
docker exec vista3d-server-standalone nvidia-smi
```

## Expected Output When Working

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  NVIDIA ...          On   | 00000000:00:00.0 Off |                    0 |
| ...                           |   ...MiB / ...MiB    |     ...%      Default |
+-------------------------------+----------------------+----------------------+
```

## Next Steps After GPU Test Works

1. Run setup.py (will use existing NGC credentials)
2. Start backend: `cd backend && docker compose up -d`
3. Verify: `docker compose ps`
4. Test from Mac: Navigate to frontend and run segmentation

