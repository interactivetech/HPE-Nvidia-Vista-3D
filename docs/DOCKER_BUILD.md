# Build image_server image and publish
cd ./image_server
docker build -t dwtwp/vista3d-image-server:v1.0.0 .
docker tag dwtwp/vista3d-image-server:v1.0.0 dwtwp/vista3d-image-server:latest
docker push dwtwp/vista3d-image-server:latest


# Build frontend image and publish
cd ./frontend
docker build -t dwtwp/vista3d-frontend:v1.0.0 .
docker tag dwtwp/vista3d-frontend:v1.0.0 dwtwp/vista3d-frontend:latest
docker push dwtwp/vista3d-frontend:latest
