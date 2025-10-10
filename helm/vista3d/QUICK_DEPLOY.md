# 🚀 Vista3D on HPE GreenLake - Quick Deploy

## One-Command Deployment

```bash
cd helm/vista3d && ./deploy-greenlake.sh
```

## Manual 3-Step Deploy

```bash
# 1. Create namespace and secret
kubectl create namespace vista3d
kubectl create secret generic vista3d-secrets \
  --from-literal=ngc-api-key="nvapi-YOUR-KEY" \
  --namespace vista3d

# 2. Deploy
helm install vista3d . \
  --namespace vista3d \
  --values values-hpe-greenlake.yaml \
  --set ingress.hosts[0].host="vista3d.yourdomain.com"

# 3. Verify
kubectl get pods -n vista3d
```

## Access

```bash
# Via ingress
https://vista3d.yourdomain.com

# Or port-forward
kubectl port-forward -n vista3d svc/vista3d-frontend 8501:8501
# Then visit: http://localhost:8501
```

## Useful Commands

```bash
# Status
kubectl get all -n vista3d

# Logs
kubectl logs -n vista3d -l app.kubernetes.io/name=vista3d -f

# Scale
kubectl scale deployment vista3d-frontend --replicas=5 -n vista3d

# Update
helm upgrade vista3d . --namespace vista3d --reuse-values

# Uninstall
helm uninstall vista3d -n vista3d
```

## Files

- **values-hpe-greenlake.yaml** - Configuration
- **deploy-greenlake.sh** - Automated deployment
- **GREENLAKE_DEPLOYMENT.md** - Full guide
- **hpe-storage.yaml** - Storage classes

## Need Help?

See `GREENLAKE_DEPLOYMENT.md` for complete documentation.

