# Minikube Frontend Deployment - Troubleshooting Fixes

## Issues Found and Fixed

### 1. **mk_guide.sh Script**
**Problem:** The script would fail if trying to install when a release already existed.

**Fix:** Added logic to check if the release exists and upgrade it instead of reinstalling.

```bash
# Check if the helm release already exists
if helm list -q | grep -q "^vista3d-frontend$"; then
    echo "vista3d-frontend release already exists. Upgrading..."
    helm upgrade vista3d-frontend ./vista3d -f vista3d/values-frontend-only.yaml
else
    echo "Installing frontend-only release (vista3d-frontend)..."
    helm install vista3d-frontend ./vista3d -f vista3d/values-frontend-only.yaml
fi
```

### 2. **PVC Template (helm/vista3d/templates/pvc.yaml)**
**Problem:** Missing YAML document separator between the two PVC definitions, causing the second PVC to not be created.

**Fix:** Added `---` separator between the PVCs at line 20.

### 3. **values-frontend-only.yaml**
**Problem:** Multiple issues:
- Persistence not properly configured
- Access mode incompatible with minikube (ReadOnlyMany not supported)
- Security context preventing container from writing to required directories

**Fix:** Created a simplified configuration:
```yaml
backend:
  enabled: false

imageServer:
  enabled: false

persistence:
  enabled: true
  output:
    enabled: true
    accessMode: ReadWriteOnce
    size: 10Gi
  dicom:
    enabled: true
    accessMode: ReadWriteOnce
    size: 10Gi

# Override security context to run as root (required for local development)
podSecurityContext:
  runAsUser: 0
  runAsNonRoot: false
  fsGroup: 0

securityContext:
  runAsUser: 0
  runAsNonRoot: false
  allowPrivilegeEscalation: true
  readOnlyRootFilesystem: false
```

### 4. **Minikube Storage Provisioner**
**Problem:** The storage provisioner was crashing on startup.

**Solution:** After recreating minikube (`minikube delete && minikube start`), the provisioner stabilizes after a few restarts.

## Usage

### Start the Frontend
```bash
cd helm
./mk_guide.sh start
```

Wait 1-2 minutes for the pod to become ready, then access the service:

```bash
# Option 1: Port forward (recommended)
kubectl port-forward service/vista3d-frontend-frontend 8501:8501
# Then open: http://localhost:8501

# Option 2: Minikube service (opens tunnel)
minikube service vista3d-frontend-frontend
```

### Stop the Frontend
```bash
cd helm
./mk_guide.sh stop
```

### Check Status
```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/instance=vista3d-frontend

# Check PVCs
kubectl get pvc

# Check logs
kubectl logs -l app.kubernetes.io/instance=vista3d-frontend
```

## Important Notes

1. **Security Context:** The frontend runs as root (UID 0) in this configuration. This is acceptable for local development but should be reconsidered for production.

2. **Storage:** Reduced PVC sizes to 10Gi each for local testing. Adjust in `values-frontend-only.yaml` if needed.

3. **Minikube Limitations:** 
   - Only supports ReadWriteOnce (RWO) access mode
   - Storage provisioner may restart a few times on initial startup (normal)

4. **Image Pull:** First start may take longer as it pulls the `dwtwp/vista3d-frontend:latest` image (~800MB).

## Verified Working Configuration

- **Minikube Version:** 1.37.0
- **Kubernetes Version:** (from minikube)
- **Platform:** Darwin (macOS) ARM64
- **Driver:** Docker

The complete flow has been tested and verified working:
1. `mk_guide.sh start` - ✅ Works
2. Pod startup with PVCs - ✅ Works  
3. Streamlit frontend running - ✅ Works
4. `mk_guide.sh stop` - ✅ Works

