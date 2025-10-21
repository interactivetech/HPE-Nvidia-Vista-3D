# Helm Chart Upgrade Guide

## Upgrading from v1.1.0 to v1.2.0

### Overview

Version 1.2.0 introduces enhanced colormap support for better medical imaging visualization. This is a backward-compatible release that requires no configuration changes.

### What's New

#### Enhanced Colormap Support
- **23+ Built-in NiiVue Colormaps**: The frontend now includes native support for 23 built-in colormaps including:
  - Standard scientific: gray, jet, hot, cool, warm, viridis, plasma, magma, inferno
  - Medical-specific: Enhanced CT, MRI, and anatomical visualization options
  - Color schemes: spring, summer, autumn, winter, rainbow, hsv, bone, copper, cubehelix
  
#### Performance Improvements
- Optimized colormap loading with intelligent caching
- Reduced initial load time for colormap selection
- Better memory management for colormap data

#### UI Enhancements
- Improved colormap selector organization
- Medical imaging colormaps prioritized in the UI
- Better visual preview of colormaps

### Upgrade Process

#### 1. Pull the Latest Chart

```bash
cd HPE-Nvidia-Vista-3D
git pull origin main
cd helm/vista3d
```

#### 2. Review Changes

```bash
# View what will change
helm diff upgrade vista3d . --namespace vista3d
```

#### 3. Upgrade the Release

```bash
# Standard upgrade
helm upgrade vista3d . --namespace vista3d

# With custom values
helm upgrade vista3d . \
  --namespace vista3d \
  --values values-production.yaml
```

#### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n vista3d

# Verify frontend pods are running
kubectl get pods -l app.kubernetes.io/component=frontend -n vista3d

# Check the new version
kubectl get deployment vista3d-frontend -n vista3d -o jsonpath='{.spec.template.spec.containers[0].image}'
```

### Breaking Changes

**None** - This is a fully backward-compatible release.

### Configuration Changes

No configuration changes are required. All existing configurations will continue to work.

### Rollback Instructions

If you need to rollback to version 1.1.0:

```bash
# View revision history
helm history vista3d --namespace vista3d

# Rollback to previous version
helm rollback vista3d --namespace vista3d
```

### Testing the Upgrade

After upgrading, verify the new colormap functionality:

1. Access the Vista3D web interface
2. Navigate to the NiiVue Viewer
3. Open the colormap selector
4. Verify built-in colormaps are available:
   - gray, jet, viridis, plasma, magma, inferno, etc.
5. Test switching between colormaps
6. Verify medical imaging colormaps work correctly

### Troubleshooting

#### Frontend Pods Not Starting

If frontend pods fail to start after upgrade:

```bash
# Check pod logs
kubectl logs -l app.kubernetes.io/component=frontend -n vista3d

# Check events
kubectl get events -n vista3d --sort-by='.lastTimestamp'

# If needed, restart deployment
kubectl rollout restart deployment/vista3d-frontend -n vista3d
```

#### Colormap Loading Issues

If colormaps don't load properly:

1. Verify the frontend image was updated:
   ```bash
   kubectl describe pod -l app.kubernetes.io/component=frontend -n vista3d | grep Image:
   ```

2. Check for any error messages in the frontend logs:
   ```bash
   kubectl logs -l app.kubernetes.io/component=frontend -n vista3d | grep -i colormap
   ```

3. Clear browser cache and reload the web interface

### Docker Image Requirements

Ensure you're using the latest frontend image that includes the colormap changes:

- **Frontend**: `dwtwp/vista3d-frontend:latest` (must be rebuilt after pulling the latest code)
- **Backend**: `nvcr.io/nim/nvidia/vista3d:1.0.0` (no changes)
- **Image Server**: `dwtwp/vista3d-image-server:latest` (no changes)

### Rebuilding Docker Images

If you're using custom-built images, rebuild the frontend:

```bash
cd frontend
docker build -t dwtwp/vista3d-frontend:latest .
docker push dwtwp/vista3d-frontend:latest
```

Then upgrade the Helm release to pick up the new image.

### Support

For issues or questions:
- GitHub Issues: https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D/issues
- Documentation: See the main README.md
- Email: dave.wright@hpe.com

### See Also

- [CHANGELOG.md](vista3d/CHANGELOG.md) - Detailed list of changes
- [README.md](vista3d/README.md) - Chart documentation
- [values.yaml](vista3d/values.yaml) - Configuration options

