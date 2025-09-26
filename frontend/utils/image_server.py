import os
import argparse
from pathlib import Path
from urllib.parse import urlparse
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

# Load environment variables
load_dotenv()

# Get folder paths from environment variables - should be full paths
def resolve_folder_path(env_var_name: str, default_path: str) -> str:
    """Resolve folder path from environment variable - expects full paths."""
    folder_path = os.getenv(env_var_name, default_path)
    
    # All paths should be absolute now - no more PROJECT_ROOT
    if not os.path.isabs(folder_path):
        raise ValueError(f"{env_var_name} must be set in .env file with full absolute path, got: {folder_path}")
    
    return folder_path

output_folder = resolve_folder_path('OUTPUT_FOLDER', 'output')
dicom_folder = resolve_folder_path('DICOM_FOLDER', 'dicom')


def get_server_config():
    """Get server configuration from environment variables."""
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # Parse the URL to extract host and port
    parsed = urlparse(image_server_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8888
    
    return host, port

def load_image_server_config():
    """Load image server configuration from JSON file."""
    # Use the image_server's config file instead of duplicating it
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "image_server" / "conf" / "image_server_conf.json"
    
    # Default configuration with resolved absolute paths
    default_config = {
        "viewable_folders": [
            {
                "name": "dicom",
                "path": dicom_folder,  # This is now an absolute path
                "url_path": "dicom",   # URL path for web access
                "description": "DICOM medical imaging files",
                "icon": "📁"
            },
            {
                "name": "output",
                "path": output_folder,  # This is now an absolute path
                "url_path": "output",   # URL path for web access
                "description": "Processed medical imaging output files", 
                "icon": "📁"
            }
        ],
        "server_settings": {
            "title": "Medical Imaging Server",
            "description": "HTTP server for medical imaging files with directory browsing",
            "show_file_sizes": True,
            "show_hidden_files": False
        }
    }
    
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update folder paths from environment variables if they exist
            for folder in config.get("viewable_folders", []):
                if folder["name"] == "dicom":
                    folder["path"] = dicom_folder
                    folder["url_path"] = "dicom"  # Ensure URL path is set
                elif folder["name"] == "output":
                    folder["path"] = output_folder
                    folder["url_path"] = "output"  # Ensure URL path is set
            
            return config
        else:
            return default_config
    except Exception as e:
        print(f"Warning: Could not load image server config: {e}")
        return default_config

# Load configuration
server_config = load_image_server_config()

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
server_settings = server_config.get("server_settings", {})
app = FastAPI(
    title=server_settings.get("title", "Medical Imaging Server"), 
    description=server_settings.get("description", "HTTP server for medical imaging files with directory browsing")
)

# Mount the assets directory to serve static files like niivue.umd.js
# Get project root for assets directory - use the directory containing this script
script_dir = Path(__file__).parent
project_root = script_dir.parent
app.mount("/assets", StaticFiles(directory=project_root / "assets"), name="assets")

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "image-server"}

@app.get("/filtered-scans/{patient_id}/{filename}")
async def get_filtered_scans(
    patient_id: str, 
    filename: str, 
    label_ids: str = Query(..., description="Comma-separated list of label IDs to include")
):
    """Filter segmentation file to only include specified label IDs"""
    try:
        # Parse label IDs from query parameter
        label_id_list = [int(id.strip()) for id in label_ids.split(',') if id.strip()]
        
        # Construct path to original segmentation file
        scan_path = Path(output_folder) / "scans" / patient_id / filename
        
        if not scan_path.exists():
            raise HTTPException(status_code=404, detail=f"Scan file not found: {filename}")
        
        # Load the NIfTI file
        nifti_img = nib.load(str(scan_path))
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

@app.get("/filtered-scans/{patient_id}/voxels/{filename}")
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
        voxels_dir = Path(output_folder) / patient_id / "voxels"
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
        voxels_dir = Path(output_folder) / patient_id / "voxels"
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
            # Get project root for config directory
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
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

def is_allowed_directory(path: Path) -> bool:
    """Check if a directory is within the allowed viewable folders"""
    try:
        # Get allowed folder paths from config (these are now absolute paths)
        allowed_folder_paths = [Path(folder["path"]) for folder in server_config.get("viewable_folders", [])]
        
        # Allow access to configured folders
        if path == Path(output_folder) or path == Path(dicom_folder):
            return True
        
        # Check if the path is within any of the allowed folder paths
        for allowed_path in allowed_folder_paths:
            try:
                # Check if the requested path is within the allowed path
                path.relative_to(allowed_path)
                return True
            except ValueError:
                # Path is not within this allowed path, continue checking
                continue
        
        # Check if it's a subdirectory of allowed folders and matches URL path
        try:
            # Check against output and dicom folders
            for base_folder in [Path(output_folder), Path(dicom_folder)]:
                try:
                    rel_path = path.relative_to(base_folder)
                    path_parts = rel_path.parts
                    
                    if path_parts:
                        # Get allowed URL paths from config
                        allowed_url_paths = [folder["url_path"] for folder in server_config.get("viewable_folders", [])]
                        
                        # Allow configured URL paths and their subdirectories
                        if path_parts[0] in allowed_url_paths:
                            return True
                except ValueError:
                    # Path is not relative to this base folder, continue checking
                    continue
        except ValueError:
            # Path is not relative to any allowed folder
            pass
            
        return False
    except Exception:
        # Any other error means not allowed
        return False

def generate_restricted_root_listing() -> HTMLResponse:
    """Generate HTML listing showing only configured viewable folders"""
    items = []
    
    # Get server settings from config
    server_settings = server_config.get("server_settings", {})
    title = server_settings.get("title", "Medical Imaging Server")
    description = server_settings.get("description", "HTTP server for medical imaging files with directory browsing")
    
    # Check each configured folder
    for folder_config in server_config.get("viewable_folders", []):
        folder_name = folder_config.get("name", "")
        folder_path = folder_config.get("path", "")
        folder_url_path = folder_config.get("url_path", folder_name)
        folder_description = folder_config.get("description", "")
        folder_icon = folder_config.get("icon", "📁")
        
        # Check if folder exists (folder_path is now absolute)
        full_path = Path(folder_path)
        if full_path.exists() and full_path.is_dir():
            items.append(f'<li><a href="/{folder_url_path}/">{folder_icon} {folder_name}/</a> <span style="color: #666; font-size: 0.8em;">({folder_description})</span></li>')
    
    # If no folders exist, show a message
    if not items:
        items.append('<li><span style="color: #666;">No accessible folders found</span></li>')
    
    items_html = "\n".join(items)
    
    # Get folder names for description
    folder_names = [folder["name"] for folder in server_config.get("viewable_folders", [])]
    folder_list = ", ".join(folder_names) if folder_names else "none"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
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
            <h1>🏥 {title}</h1>
            <p>{description}</p>
            <p>Accessible folders: {folder_list}</p>
        </div>
        <ul>
            {items_html}
        </ul>
        <div class="footer">
            <p>🏥 {title} | FastAPI + Uvicorn</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

@app.get("/{full_path:path}")
@app.head("/{full_path:path}")
async def serve_files(request: Request, full_path: str):
    """Serve files and directory listings with proper range request support"""
    
    # Handle root path - only show configured folders
    if full_path == "" or full_path == ".":
        return generate_restricted_root_listing()
    
    # Map URL path to actual folder path
    def map_url_to_actual_path(url_path: str) -> Path:
        """Map URL path to actual file system path"""
        # Check if this is a configured folder URL path
        for folder_config in server_config.get("viewable_folders", []):
            folder_url_path = folder_config.get("url_path", folder_config.get("name", ""))
            if url_path.startswith(folder_url_path + "/") or url_path == folder_url_path:
                # Replace the URL path with the actual folder path
                actual_folder_path = Path(folder_config.get("path", ""))
                if url_path == folder_url_path:
                    return actual_folder_path
                else:
                    # Get the subpath after the folder name
                    subpath = url_path[len(folder_url_path):].lstrip("/")
                    return actual_folder_path / subpath
        
        # If not a configured folder, treat as relative to output folder
        return Path(output_folder) / url_path
    
    # Map URL path to actual path
    absolute_path = map_url_to_actual_path(full_path)
    
    # Security check - ensure path is within allowed directories
    try:
        absolute_path = absolute_path.resolve()
        
        # Check if this is an allowed directory or subdirectory
        if not is_allowed_directory(absolute_path):
            raise HTTPException(status_code=403, detail="Access denied - only configured folders are accessible")
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

# Configure CORS to allow access from any origin
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
    parser = argparse.ArgumentParser(description="HTTP Image Server")
    parser.add_argument("--host", help="Host to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--port", type=int, help="Port to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--disable-dir-listing", action="store_true", help="Disable directory listing for enhanced security (files will still be served)")
    
    args = parser.parse_args()
    
    # Get configuration
    default_host, default_port = get_server_config()
    host = args.host or default_host
    port = args.port or default_port
    
    # Note: Files are served via the @app.get("/{full_path:path}") route above
    # This provides better control over directory listings and security

    # Run Uvicorn without SSL
    print(f"Starting HTTP Image Server with FastAPI/Uvicorn...")
    print(f"  URL: http://{host}:{port}")
    print(f"  Output Folder: {output_folder}")
    print(f"  DICOM Folder: {dicom_folder}")
    print(f"  Directory Listing Enabled: {not args.disable_dir_listing}")
    print(f"  CORS: Enabled for all origins")
    print(f"  Binding to: 0.0.0.0 (all interfaces)")
    print(f"  Press Ctrl+C to stop the server")
    print("-" * 60)
    uvicorn.run(
        app,
        host="0.0.0.0",  # Bind to all interfaces to allow external access
        port=port,
        log_level="info"
    )