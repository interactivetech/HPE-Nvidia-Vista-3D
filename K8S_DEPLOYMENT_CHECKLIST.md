# Kubernetes Deployment Checklist for Vista3D

## 📋 Pre-Deployment Checklist

### **Phase 1: Docker Images** (REQUIRED)

- [ ] **1.1 Build Docker Images**
  ```bash
  ./build-and-push.sh 1.2.0 [your-registry] no  # Build only, don't push
  ```

- [ ] **1.2 Test Images Locally**
  ```bash
  # Test frontend
  docker run -p 8501:8501 dwtwp/vista3d-frontend:1.2.0
  
  # Test image server
  docker run -p 8888:8888 dwtwp/vista3d-image-server:1.2.0
  ```

- [ ] **1.3 Push to Registry**
  ```bash
  # Option A: Docker Hub
  docker login
  ./build-and-push.sh 1.2.0 "" yes
  
  # Option B: Private Registry
  docker login your-registry.com
  ./build-and-push.sh 1.2.0 your-registry.com yes
  ```

- [ ] **1.4 Verify Images in Registry**
  ```bash
  # Docker Hub
  docker pull dwtwp/vista3d-frontend:1.2.0
  docker pull dwtwp/vista3d-image-server:1.2.0
  
  # Or check on Docker Hub website
  ```

---

### **Phase 2: Kubernetes Cluster** (REQUIRED)

- [ ] **2.1 Verify Cluster Access**
  ```bash
  kubectl cluster-info
  kubectl get nodes
  ```

- [ ] **2.2 Check GPU Nodes**
  ```bash
  kubectl get nodes -o json | \
    jq '.items[] | select(.status.allocatable."nvidia.com/gpu" != null) | 
    {name: .metadata.name, gpu: .status.allocatable."nvidia.com/gpu"}'
  ```

- [ ] **2.3 Verify GPU Operator**
  ```bash
  kubectl get pods -n gpu-operator-resources
  # or
  kubectl get pods -n nvidia-gpu-operator
  ```

- [ ] **2.4 Check Storage Classes**
  ```bash
  kubectl get storageclass
  # Ensure you have a ReadWriteMany capable storage class
  ```

- [ ] **2.5 Verify NVIDIA Container Toolkit**
  ```bash
  # On GPU node
  nvidia-smi
  docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
  ```

---

### **Phase 3: Prerequisites Installation** (REQUIRED)

- [ ] **3.1 Install/Verify kubectl**
  ```bash
  kubectl version --client
  ```

- [ ] **3.2 Install/Verify Helm 3**
  ```bash
  helm version
  # Should be v3.x.x
  ```

- [ ] **3.3 Install Ingress Controller** (if not present)
  ```bash
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm install nginx-ingress ingress-nginx/ingress-nginx \
    --namespace ingress-nginx --create-namespace
  ```

---

### **Phase 4: Configuration** (REQUIRED)

- [ ] **4.1 Obtain NGC API Key**
  - Visit https://ngc.nvidia.com
  - Create account if needed
  - Generate API key (starts with `nvapi-`)

- [ ] **4.2 Configure Domain Name**
  - Decide on domain: `vista3d.yourdomain.com`
  - Prepare to configure DNS

- [ ] **4.3 Prepare Storage Configuration**
  - Identify storage class name
  - Estimate storage sizes needed:
    - Output: 100Gi - 1Ti
    - DICOM: 50Gi - 500Gi

- [ ] **4.4 Review Helm Values**
  ```bash
  cd helm/vista3d
  # Review and customize:
  nano values-hpe-greenlake.yaml  # For HPE GreenLake
  # or
  nano values-production.yaml      # For other platforms
  ```

---

### **Phase 5: Deployment** (EXECUTION)

#### **For HPE GreenLake:**

- [ ] **5.1 Deploy Using Script**
  ```bash
  cd helm/vista3d
  ./deploy-greenlake.sh
  ```

#### **For Other Kubernetes:**

- [ ] **5.1 Create Namespace**
  ```bash
  kubectl create namespace vista3d
  ```

- [ ] **5.2 Create NGC Secret**
  ```bash
  kubectl create secret generic vista3d-secrets \
    --from-literal=ngc-api-key="nvapi-YOUR-KEY" \
    --namespace vista3d
  ```

- [ ] **5.3 Deploy with Helm**
  ```bash
  helm install vista3d . \
    --namespace vista3d \
    --values values-production.yaml \
    --set frontend.image.tag=1.2.0 \
    --set imageServer.image.tag=1.2.0 \
    --set ingress.hosts[0].host="vista3d.yourdomain.com"
  ```

- [ ] **5.4 Wait for Pods**
  ```bash
  kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=vista3d \
    -n vista3d \
    --timeout=600s
  ```

---

### **Phase 6: Verification** (REQUIRED)

- [ ] **6.1 Check Pod Status**
  ```bash
  kubectl get pods -n vista3d
  # All pods should be Running
  ```

- [ ] **6.2 Check Services**
  ```bash
  kubectl get svc -n vista3d
  ```

- [ ] **6.3 Check PVCs**
  ```bash
  kubectl get pvc -n vista3d
  # Should be Bound
  ```

- [ ] **6.4 Check Ingress**
  ```bash
  kubectl get ingress -n vista3d
  ```

- [ ] **6.5 Check Backend Logs**
  ```bash
  kubectl logs -n vista3d -l app.kubernetes.io/component=backend --tail=50
  # Should show successful startup
  ```

- [ ] **6.6 Verify GPU Allocation**
  ```bash
  BACKEND_POD=$(kubectl get pod -n vista3d -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].metadata.name}')
  kubectl exec -n vista3d $BACKEND_POD -- nvidia-smi
  # Should show GPU info
  ```

---

### **Phase 7: Network Configuration** (REQUIRED)

- [ ] **7.1 Get Ingress IP**
  ```bash
  kubectl get ingress -n vista3d -o wide
  # or
  kubectl get svc -n ingress-nginx
  ```

- [ ] **7.2 Configure DNS**
  - Create A record pointing to ingress IP
  - Domain: `vista3d.yourdomain.com` → `<ingress-ip>`

- [ ] **7.3 Verify DNS**
  ```bash
  nslookup vista3d.yourdomain.com
  dig vista3d.yourdomain.com
  ```

- [ ] **7.4 Set Up TLS (Optional but Recommended)**
  ```bash
  # Install cert-manager
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
  
  # Create ClusterIssuer (see helm/vista3d/GREENLAKE_DEPLOYMENT.md)
  ```

---

### **Phase 8: Testing** (REQUIRED)

- [ ] **8.1 Access Web Interface**
  ```bash
  # Via ingress
  https://vista3d.yourdomain.com
  
  # Or port-forward
  kubectl port-forward -n vista3d svc/vista3d-frontend 8501:8501
  # Visit http://localhost:8501
  ```

- [ ] **8.2 Upload Test DICOM**
  - Access web interface
  - Navigate to Tools page
  - Upload sample DICOM files

- [ ] **8.3 Run Segmentation**
  - Select uploaded DICOM
  - Run Vista3D segmentation
  - Verify results appear

- [ ] **8.4 Check 3D Viewer**
  - View segmentation results
  - Test colormap selection
  - Verify 3D rendering works

- [ ] **8.5 Monitor Resources**
  ```bash
  kubectl top pods -n vista3d
  kubectl top nodes
  ```

---

### **Phase 9: Monitoring & Operations** (RECOMMENDED)

- [ ] **9.1 Set Up Monitoring**
  ```bash
  # Check if ServiceMonitor is created
  kubectl get servicemonitor -n vista3d
  ```

- [ ] **9.2 Configure Alerts** (if using Prometheus)
  - Set up alerts for pod failures
  - Monitor GPU utilization
  - Track storage usage

- [ ] **9.3 Set Up Log Aggregation**
  ```bash
  # If using ELK/Loki
  kubectl logs -n vista3d -l app.kubernetes.io/name=vista3d -f
  ```

- [ ] **9.4 Configure Backups**
  ```bash
  # Set up VolumeSnapshot schedules
  # See helm/vista3d/GREENLAKE_DEPLOYMENT.md for examples
  ```

---

### **Phase 10: Documentation** (RECOMMENDED)

- [ ] **10.1 Document Access**
  - Record URL: `https://vista3d.yourdomain.com`
  - Document admin credentials
  - Note NGC API key location

- [ ] **10.2 Create Runbook**
  - Deployment procedures
  - Update procedures
  - Rollback procedures
  - Troubleshooting steps

- [ ] **10.3 Train Users**
  - Provide access instructions
  - Demo key features
  - Share documentation links

---

## 🚨 Common Issues & Solutions

### Issue: Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n vista3d

# Check logs
kubectl logs <pod-name> -n vista3d --previous

# Common causes:
# - Image pull errors (check registry access)
# - Resource constraints (check node capacity)
# - PVC binding issues (check storage class)
```

### Issue: Backend Pod Pending

```bash
# Check GPU node availability
kubectl get nodes -l nvidia.com/gpu=true

# Check GPU resources
kubectl describe node <gpu-node-name> | grep -A 5 "nvidia.com/gpu"

# Verify GPU operator
kubectl get pods -n gpu-operator-resources
```

### Issue: PVC Not Binding

```bash
# Check PVC status
kubectl get pvc -n vista3d
kubectl describe pvc <pvc-name> -n vista3d

# Check storage class
kubectl get storageclass
kubectl describe storageclass <storage-class-name>

# Verify provisioner
kubectl get pods -n kube-system | grep provisioner
```

### Issue: Ingress Not Working

```bash
# Check ingress
kubectl describe ingress -n vista3d

# Check ingress controller
kubectl get pods -n ingress-nginx

# Test service directly
kubectl port-forward -n vista3d svc/vista3d-frontend 8501:8501
```

---

## 📞 Support Resources

- **Documentation**: `helm/vista3d/GREENLAKE_DEPLOYMENT.md`
- **GitHub Issues**: https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D/issues
- **Helm Chart**: `helm/vista3d/README.md`
- **Upgrade Guide**: `helm/UPGRADE_GUIDE.md`

---

## ✅ Final Checklist Summary

**Critical Path:**
1. ✅ Build & push Docker images
2. ✅ Verify Kubernetes cluster access
3. ✅ Check GPU availability
4. ✅ Configure storage classes
5. ✅ Deploy with Helm
6. ✅ Verify all pods running
7. ✅ Configure DNS/ingress
8. ✅ Test web interface
9. ✅ Run sample segmentation

**Time Estimate:**
- First-time deployment: 2-4 hours
- Subsequent deployments: 15-30 minutes

---

**Last Updated:** October 10, 2025  
**Version:** 1.2.0

