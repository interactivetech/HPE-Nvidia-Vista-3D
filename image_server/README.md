# Vista3D Image Server (Standalone)

Minimal FastAPI server to serve OUTPUT_FOLDER and DICOM_FOLDER via HTTP, identical to the monorepo behavior.

Environment variables (absolute paths required):
- OUTPUT_FOLDER: Absolute path, mounted read-only in container
- DICOM_FOLDER: Absolute path, mounted read-only in container
- IMAGE_SERVER: Base URL (e.g., http://localhost:8888)

Build and run:

```
docker build -t vista3d-image-server ./image_server
docker run --rm -p 8888:8888 \
  -e OUTPUT_FOLDER=/data/output \
  -e DICOM_FOLDER=/data/dicom \
  -e IMAGE_SERVER=http://localhost:8888 \
  -v /host/output:/data/output:ro \
  -v /host/dicom:/data/dicom:ro \
  vista3d-image-server
```


