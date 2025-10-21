# HPE GreenLake Deployment Files - Summary

## ✅ Files Created

All HPE GreenLake for Containers deployment files have been successfully created!

### 📁 Location
`/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/helm/vista3d/`

### 📄 Files

1. **`values-hpe-greenlake.yaml`** (14 KB)
   - Main Helm values file optimized for HPE GreenLake
   - Configured for production deployment
   - Includes HPE-specific labels and annotations
   - GPU node selectors and tolerations
   - Storage class configurations
   - Auto-scaling and monitoring enabled

2. **`hpe-storage.yaml`** (2.3 KB)
   - HPE storage class definitions
   - Three storage tiers: fast, standard, archive
   - CSI driver configurations
   - Volume expansion enabled
   - Optimized for medical imaging workloads

3. **`deploy-greenlake.sh`** (6.5 KB) ⭐ *Executable*
   - Automated deployment script
   - Interactive prompts for NGC API key and domain
   - Prerequisites checking
   - Namespace creation and labeling
   - Secret management
   - Full Helm deployment

4. **`GREENLAKE_DEPLOYMENT.md`** (11 KB)
   - Comprehensive deployment guide
   - Quick start instructions
   - Configuration details
   - Security best practices
   - Monitoring and operations
   - Troubleshooting guide
   - Complete checklist

---

## 🚀 Quick Start

### Deploy Vista3D on HPE GreenLake

```bash
cd helm/vista3d
./deploy-greenlake.sh
```

The script will guide you through:
1. ✅ Checking prerequisites
2. ✅ Configuring NGC API key
3. ✅ Setting domain name
4. ✅ Creating namespace and secrets
5. ✅ Deploying Vista3D

### Manual Deployment

```bash
# 1. Create namespace
kubectl create namespace vista3d

# 2. Create secret
kubectl create secret generic vista3d-secrets \
  --from-literal=ngc-api-key="nvapi-your-key" \
  --namespace vista3d

# 3. Deploy
helm install vista3d . \
  --namespace vista3d \
  --values values-hpe-greenlake.yaml \
  --set ingress.hosts[0].host="vista3d.greenlake.yourdomain.com"
```

---

## 📋 Key Features

### HPE GreenLake Optimizations

✅ **Storage Integration**
- HPE CSI driver support
- Three storage tiers (fast/standard/archive)
- Automatic volume expansion
- Snapshot support for backups

✅ **GPU Scheduling**
- Automatic GPU node detection
- Proper node selectors and tolerations
- Affinity rules for optimal placement

✅ **High Availability**
- Frontend: 3 replicas with anti-affinity
- Image Server: 2 replicas
- Pod disruption budgets
- Auto-scaling (HPA) enabled

✅ **Monitoring**
- ServiceMonitor for Prometheus
- HPE GreenLake console integration
- HPE-specific labels and annotations

✅ **Security**
- Network policies enabled
- Security contexts configured
- RBAC with service accounts
- TLS/SSL support

---

## 🎯 Customization

### Common Changes

#### 1. Update Storage Class
```yaml
# In values-hpe-greenlake.yaml
persistence:
  storageClass: "your-hpe-storage-class"
```

#### 2. Adjust Storage Sizes
```yaml
persistence:
  output:
    size: 1Ti  # Increase for more data
  dicom:
    size: 500Gi
```

#### 3. Change Domain
```yaml
ingress:
  hosts:
    - host: vista3d.your-domain.com
```

#### 4. Scale Resources
```yaml
backend:
  resources:
    limits:
      memory: "64Gi"  # For larger workloads
      
frontend:
  replicaCount: 5  # More replicas for high traffic
```

---

## 📊 Deployment Architecture

```
HPE GreenLake Cluster
├── GPU Node(s)
│   └── Vista3D Backend (1 replica)
│       ├── NVIDIA GPU allocated
│       └── Connects to HPE Storage
├── Compute Nodes
│   ├── Frontend Pods (3 replicas)
│   │   └── Streamlit Web Interface
│   └── Image Server Pods (2 replicas)
│       └── Medical image file serving
├── Storage
│   ├── Output PVC (500Gi, ReadWriteMany)
│   └── DICOM PVC (200Gi, ReadOnlyMany)
└── Ingress
    └── NGINX Ingress Controller
        └── TLS/SSL termination
```

---

## 🔍 Verification

### Check Deployment Status

```bash
# All pods
kubectl get pods -n vista3d

# Services
kubectl get svc -n vista3d

# Storage
kubectl get pvc -n vista3d

# Ingress
kubectl get ingress -n vista3d

# GPU allocation
kubectl describe node | grep -A 5 "nvidia.com/gpu"
```

### Expected Output

```
NAME                                  READY   STATUS    RESTARTS   AGE
vista3d-backend-xxxxxxxxx-xxxxx       1/1     Running   0          5m
vista3d-frontend-xxxxxxxxx-xxxxx      1/1     Running   0          5m
vista3d-frontend-xxxxxxxxx-xxxxx      1/1     Running   0          5m
vista3d-frontend-xxxxxxxxx-xxxxx      1/1     Running   0          5m
vista3d-image-server-xxxxxxxx-xxxxx   1/1     Running   0          5m
vista3d-image-server-xxxxxxxx-xxxxx   1/1     Running   0          5m
```

---

## 📚 Documentation

### Primary Documentation
- **`GREENLAKE_DEPLOYMENT.md`** - Complete deployment guide
- **`values-hpe-greenlake.yaml`** - Configuration reference (commented)
- **`../UPGRADE_GUIDE.md`** - Upgrade procedures
- **`../RELEASE_NOTES_v1.2.0.md`** - What's new

### Related Documentation
- **`README.md`** - Helm chart overview
- **`../README.md`** - Main project README
- **`../../docs/HELM.md`** - Kubernetes deployment guide

---

## 🛠️ Operations

### Common Commands

```bash
# View logs
kubectl logs -n vista3d -l app.kubernetes.io/name=vista3d --tail=100 -f

# Scale frontend
kubectl scale deployment vista3d-frontend --replicas=5 -n vista3d

# Check GPU usage
kubectl exec -n vista3d <backend-pod> -- nvidia-smi

# Port-forward for testing
kubectl port-forward -n vista3d svc/vista3d-frontend 8501:8501

# Update deployment
helm upgrade vista3d . \
  --namespace vista3d \
  --values values-hpe-greenlake.yaml \
  --reuse-values

# Rollback
helm rollback vista3d -n vista3d

# Uninstall
helm uninstall vista3d -n vista3d
```

---

## 🆘 Troubleshooting

### Pod Issues
```bash
# Check pod events
kubectl describe pod <pod-name> -n vista3d

# Check logs
kubectl logs <pod-name> -n vista3d --previous

# Check resource constraints
kubectl top pods -n vista3d
```

### Storage Issues
```bash
# Check PVC status
kubectl get pvc -n vista3d
kubectl describe pvc <pvc-name> -n vista3d

# Check storage class
kubectl get storageclass
```

### GPU Issues
```bash
# Check GPU nodes
kubectl get nodes -o json | \
  jq '.items[] | select(.status.allocatable."nvidia.com/gpu" != null)'

# Check GPU operator
kubectl get pods -n gpu-operator-resources

# Verify GPU in pod
kubectl exec -n vista3d <backend-pod> -- nvidia-smi
```

---

## ✨ Next Steps

### 1. Prerequisites
- [ ] Access HPE GreenLake console
- [ ] Download kubeconfig
- [ ] Install kubectl and helm
- [ ] Obtain NGC API key

### 2. Deployment
- [ ] Review `values-hpe-greenlake.yaml`
- [ ] Customize domain and storage settings
- [ ] Run `./deploy-greenlake.sh`
- [ ] Verify all pods are running

### 3. Configuration
- [ ] Configure DNS for your domain
- [ ] Set up TLS certificates
- [ ] Upload test DICOM data
- [ ] Test AI segmentation

### 4. Operations
- [ ] Set up monitoring dashboards
- [ ] Configure backup schedules
- [ ] Document access procedures
- [ ] Train users on the platform

---

## 📞 Support

### HPE Support
- **Infrastructure Issues**: HPE GreenLake Support
- **Storage Issues**: HPE CSI Driver documentation
- **GPU Issues**: NVIDIA GPU Operator

### Application Support
- **GitHub**: [HPE-Nvidia-Vista-3D Issues](https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D/issues)
- **Email**: dave.wright@hpe.com

---

## 📝 Change Log

**October 10, 2025**
- ✅ Created `values-hpe-greenlake.yaml`
- ✅ Created `hpe-storage.yaml`
- ✅ Created `deploy-greenlake.sh`
- ✅ Created `GREENLAKE_DEPLOYMENT.md`
- ✅ All files ready for deployment

---

**Ready to deploy! 🚀**

For detailed instructions, see: **`GREENLAKE_DEPLOYMENT.md`**

