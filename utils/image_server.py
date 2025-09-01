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

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # Added
import uvicorn

from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent

# Load environment variables
load_dotenv()

# --- Certificate Generation Functions ---
def generate_self_signed_cert(cert_file: Path, key_file: Path, hostname: str = "localhost"):
    """Generate a self-signed SSL certificate and private key."""
    
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

# --- FastAPI Application ---
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8501", # Streamlit's default port
    "https://localhost",
    "https://localhost:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from project root
app.mount("/", StaticFiles(directory=str(project_root)), name="static")

# --- Main execution block for Uvicorn ---
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="HTTPS Image Server")
    parser.add_argument("--host", help="Host to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--port", type=int, help="Port to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--cert", help="Path to SSL certificate file")
    parser.add_argument("--key", help="Path to SSL private key file")
    
    args = parser.parse_args()
    
    # Get configuration
    default_host, default_port = get_server_config()
    host = args.host or default_host
    port = args.port or default_port
    
    # Set up SSL certificate and key paths
    cert_dir = project_root / "outputs" / "certs"
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = args.cert or cert_dir / "server.crt"
    key_file = args.key or cert_dir / "server.key"
    
    # Generate self-signed certificate if it doesn't exist
    if not Path(cert_file).exists() or not Path(key_file).exists():
        print("Self-signed certificate not found. Generating new one...")
        generate_self_signed_cert(Path(cert_file), Path(key_file), host)
    
    # Run Uvicorn with SSL
    print(f"Starting HTTPS Image Server with FastAPI/Uvicorn...")
    print(f"  URL: https://{host}:{port}")
    print(f"  Serving from: {project_root.absolute()}")
    print(f"  Certificate: {cert_file}")
    print(f"  Private Key: {key_file}")
    print(f"  Press Ctrl+C to stop the server")
    print("-" * 60)

    uvicorn.run(
        app,
        host=host,
        port=port,
        ssl_keyfile=str(key_file),
        ssl_certfile=str(cert_file),
        log_level="info"
    )