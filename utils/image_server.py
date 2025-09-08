import os
import ssl
import argparse
import ipaddress
from pathlib import Path
from urllib.parse import urlparse
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import datetime
import os.path as osp

from fastapi import FastAPI, HTTPException, status, Request, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # Added
import uvicorn
import nibabel as nib
import numpy as np
import json
import tempfile
import io

from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent

# Load environment variables
load_dotenv()

# --- Certificate Generation Functions ---
def generate_self_signed_cert(cert_dir: Path, cert_file: Path, key_file: Path, hostname: str = "localhost"):
    """Generate a self-signed SSL certificate and private key."""
    
    cert_dir.mkdir(parents=True, exist_ok=True)

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Jose"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Image Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.DNSName(hostname),
            x509.DNSName("127.0.0.1"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write certificate to file
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(Encoding.PEM))
    
    # Write private key to file
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption()
        ))
    
    print(f"Generated self-signed certificate:")
    print(f"  Certificate: {cert_file}")
    print(f"  Private Key: {key_file}")

def get_server_config():
    """Get server configuration from environment variables."""
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # Parse the URL to extract host and port
    parsed = urlparse(image_server_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8888
    
    return host, port

def generate_directory_listing(directory_path: Path, request_path: str) -> str:
    """Generate HTML directory listing"""
    items = []
    
    try:
        # Add parent directory link if not at root
        if request_path != "/":
            parent_path = str(Path(request_path).parent)
            if parent_path == ".":
                parent_path = "/"
            items.append(f'<li><a href="{parent_path}">📁 ../</a></li>')
        
        # List directories first
        for item in sorted(directory_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                item_name = item.name
                item_path = f"{request_path.rstrip('/')}/{item_name}/"
                items.append(f'<li><a href="{item_path}">📁 {item_name}/</a></li>')
        
        # Then list files
        for item in sorted(directory_path.iterdir()):
            if item.is_file() and not item.name.startswith('.'):
                item_name = item.name
                item_path = f"{request_path.rstrip('/')}/{item_name}"
                file_size = item.stat().st_size
                size_str = f"({file_size:,} bytes)" if file_size < 1024*1024 else f"({file_size/(1024*1024):.1f} MB)"
                items.append(f'<li><a href="{item_path}">📄 {item_name}</a> <span style="color: #666; font-size: 0.8em;">{size_str}</span></li>')
    
    except Exception as e:
        items.append(f'<li><span style="color: #cc0000;">Error reading directory: {e}</span></li>')
    
    items_html = "\n".join(items)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Directory listing for {request_path}</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            a {{ text-decoration: none; color: #0066cc; }}
            a:hover {{ text-decoration: underline; }}
            .header {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📁 Directory listing for {request_path}</h1>
            <p>Image Server - Medical Imaging Files</p>
        </div>
        <ul>
            {items_html}
        </ul>
        <div class="footer">
            <p>🏥 Medical Imaging Server | FastAPI + Uvicorn</p>
        </div>
    </body>
    </html>
    """
    return html

# --- FastAPI Application ---
app = FastAPI(title="Medical Imaging Server", description="HTTP server for medical imaging files with directory browsing")

# Mount the assets directory to serve static files like niivue.umd.js
app.mount("/assets", StaticFiles(directory=project_root / "assets"), name="assets")

@app.get("/filtered-segments/{patient_id}/{filename}")
async def get_filtered_segments(
    patient_id: str, 
    filename: str, 
    label_ids: str = Query(..., description="Comma-separated list of label IDs to include")
):
    """Filter segmentation file to only include specified label IDs"""
    try:
        # Parse label IDs from query parameter
        label_id_list = [int(id.strip()) for id in label_ids.split(',') if id.strip()]
        
        # Construct path to original segmentation file
        segment_path = project_root / "output" / "segments" / patient_id / filename
        
        if not segment_path.exists():
            raise HTTPException(status_code=404, detail=f"Segmentation file not found: {filename}")
        
        # Load the NIfTI file
        nifti_img = nib.load(str(segment_path))
        data = nifti_img.get_fdata()
        
        # Create filtered data - only keep voxels with selected label IDs
        filtered_data = np.zeros_like(data)
        for label_id in label_id_list:
            filtered_data[data == label_id] = label_id
        
        # Create new NIfTI image with filtered data
        filtered_img = nib.Nifti1Image(filtered_data, nifti_img.affine, nifti_img.header)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp_file:
            nib.save(filtered_img, tmp_file.name)
            
            # Read the temporary file and return as streaming response
            def iter_file():
                with open(tmp_file.name, 'rb') as f:
                    while chunk := f.read(8192):
                        yield chunk
                # Clean up temporary file
                os.unlink(tmp_file.name)
            
            return StreamingResponse(
                iter_file(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=filtered_{filename}",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering segmentation: {str(e)}")

@app.get("/filtered-segments/{patient_id}/voxels/{filename}")
async def get_filtered_voxels(
    patient_id: str, 
    filename: str, 
    label_ids: str = Query(..., description="Comma-separated list of label IDs to include")
):
    """Filter voxels file to only include specified label IDs"""
    try:
        # Parse label IDs from query parameter
        label_id_list = [int(id.strip()) for id in label_ids.split(',') if id.strip()]
        
        # Construct path to voxels file (strict - no fallback)
        voxels_dir = project_root / "output" / patient_id / "voxels"
        voxels_path = voxels_dir / filename
        if not voxels_path.exists():
            # Attempt to find a voxels file with matching stem or any .nii/.nii.gz in the voxels dir
            target_stem = Path(filename).stem
            candidates = []
            if voxels_dir.exists():
                for p in voxels_dir.iterdir():
                    if p.is_file() and p.suffix in (".nii", ".gz"):
                        candidates.append(p)
            # Prefer same stem
            chosen = None
            for p in candidates:
                if p.stem == target_stem:
                    chosen = p
                    break
            if chosen is None and candidates:
                chosen = candidates[0]
            if chosen is None:
                raise HTTPException(status_code=404, detail=f"Voxels file not found: {filename}")
            voxels_path = chosen
        
        # Load the NIfTI file
        nifti_img = nib.load(str(voxels_path))
        data = nifti_img.get_fdata()
        
        # Create filtered data - only keep voxels with selected label IDs
        filtered_data = np.zeros_like(data)
        for label_id in label_id_list:
            filtered_data[data == label_id] = label_id
        
        # Create new NIfTI image with filtered data
        filtered_img = nib.Nifti1Image(filtered_data, nifti_img.affine, nifti_img.header)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp_file:
            nib.save(filtered_img, tmp_file.name)
            
            # Read the temporary file and return as streaming response
            def iter_file():
                with open(tmp_file.name, 'rb') as f:
                    while chunk := f.read(8192):
                        yield chunk
                # Clean up temporary file
                os.unlink(tmp_file.name)
            
            return StreamingResponse(
                iter_file(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=filtered_voxels_{filename}",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering voxels: {str(e)}")

@app.get("/output/{patient_id}/voxels/{filename}/labels")
async def get_available_voxel_labels(
    patient_id: str,
    filename: str,
):
    """Return available non-zero label IDs (and names) present in the voxels NIfTI for this patient/file."""
    try:
        voxels_dir = project_root / "output" / patient_id / "voxels"
        voxels_path = voxels_dir / filename
        if not voxels_path.exists():
            # Attempt to find a voxels file with matching stem or any .nii/.nii.gz
            target_stem = Path(filename).stem
            candidates = []
            if voxels_dir.exists():
                for p in voxels_dir.iterdir():
                    if p.is_file() and p.suffix in (".nii", ".gz"):
                        candidates.append(p)
            chosen = None
            for p in candidates:
                if p.stem == target_stem:
                    chosen = p
                    break
            if chosen is None and candidates:
                chosen = candidates[0]
            if chosen is None:
                raise HTTPException(status_code=404, detail=f"Voxels file not found: {filename}")
            voxels_path = chosen

        # Load NIfTI and find unique labels (excluding 0)
        nifti_img = nib.load(str(voxels_path))
        data = nifti_img.get_fdata()
        unique_vals = np.unique(data.astype(np.int32))
        label_ids = [int(v) for v in unique_vals if int(v) != 0]

        # Map IDs to names using conf/vista3d_label_colors.json if available
        id_to_name = {}
        try:
            colors_path = project_root / "conf" / "vista3d_label_colors.json"
            if colors_path.exists():
                with open(colors_path, 'r') as f:
                    items = json.load(f)
                for item in items:
                    iid = int(item.get('id', -1))
                    name = item.get('name', '')
                    if iid >= 0:
                        id_to_name[iid] = name
        except Exception:
            # Non-fatal; names may be missing
            pass

        labels = [{"id": lid, "name": id_to_name.get(lid, str(lid))} for lid in label_ids]
        return {"labels": labels, "voxel_filename": voxels_path.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading voxel labels: {str(e)}")

@app.get("/{full_path:path}")
@app.head("/{full_path:path}")
async def serve_files(request: Request, full_path: str):
    """Serve files and directory listings with proper range request support"""
    
    # Handle root path
    if full_path == "":
        full_path = "."
    
    # Construct absolute path
    absolute_path = project_root / full_path
    
    # Security check - ensure path is within project root
    try:
        absolute_path = absolute_path.resolve()
        project_root_resolved = project_root.resolve()
        
        # Check if the resolved path is within project root
        if not str(absolute_path).startswith(str(project_root_resolved)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if path exists
    if not absolute_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    
    # If it's a file, serve it with range request support
    if absolute_path.is_file():
        return await serve_file_with_range(request, absolute_path)
    
    # If it's a directory, generate listing
    elif absolute_path.is_dir():
        request_path = "/" + full_path.strip("/")
        if request_path != "/" and not request_path.endswith("/"):
            request_path += "/"
        
        html_content = generate_directory_listing(absolute_path, request_path)
        return HTMLResponse(content=html_content, status_code=200)
    
    else:
        raise HTTPException(status_code=404, detail="Not found")

async def serve_file_with_range(request: Request, file_path: Path):
    """Serve a file with proper range request support for large files"""
    import re
    
    # Get file size
    file_size = file_path.stat().st_size
    
    # Check for range header
    range_header = request.headers.get('range')
    
    if not range_header:
        # No range requested, serve entire file
        return FileResponse(
            file_path,
            headers={
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Range"
            }
        )
    
    # Parse range header
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    if not range_match:
        raise HTTPException(status_code=416, detail="Range Not Satisfiable")
    
    start = int(range_match.group(1))
    end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
    
    # Validate range
    if start >= file_size or end >= file_size or start > end:
        raise HTTPException(status_code=416, detail="Range Not Satisfiable")
    
    # Calculate content length
    content_length = end - start + 1
    
    # Read the requested range
    def iter_file_range():
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk_size = min(8192, remaining)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
    
    return StreamingResponse(
        iter_file_range(),
        status_code=206,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Range"
        },
        media_type="application/octet-stream"
    )

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Main execution block for Uvicorn ---
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="HTTP/S Image Server")
    parser.add_argument("--host", help="Host to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--port", type=int, help="Port to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--cert-dir", help="Directory to store SSL certificate and key files", default=str(project_root / "output" / "certs"))
    parser.add_argument("--disable-dir-listing", action="store_true", help="Disable directory listing for enhanced security (files will still be served)")
    parser.add_argument("--https", action="store_true", help="Run as an HTTPS server with a self-signed certificate")
    
    args = parser.parse_args()
    
    # Get configuration
    default_host, default_port = get_server_config()
    host = args.host or default_host
    port = args.port or default_port
    
    # Note: Files are served via the @app.get("/{full_path:path}") route above
    # This provides better control over directory listings and security

    if args.https:
        # Run Uvicorn with SSL
        # Set up SSL certificate and key paths
        cert_dir = Path(args.cert_dir)
        cert_file = cert_dir / "server.crt"
        key_file = cert_dir / "server.key"
        
        # Generate self-signed certificate if it doesn't exist
        if not cert_file.exists() or not key_file.exists():
            print("Self-signed certificate not found. Generating new one...")
            generate_self_signed_cert(cert_dir, cert_file, key_file, host)

        print(f"Starting HTTPS Image Server with FastAPI/Uvicorn...")
        print(f"  URL: https://{host}:{port}")
        print(f"  Serving from: {project_root.absolute()}")
        print(f"  Certificate: {cert_file}")
        print(f"  Private Key: {key_file}")
        print(f"  Directory Listing Enabled: {not args.disable_dir_listing}")
        print(f"  Press Ctrl+C to stop the server")
        print("-" * 60)

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file),
            log_level="info"
        )
    else:
        # Run Uvicorn without SSL (default)
        print(f"Starting HTTP Image Server with FastAPI/Uvicorn...")
        print(f"  URL: http://{host}:{port}")
        print(f"  Serving from: {project_root.absolute()}")
        print(f"  Directory Listing Enabled: {not args.disable_dir_listing}")
        print(f"  Press Ctrl+C to stop the server")
        print("-" * 60)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )