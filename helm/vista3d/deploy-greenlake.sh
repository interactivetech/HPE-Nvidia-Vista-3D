#!/bin/bash
# ============================================================================
# Vista3D Deployment Script for HPE GreenLake for Containers
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}       Vista3D Deployment on HPE GreenLake for Containers      ${NC}"
echo -e "${GREEN}================================================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}[1/8] Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kubectl found${NC}"

# Check helm
if ! command -v helm &> /dev/null; then
    echo -e "${RED}✗ helm not found. Please install Helm 3.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ helm found${NC}"

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}✗ Cannot connect to Kubernetes cluster.${NC}"
    echo -e "${YELLOW}Please ensure your kubeconfig is set up correctly.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"

# Display cluster info
CLUSTER_NAME=$(kubectl config current-context)
echo -e "${BLUE}Current cluster: ${CLUSTER_NAME}${NC}"

# Get NGC API Key
echo -e "\n${YELLOW}[2/8] NGC API Key Configuration${NC}"
echo -e "${BLUE}Enter your NVIDIA NGC API Key (starts with 'nvapi-'):${NC}"
read -s NGC_API_KEY
echo ""

if [ -z "$NGC_API_KEY" ]; then
    echo -e "${RED}✗ NGC API Key is required.${NC}"
    exit 1
fi

if [[ ! "$NGC_API_KEY" =~ ^nvapi- ]]; then
    echo -e "${YELLOW}⚠ Warning: NGC API key should start with 'nvapi-'${NC}"
    echo -e "${YELLOW}Continue anyway? (y/N)${NC}"
    read -r CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo -e "${GREEN}✓ NGC API Key configured${NC}"

# Get domain name
echo -e "\n${YELLOW}[3/8] Domain Configuration${NC}"
echo -e "${BLUE}Enter your domain name (e.g., vista3d.greenlake.yourdomain.com):${NC}"
echo -e "${BLUE}Press Enter for default: vista3d.greenlake.local${NC}"
read DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    DOMAIN_NAME="vista3d.greenlake.local"
fi
echo -e "${GREEN}✓ Using domain: ${DOMAIN_NAME}${NC}"

# Get storage class
echo -e "\n${YELLOW}[4/8] Storage Configuration${NC}"
echo -e "${BLUE}Available storage classes:${NC}"
kubectl get storageclass -o name 2>/dev/null || echo "None found"
echo -e "${BLUE}Enter HPE storage class name (press Enter for 'hpe-standard'):${NC}"
read STORAGE_CLASS

if [ -z "$STORAGE_CLASS" ]; then
    STORAGE_CLASS="hpe-standard"
fi
echo -e "${GREEN}✓ Using storage class: ${STORAGE_CLASS}${NC}"

# Create namespace
echo -e "\n${YELLOW}[5/8] Creating namespace...${NC}"
kubectl create namespace vista3d --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true

# Label namespace
kubectl label namespace vista3d \
  hpe.com/project=medical-ai \
  hpe.com/team=healthcare \
  hpe.com/platform=greenlake \
  --overwrite 2>/dev/null

echo -e "${GREEN}✓ Namespace 'vista3d' created and labeled${NC}"

# Create secret
echo -e "\n${YELLOW}[6/8] Creating NGC secret...${NC}"
kubectl create secret generic vista3d-secrets \
  --from-literal=ngc-api-key="$NGC_API_KEY" \
  --namespace vista3d \
  --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null

echo -e "${GREEN}✓ Secret 'vista3d-secrets' created${NC}"

# Apply storage classes (if file exists)
if [ -f "hpe-storage.yaml" ]; then
    echo -e "\n${YELLOW}[7/8] Creating Vista3D storage classes...${NC}"
    kubectl apply -f hpe-storage.yaml 2>/dev/null || echo -e "${YELLOW}⚠ Could not create storage classes (may already exist)${NC}"
    echo -e "${GREEN}✓ Storage classes configured${NC}"
else
    echo -e "${YELLOW}⚠ hpe-storage.yaml not found, skipping storage class creation${NC}"
fi

# Deploy with Helm
echo -e "\n${YELLOW}[8/8] Deploying Vista3D with Helm...${NC}"
echo -e "${BLUE}This may take several minutes...${NC}"

cd "$(dirname "$0")"

helm upgrade --install vista3d . \
  --namespace vista3d \
  --values values-hpe-greenlake.yaml \
  --set ingress.hosts[0].host="$DOMAIN_NAME" \
  --set ingress.tls[0].hosts[0]="$DOMAIN_NAME" \
  --set persistence.storageClass="$STORAGE_CLASS" \
  --set persistence.output.storageClass="$STORAGE_CLASS" \
  --set persistence.dicom.storageClass="$STORAGE_CLASS" \
  --wait \
  --timeout 10m

echo -e "${GREEN}✓ Vista3D deployed successfully${NC}"

# Wait for pods
echo -e "\n${YELLOW}Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=vista3d \
  -n vista3d \
  --timeout=300s 2>/dev/null || echo -e "${YELLOW}⚠ Some pods may still be starting${NC}"

# Display status
echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}                    Deployment Complete!                        ${NC}"
echo -e "${GREEN}================================================================${NC}"

echo -e "\n${YELLOW}📊 Deployment Status:${NC}"
kubectl get pods -n vista3d

echo -e "\n${YELLOW}🌐 Access Information:${NC}"
echo -e "Primary URL: ${GREEN}https://$DOMAIN_NAME${NC}"
echo -e "Namespace:   ${GREEN}vista3d${NC}"

echo -e "\n${YELLOW}📋 Useful Commands:${NC}"
echo -e "${BLUE}Check all resources:${NC}"
echo -e "  kubectl get all -n vista3d"

echo -e "\n${BLUE}View logs:${NC}"
echo -e "  kubectl logs -n vista3d -l app.kubernetes.io/name=vista3d --tail=100 -f"

echo -e "\n${BLUE}Check backend (GPU) pod:${NC}"
echo -e "  kubectl logs -n vista3d -l app.kubernetes.io/component=backend --tail=50"

echo -e "\n${BLUE}Port-forward (if ingress not ready):${NC}"
echo -e "  kubectl port-forward -n vista3d svc/vista3d-frontend 8501:8501"
echo -e "  Then visit: ${GREEN}http://localhost:8501${NC}"

echo -e "\n${BLUE}Check ingress:${NC}"
echo -e "  kubectl get ingress -n vista3d"

echo -e "\n${BLUE}Scale frontend:${NC}"
echo -e "  kubectl scale deployment vista3d-frontend --replicas=5 -n vista3d"

echo -e "\n${BLUE}Uninstall:${NC}"
echo -e "  helm uninstall vista3d -n vista3d"

echo -e "\n${YELLOW}📚 Documentation:${NC}"
echo -e "See GREENLAKE_DEPLOYMENT.md for detailed information"

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}✓ Setup complete! Your Vista3D platform is ready.${NC}"
echo -e "${GREEN}================================================================${NC}"

