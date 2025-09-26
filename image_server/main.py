import os
import argparse
from pathlib import Path
from urllib.parse import urlparse

# Reuse the existing server implementation without changes
# We import the code from the monorepo and run it as-is
from dotenv import load_dotenv

load_dotenv()

# Ensure absolute paths provided via env
def resolve_folder_path(env_var_name: str, default_path: str) -> str:
    folder_path = os.getenv(env_var_name, default_path)
    if not os.path.isabs(folder_path):
        raise ValueError(f"{env_var_name} must be an absolute path, got: {folder_path}")
    return folder_path

# To keep functionality identical, import and run the existing FastAPI app
# from utils/image_server.py but executed from this entrypoint.

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils import image_server as server_module  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vista3D Image Server Entrypoint")
    parser.add_argument("--host", help="Host to bind to (default from IMAGE_SERVER)")
    parser.add_argument("--port", type=int, help="Port to bind to (default from IMAGE_SERVER)")
    args = parser.parse_args()

    host, default_port = server_module.get_server_config()
    host = args.host or host
    port = args.port or default_port

    # Run underlying uvicorn invocation from the module's main block logic
    import uvicorn
    uvicorn.run(server_module.app, host="0.0.0.0", port=port, log_level="info")


