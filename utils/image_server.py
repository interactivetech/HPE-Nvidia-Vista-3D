#!/usr/bin/env python3
"""
HTTPS Image Server with self-signed certificates.
Serves files from the outputs directory over HTTPS.
"""

import os
import sys
import ssl
import socket
import argparse
import ipaddress
import posixpath
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageServerHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the image server."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Override to set the document root to the outputs directory."""
        # Get the document root from the server
        if hasattr(self.server, 'document_root'):
            doc_root = self.server.document_root
        else:
            doc_root = str(project_root / "outputs")
        
        # Clean the path and join with document root
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = doc_root
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore absolute paths and parent directory references
                continue
            path = os.path.join(path, word)
        return path
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight CORS requests
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging format
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

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

def main():
    """Main function to start the HTTPS image server."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="HTTPS Image Server")
    parser.add_argument("--host", help="Host to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--port", type=int, help="Port to bind to (default: from IMAGE_SERVER env var)")
    parser.add_argument("--cert", help="Path to SSL certificate file")
    parser.add_argument("--key", help="Path to SSL private key file")
    parser.add_argument("--outputs-dir", help="Directory to serve (default: ./outputs)")
    
    args = parser.parse_args()
    
    # Get configuration
    default_host, default_port = get_server_config()
    host = args.host or default_host
    port = args.port or default_port
    outputs_dir = args.outputs_dir or str(project_root / "outputs")
    
    # Ensure outputs directory exists
    outputs_path = Path(outputs_dir)
    if not outputs_path.exists():
        print(f"Error: Outputs directory '{outputs_path}' does not exist!")
        sys.exit(1)
    
    # Set up SSL certificate and key paths
    cert_dir = outputs_path / "certs"
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = args.cert or cert_dir / "server.crt"
    key_file = args.key or cert_dir / "server.key"
    
    # Generate self-signed certificate if it doesn't exist
    if not cert_file.exists() or not key_file.exists():
        print("Self-signed certificate not found. Generating new one...")
        generate_self_signed_cert(cert_file, key_file, host)
    
    # Create HTTPS server
    server = HTTPServer((host, port), ImageServerHandler)
    
    # Set the document root for the server
    server.document_root = str(outputs_path.absolute())
    
    # Configure SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    
    print(f"Starting HTTPS Image Server...")
    print(f"  URL: https://{host}:{port}")
    print(f"  Document Root: {outputs_path.absolute()}")
    print(f"  Certificate: {cert_file}")
    print(f"  Private Key: {key_file}")
    print(f"  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
        server.server_close()
        print("Server stopped.")

if __name__ == "__main__":
    main()
