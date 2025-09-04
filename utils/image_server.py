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

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # Added
import uvicorn

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
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
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
    image_server_url = os.getenv("IMAGE_SERVER", "https://localhost:8888")
    
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
app = FastAPI(title="Medical Imaging Server", description="HTTPS server for medical imaging files with directory browsing")

@app.get("/{full_path:path}")
@app.head("/{full_path:path}")
async def serve_files(request: Request, full_path: str):
    """Serve files and directory listings"""
    
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
    
    # If it's a file, serve it
    if absolute_path.is_file():
        return FileResponse(absolute_path)
    
    # If it's a directory, generate listing
    elif absolute_path.is_dir():
        request_path = "/" + full_path.strip("/")
        if request_path != "/" and not request_path.endswith("/"):
            request_path += "/"
        
        html_content = generate_directory_listing(absolute_path, request_path)
        return HTMLResponse(content=html_content, status_code=200)
    
    else:
        raise HTTPException(status_code=404, detail="Not found")

origins = [
    "http://localhost",
    "http://localhost:8501", # Streamlit's default port
    "http://localhost:8502", # Alternative Streamlit port
    "https://localhost",
    "https://localhost:8501",
    "https://localhost:8502",
]

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
    parser = argparse.ArgumentParser(description="HTTPS Image Server")
    parser.add_argument("--host", help="Host to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--port", type=int, help="Port to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--cert-dir", help="Directory to store SSL certificate and key files", default=str(project_root / "outputs" / "certs"))
    parser.add_argument("--disable-dir-listing", action="store_true", help="Disable directory listing for enhanced security (files will still be served)")
    
    args = parser.parse_args()
    
    # Get configuration
    default_host, default_port = get_server_config()
    host = args.host or default_host
    port = args.port or default_port
    
    # Set up SSL certificate and key paths
    cert_dir = Path(args.cert_dir)
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    # Generate self-signed certificate if it doesn't exist
    if not cert_file.exists() or not key_file.exists():
        print("Self-signed certificate not found. Generating new one...")
        generate_self_signed_cert(cert_dir, cert_file, key_file, host)
    
    # Note: Files are served via the @app.get("/{full_path:path}") route above
    # This provides better control over directory listings and security

    # Run Uvicorn with SSL
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
