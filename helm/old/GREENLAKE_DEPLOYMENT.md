# Vista3D Deployment on HPE GreenLake for Containers

## 🎯 Overview

This guide provides comprehensive instructions for deploying the HPE NVIDIA Vista3D Medical AI Platform on **HPE GreenLake for Containers**.

**Platform Version:** 1.2.0  
**Target Platform:** HPE GreenLake for Containers  
**Kubernetes Version:** 1.19+

---

## 📋 Prerequisites

### Required Access and Tools

- ✅ **HPE GreenLake Portal Access** - [https://common.cloud.hpe.com](https://common.cloud.hpe.com)
- ✅ **Kubernetes Cluster** - HPE GreenLake for Containers cluster with:
  - At least 1 GPU node (NVIDIA A100, A30, or T4)
  - 2-3 standard compute nodes
  - NVIDIA GPU Operator installed
  - HPE CSI Driver for storage
- ✅ **kubectl** - Configured with your cluster kubeconfig
- ✅ **Helm 3** - Version 3.0 or higher
- ✅ **NVIDIA NGC Account** - Free account at [ngc.nvidia.com](https://ngc.nvidia.com)
- ✅ **NGC API Key** - Starts with `nvapi-`

### Verify Cluster Access

```bash
# Test cluster connectivity
kubectl cluster-info

# Check available nodes
kubectl get nodes -o wide

# Verify GPU nodes
kubectl get nodes -o json | jq '.items[] | 
  select(.status.allocatable."nvidia.com/gpu" != null) | 
  {name: .metadata.name, gpu: .status.allocatable."nvidia.com/gpu"}'

# Check storage classes
kubectl get storageclass
```

---

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
cd helm/vista3d
chmod +x deploy-greenlake.sh
./deploy-greenlake.sh
```

The script will:
1. ✅ Check prerequisites (kubectl, helm, cluster access)
2. ✅ Prompt for NGC API key
3. ✅ Ask for domain name
4. ✅ Create namespace and labels
5. ✅ Create secrets
6. ✅ Apply storage classes
7. ✅ Deploy Vista3D with Helm
8. ✅ Wait for pods to be ready

### Option 2: Manual Deployment

```bash
# 1. Create namespace
kubectl create namespace vista3d

# 2. Label namespace
kubectl label namespace vista3d \
  hpe.com/project=medical-ai \
  hpe.com/team=healthcare \
  hpe.com/platform=greenlake

# 3. Create NGC secret
kubectl create secret generic vista3d-secrets \
  --from-literal=ngc-api-key="nvapi-your-key-here" \
  --namespace vista3d

# 4. Apply storage classes (optional)
kubectl apply -f hpe-storage.yaml

# 5. Deploy with Helm
helm install vista3d . \
  --namespace vista3d \
  --values values-hpe-greenlake.yaml \
  --set ingress.hosts[0].host="vista3d.greenlake.yourdomain.com"
```

---

## ⚙️ Configuration

### Core Configuration File

The main configuration is in **`values-hpe-greenlake.yaml`**. Key sections to customize:

#### 1. Storage Configuration

```yaml
persistence:
  storageClass: "hpe-standard"  # Change to your HPE storage class
  
  output:
    size: 500Gi  # Adjust based on expected data volume
  
  dicom:
    size: 200Gi  # Adjust based on DICOM data size
```

#### 2. Domain Configuration

```yaml
ingress:
  hosts:
    - host: vista3d.greenlake.yourdomain.com  # Your domain
  tls:
    - secretName: vista3d-tls
      hosts:
        - vista3d.greenlake.yourdomain.com
```

#### 3. Resource Limits

```yaml
backend:
  resources:
    limits:
      nvidia.com/gpu: 1
      memory: "32Gi"  # Increase if needed
      cpu: "8"

frontend:
  replicaCount: 3  # Adjust for load
  resources:
    limits:
      memory: "8Gi"
      cpu: "4"
```

#### 4. Node Selectors

```yaml
backend:
  nodeSelector:
    nvidia.com/gpu: "true"
    workload-type: "ai-medical"  # Custom label
```

---

## 📦 Storage Classes

### Pre-configured Storage Classes

The `hpe-storage.yaml` file defines three storage classes:

1. **vista3d-fast** - High-performance storage for active processing
2. **vista3d-standard** - Standard storage for output/results
3. **vista3d-archive** - Archive storage for long-term retention

### Customize for Your Environment

Edit `hpe-storage.yaml` to match your HPE storage configuration:

```yaml
parameters:
  accessProtocol: "iscsi"  # or "fc" for Fibre Channel
  performancePolicy: "high"  # high, medium, or low
```

---

## 🔐 Security

### Secrets Management

**Option 1: Kubernetes Secrets (Default)**
```bash
kubectl create secret generic vista3d-secrets \
  --from-literal=ngc-api-key="nvapi-xxx" \
  --namespace vista3d
```

**Option 2: External Secrets Operator** (Production Recommended)
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vista3d-ngc-secret
  namespace: vista3d
spec:
  secretStoreRef:
    name: hpe-secrets-store
  target:
    name: vista3d-secrets
  data:
  - secretKey: ngc-api-key
    remoteRef:
      key: nvidia/ngc-api-key
```

### Network Policies

Network policies are enabled by default in `values-hpe-greenlake.yaml`:

```yaml
networkPolicy:
  enabled: true
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
```

---

## 🌐 Access and Ingress

### DNS Configuration

1. **Get Ingress IP:**
```bash
kubectl get ingress -n vista3d
# or
kubectl get svc -n ingress-nginx
```

2. **Configure DNS:**
   - In your DNS provider, create an A record
   - Point `vista3d.greenlake.yourdomain.com` to the ingress IP

3. **Verify:**
```bash
nslookup vista3d.greenlake.yourdomain.com
```

### TLS/SSL Certificates

**Option 1: cert-manager (Recommended)**
```bash
# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

**Option 2: Manual Certificate**
```bash
kubectl create secret tls vista3d-tls \
  --cert=path/to/cert.crt \
  --key=path/to/cert.key \
  --namespace vista3d
```

### Port Forwarding (Testing)

```bash
# Forward frontend
kubectl port-forward -n vista3d svc/vista3d-frontend 8501:8501

# Access at http://localhost:8501
```

---

## 📊 Monitoring

### HPE GreenLake Console

1. Navigate to **HPE GreenLake Portal**
2. Go to **Containers** → **Clusters** → **Your Cluster**
3. Select **Monitoring** → **Services**
4. Find **vista3d** services

### Prometheus/Grafana

ServiceMonitor is enabled by default:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

View metrics in Prometheus:
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```

### Viewing Logs

```bash
# All Vista3D logs
kubectl logs -n vista3d -l app.kubernetes.io/name=vista3d --tail=100 -f

# Backend (GPU) logs
kubectl logs -n vista3d -l app.kubernetes.io/component=backend --tail=50

# Frontend logs
kubectl logs -n vista3d -l app.kubernetes.io/component=frontend --tail=50

# Image server logs
kubectl logs -n vista3d -l app.kubernetes.io/component=image-server --tail=50
```

---

## 🔧 Operations

### Scaling

```bash
# Scale frontend
kubectl scale deployment vista3d-frontend --replicas=5 -n vista3d

# Scale image server
kubectl scale deployment vista3d-image-server --replicas=3 -n vista3d

# Auto-scaling is enabled by default via HPA
kubectl get hpa -n vista3d
```

### Updates

```bash
# Update values
helm upgrade vista3d . \
  --namespace vista3d \
  --values values-hpe-greenlake.yaml \
  --reuse-values

# Update just the frontend image
helm upgrade vista3d . \
  --namespace vista3d \
  --reuse-values \
  --set frontend.image.tag=v1.2.1
```

### Backup and Restore

**Create Snapshot:**
```bash
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: vista3d-backup-$(date +%Y%m%d)
  namespace: vista3d
spec:
  volumeSnapshotClassName: hpe-snapshot
  source:
    persistentVolumeClaimName: vista3d-output-pvc
EOF
```

**List Snapshots:**
```bash
kubectl get volumesnapshot -n vista3d
```

### Troubleshooting

**Check Pod Status:**
```bash
kubectl get pods -n vista3d
kubectl describe pod <pod-name> -n vista3d
```

**Check Events:**
```bash
kubectl get events -n vista3d --sort-by='.lastTimestamp'
```

**Check GPU Allocation:**
```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pod -n vista3d -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].metadata.name}')

# Check GPU
kubectl exec -n vista3d $BACKEND_POD -- nvidia-smi
```

**Check Storage:**
```bash
kubectl get pvc -n vista3d
kubectl describe pvc vista3d-output-pvc -n vista3d
```

---

## 🧹 Cleanup

### Uninstall Vista3D

```bash
# Uninstall Helm release
helm uninstall vista3d -n vista3d

# Delete namespace (WARNING: This deletes all data)
kubectl delete namespace vista3d

# Delete storage classes (if needed)
kubectl delete -f hpe-storage.yaml
```

### Preserve Data

```bash
# Uninstall but keep PVCs
helm uninstall vista3d -n vista3d

# PVCs remain - check with:
kubectl get pvc -n vista3d

# Reinstall later to reuse data
helm install vista3d . --namespace vista3d --values values-hpe-greenlake.yaml
```

---

## 📚 Additional Resources

### Documentation
- [Main README](../../README.md)
- [Helm Chart Documentation](README.md)
- [Upgrade Guide](../UPGRADE_GUIDE.md)
- [Release Notes](../RELEASE_NOTES_v1.2.0.md)

### HPE Resources
- [HPE GreenLake Documentation](https://support.hpe.com/connect/s/product?language=en_US&ismnp=0&l5oid=1013083813&kmpmoid=1013083813&cep=on&manualsAndGuidesFilter=66000109,66000108)
- [HPE CSI Driver](https://scod.hpedev.io/csi_driver/)
- [HPE Support Portal](https://support.hpe.com)

### NVIDIA Resources
- [NVIDIA NGC](https://ngc.nvidia.com)
- [Vista3D Documentation](https://docs.nvidia.com/nim/vista3d/)
- [GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)

---

## 🆘 Support

### For Infrastructure Issues
- **HPE GreenLake Support**: Contact via HPE Support Portal
- **HPE Storage Issues**: Check HPE CSI driver logs
- **GPU Issues**: Verify NVIDIA GPU Operator status

### For Application Issues
- **GitHub Issues**: [HPE-Nvidia-Vista-3D Issues](https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D/issues)
- **Email**: dave.wright@hpe.com

---

## ✅ Checklist

### Pre-Deployment
- [ ] HPE GreenLake cluster access configured
- [ ] kubectl and helm installed
- [ ] NGC API key obtained
- [ ] GPU nodes available and labeled
- [ ] Storage classes configured
- [ ] Domain name configured
- [ ] TLS certificates ready (if using custom certs)

### Deployment
- [ ] Namespace created
- [ ] Secrets configured
- [ ] Helm chart deployed
- [ ] All pods running
- [ ] PVCs bound
- [ ] Ingress configured
- [ ] DNS pointing to ingress

### Post-Deployment
- [ ] Web interface accessible
- [ ] GPU allocation verified
- [ ] Test DICOM upload
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Documentation updated
- [ ] Team trained

---

**Last Updated:** October 10, 2025  
**Chart Version:** 1.2.0

