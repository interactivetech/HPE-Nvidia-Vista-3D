# HPE NVIDIA Vista3D Helm Chart

This directory contains the Helm chart for deploying the HPE NVIDIA Vista3D Medical AI Platform on Kubernetes.

## 📁 Chart Structure

```
helm/vista3d/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Default configuration values
├── values-production.yaml        # Production configuration example
├── README.md                     # Chart documentation
└── templates/                    # Kubernetes resource templates
    ├── _helpers.tpl             # Template helpers
    ├── backend-deployment.yaml   # Vista3D backend deployment
    ├── backend-service.yaml      # Vista3D backend service
    ├── frontend-deployment.yaml  # Streamlit frontend deployment
    ├── frontend-service.yaml     # Streamlit frontend service
    ├── image-server-deployment.yaml # Image server deployment
    ├── image-server-service.yaml    # Image server service
    ├── ingress.yaml             # Ingress configuration
    ├── configmap.yaml           # Application configuration
    ├── secret.yaml              # Secrets (NGC API key)
    ├── pvc.yaml                 # Persistent volume claims
    ├── serviceaccount.yaml      # Service account
    └── NOTES.txt                # Post-installation notes
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- NVIDIA GPU nodes with Container Toolkit
- NVIDIA NGC account and API key

### Installation

```bash
# Clone the repository
git clone https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/helm/vista3d

# Install with default values
helm install vista3d . --namespace vista3d --create-namespace

# Install with custom values
helm install vista3d . \
  --namespace vista3d \
  --create-namespace \
  --set secrets.ngcApiKey="your-ngc-api-key" \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host="vista3d.yourdomain.com"

# Install with production values
helm install vista3d . \
  --namespace vista3d \
  --create-namespace \
  --values values-production.yaml
```

## 🏗️ Architecture

The Helm chart deploys three main components:

### 1. Backend (Vista3D Server)
- **Image**: `nvcr.io/nim/nvidia/vista3d:1.0.0`
- **Purpose**: AI-powered medical image segmentation
- **Requirements**: NVIDIA GPU nodes
- **Port**: 8000

### 2. Frontend (Streamlit App)
- **Image**: `dwtwp/vista3d-frontend:latest`
- **Purpose**: Web interface for medical imaging
- **Port**: 8501
- **Scaling**: Horizontal scaling supported

### 3. Image Server
- **Image**: `dwtwp/vista3d-image-server:latest`
- **Purpose**: HTTP server for medical image files
- **Port**: 8888

## ⚙️ Configuration

### Key Configuration Options

| Component | Key | Description | Default |
|-----------|-----|-------------|---------|
| Backend | `backend.enabled` | Enable Vista3D server | `true` |
| Backend | `backend.resources.limits.nvidia.com/gpu` | GPU limit | `1` |
| Frontend | `frontend.replicaCount` | Number of replicas | `2` |
| Image Server | `imageServer.enabled` | Enable image server | `true` |
| Ingress | `ingress.enabled` | Enable external access | `false` |
| Persistence | `persistence.enabled` | Enable persistent storage | `true` |

### GPU Requirements

The backend requires NVIDIA GPU nodes with:
- NVIDIA Container Toolkit installed
- GPU drivers configured
- Proper node selectors and tolerations

### Storage Requirements

- **Output Volume**: ReadWriteMany access for processed data
- **DICOM Volume**: ReadOnlyMany access for source data
- **Recommended**: Fast SSD storage for optimal performance

## 🔧 Customization

### Environment Variables

All environment variables are configurable through the values.yaml file:

```yaml
backend:
  env:
    - name: NGC_API_KEY
      valueFrom:
        secretKeyRef:
          name: vista3d-secrets
          key: ngc-api-key
    - name: VISTA3D_SERVER
      value: "http://localhost:8000"
```

### Resource Limits

Configure resource limits for each component:

```yaml
backend:
  resources:
    limits:
      nvidia.com/gpu: 1
      memory: "16Gi"
      cpu: "4"
    requests:
      nvidia.com/gpu: 1
      memory: "8Gi"
      cpu: "2"
```

### Scaling

Enable horizontal pod autoscaling:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

## 🔒 Security

### Network Policies

Enable network policies for security:

```yaml
networkPolicy:
  enabled: true
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
      ports:
      - protocol: TCP
        port: 8501
```

### Security Contexts

Production-ready security contexts are configured:

```yaml
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
  runAsNonRoot: true
  runAsUser: 1000
```

## 📊 Monitoring

### ServiceMonitor

Enable Prometheus monitoring:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
```

### Logging

View logs for troubleshooting:

```bash
# Backend logs
kubectl logs -l app.kubernetes.io/component=backend --namespace vista3d

# Frontend logs
kubectl logs -l app.kubernetes.io/component=frontend --namespace vista3d

# Image server logs
kubectl logs -l app.kubernetes.io/component=image-server --namespace vista3d
```

## 🚨 Troubleshooting

### Common Issues

1. **Backend pod not starting**
   - Check GPU node availability
   - Verify NVIDIA Container Toolkit
   - Check resource limits

2. **Frontend not accessible**
   - Verify service status
   - Check ingress configuration
   - Verify port forwarding

3. **Image server issues**
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

## 📚 Documentation

- **Chart README**: [helm/vista3d/README.md](vista3d/README.md)
- **Production Values**: [helm/vista3d/values-production.yaml](vista3d/values-production.yaml)
- **Main Project**: [README.md](../README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the chart
5. Submit a pull request

## 📄 License

This Helm chart is licensed under the Apache 2.0 License.
