# HPE NVIDIA Vista3D Helm Chart

This Helm chart deploys the HPE NVIDIA Vista3D Medical AI Platform on Kubernetes. The platform provides AI-powered medical image segmentation with 3D visualization capabilities.

**Chart Version**: 1.1.0  
**App Version**: 1.1.0

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- NVIDIA GPU nodes with Container Toolkit installed
- NVIDIA NGC account and API key

## Installation

### Add the Helm repository (if published)
```bash
# Note: This chart is not yet published to a public repository
# Use the local installation method below instead
# helm repo add vista3d https://your-helm-repo.com
# helm repo update
```

### Install from local chart
```bash
# Clone the repository
git clone https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/helm/vista3d

# Install the chart
helm install vista3d . --namespace vista3d --create-namespace
```

### Install with custom values
```bash
helm install vista3d . \
  --namespace vista3d \
  --create-namespace \
  --set secrets.ngcApiKey="your-ngc-api-key" \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host="vista3d.yourdomain.com"
```

## Configuration

The following table lists the configurable parameters and their default values:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable Vista3D backend server | `true` |
| `frontend.enabled` | Enable Streamlit frontend | `true` |
| `imageServer.enabled` | Enable image server | `true` |
| `ingress.enabled` | Enable ingress | `false` |
| `persistence.enabled` | Enable persistent volumes | `true` |
| `secrets.ngcApiKey` | NVIDIA NGC API key | `""` |

### Backend Configuration

The backend requires NVIDIA GPU nodes. Configure node selectors and tolerations:

```yaml
backend:
  enabled: true
  nodeSelector:
    nvidia.com/gpu: "true"
  tolerations:
    - key: nvidia.com/gpu
      operator: Exists
      effect: NoSchedule
  resources:
    limits:
      nvidia.com/gpu: 1
      memory: "16Gi"
      cpu: "4"
```

### Frontend Configuration

The frontend can be scaled horizontally:

```yaml
frontend:
  enabled: true
  replicaCount: 2
  resources:
    limits:
      memory: "4Gi"
      cpu: "2"
```

### Ingress Configuration

Enable ingress for external access:

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: vista3d.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
          service: vista3d-frontend
```

### Persistence Configuration

Configure persistent volumes for data storage:

```yaml
persistence:
  enabled: true
  storageClass: "fast-ssd"
  output:
    size: 100Gi
    accessMode: ReadWriteMany
  dicom:
    size: 50Gi
    accessMode: ReadOnlyMany
```

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `backend.enabled` | bool | `true` | Enable Vista3D backend server |
| `backend.replicaCount` | int | `1` | Number of backend replicas |
| `backend.image.repository` | string | `"nvcr.io/nim/nvidia/vista3d"` | Backend image repository |
| `backend.image.tag` | string | `"1.0.0"` | Backend image tag |
| `backend.resources.limits.nvidia.com/gpu` | int | `1` | GPU resource limit |
| `frontend.enabled` | bool | `true` | Enable Streamlit frontend |
| `frontend.replicaCount` | int | `2` | Number of frontend replicas |
| `frontend.image.repository` | string | `"dwtwp/vista3d-frontend"` | Frontend image repository |
| `imageServer.enabled` | bool | `true` | Enable image server |
| `imageServer.image.repository` | string | `"dwtwp/vista3d-image-server"` | Image server repository |
| `ingress.enabled` | bool | `false` | Enable ingress |
| `ingress.className` | string | `"nginx"` | Ingress class name |
| `persistence.enabled` | bool | `true` | Enable persistent volumes |
| `persistence.storageClass` | string | `""` | Storage class for PVCs |
| `secrets.create` | bool | `true` | Create secrets |
| `secrets.ngcApiKey` | string | `""` | NVIDIA NGC API key |

## Usage

### 1. Deploy the Chart

```bash
helm install vista3d . --namespace vista3d --create-namespace
```

### 2. Configure NVIDIA NGC API Key

```bash
kubectl create secret generic vista3d-secrets \
  --from-literal=ngc-api-key="your-ngc-api-key" \
  --namespace vista3d
```

### 3. Access the Application

If ingress is enabled:
```bash
# Access via ingress hostname
curl http://vista3d.yourdomain.com
```

If ingress is disabled:
```bash
# Port forward to access locally
kubectl port-forward service/vista3d-frontend 8501:8501 --namespace vista3d
```

### 4. Upload Medical Data

1. Access the web interface
2. Navigate to the Tools page
3. Upload DICOM or NIFTI files
4. Run AI segmentation
5. View 3D visualizations

## Scaling

### Horizontal Pod Autoscaling

Enable HPA for the frontend:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

### Manual Scaling

```bash
# Scale frontend
kubectl scale deployment vista3d-frontend --replicas=5 --namespace vista3d

# Scale image server
kubectl scale deployment vista3d-image-server --replicas=3 --namespace vista3d
```

## Monitoring

### Enable ServiceMonitor for Prometheus

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
```

### View Logs

```bash
# Backend logs
kubectl logs -l app.kubernetes.io/component=backend --namespace vista3d

# Frontend logs
kubectl logs -l app.kubernetes.io/component=frontend --namespace vista3d

# Image server logs
kubectl logs -l app.kubernetes.io/component=image-server --namespace vista3d
```

## Troubleshooting

### Common Issues

1. **Backend pod not starting**
   - Check if GPU nodes are available
   - Verify NVIDIA Container Toolkit installation
   - Check resource limits and requests

2. **Frontend not accessible**
   - Verify service is running
   - Check ingress configuration
   - Verify port forwarding

3. **Image server not serving files**
   - Check persistent volume claims
   - Verify file permissions
   - Check image server logs

### Debug Commands

```bash
# Check pod status
kubectl get pods --namespace vista3d

# Check services
kubectl get svc --namespace vista3d

# Check persistent volumes
kubectl get pvc --namespace vista3d

# Check events
kubectl get events --namespace vista3d --sort-by='.lastTimestamp'
```

## Uninstallation

```bash
helm uninstall vista3d --namespace vista3d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the chart
5. Submit a pull request

## License

This chart is licensed under the Apache 2.0 License.
