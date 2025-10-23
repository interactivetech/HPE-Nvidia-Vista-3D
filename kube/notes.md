# get current status 
microk8s status

# start if it is not already
microk8s start

# set for current sesstion
export KUBECONFIG=/home/hpadmin/HPE-Nvidia-Vista-3D/kube/microk8s.kubeconfig

# deploy helm chart for frontend and image-server
#helm upgrade --install vista3d helm/vista3d -f helm/vista3d/values-frontend-imageserver.yaml
helm install vista3d helm/vista3d -f helm/vista3d/values.yaml

# see what is running
microk8s kubectl get pods
microk8s kubectl get deployments

# portforward from pod to host
export KUBECONFIG=/home/hpadmin/HPE-Nvidia-Vista-3D/kube/microk8s.kubeconfig 
microk8s.kubectl port-forward service/vista3d-frontend 8501:8501 -n vista3d &
microk8s.kubectl port-forward service/vista3d-image-server 8888:8888 -n vista3d &

# portforward from server to localhost
ssh ssh.axisapps.io  -l a55edd84cf804eed8d07957c24146fe6 -L 8501:localhost:8501 -L 8888:localhost:8888


# delete a pod
microk8s kubectl delete deployment vista3d-backend


# helm commands
helm list
helm uninstall vista3d
cd helm/vista3d
helm install vista3d . --namespace vista3d --create-namespace
cd helm
helm package vista3d
microk8s helm list
microk8s kubectl get pods -n default
microk8s kubectl get pods -n vista3d
# see ports assigned
microk8s kubectl get svc -n vista3d

# list secrets
microk8s kubectl get secrets -n vista3d | grep 'helm.sh/release.v1'
microk8s kubectl delete secret sh.helm.release.v1.vista3d.v1  -n vista3d
