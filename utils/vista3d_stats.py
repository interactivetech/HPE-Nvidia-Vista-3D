import requests
import json
import argparse

# Configuration
VISTA3D_BASE_URL = "http://localhost:8000/v1"
MODEL_NAME = "vista3d"

def query_api(endpoint: str):
    """Helper function to query an API endpoint and return the JSON response."""
    url = f"{VISTA3D_BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error querying {url}: {e}")
        print("  Please ensure the Vista3D Docker container is running and accessible on port 8000.")
        return None
    except json.JSONDecodeError:
        print(f"  Error: Could not decode JSON response from {url}. Invalid JSON received.")
        return None

def print_section_header(title: str):
    print(f"\n{'=' * 50}\n{title.upper()}\n{'=' * 50}")

def print_subsection_header(title: str):
    print(f"\n--- {title} ---")

def print_formatted_json(data):
    """Prints a Python dictionary as a formatted JSON string."""
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("  (No data available)")

def main():
    parser = argparse.ArgumentParser(description="Get comprehensive information about the running Nvidia Vista3D Model.")
    parser.add_argument("--all", action="store_true", help="Get all available information (default).")
    parser.add_argument("--models", action="store_true", help="List available models.")
    parser.add_argument("--status", action="store_true", help="Get server status and GPU information.")
    parser.add_argument("--config", action="store_true", help=f"Get the configuration for the '{MODEL_NAME}' model.")
    parser.add_argument("--metadata", action="store_true", help=f"Get the metadata for the '{MODEL_NAME}' model.")
    args = parser.parse_args()

    # If no specific flag is provided, default to --all
    get_all = args.all or not any([args.models, args.status, args.config, args.metadata])

    print_section_header("Vista3D Model Comprehensive Report")

    # 1. Server Status and GPU Information
    if args.status or get_all:
        print_subsection_header("Server Status and System Information")
        status_info = query_api("status")
        if status_info:
            print_formatted_json(status_info)
            # Attempt to extract GPU info if present
            if "system_info" in status_info and "gpu_info" in status_info["system_info"]:
                print_subsection_header("GPU Information")
                print_formatted_json(status_info["system_info"]["gpu_info"])
            else:
                print("  (GPU information not explicitly found in status output)")
        else:
            print("  (Server status not available)")

    # 2. Available Models
    if args.models or get_all:
        print_subsection_header("Available Models")
        models_info = query_api("models")
        print_formatted_json(models_info)

    # 3. Model Metadata
    if args.metadata or get_all:
        print_subsection_header(f"Metadata for model '{MODEL_NAME}'")
        metadata = query_api(f"models/{MODEL_NAME}")
        print_formatted_json(metadata)

    # 4. Model Configuration
    if args.config or get_all:
        print_subsection_header(f"Configuration for model '{MODEL_NAME}'")
        config = query_api(f"models/{MODEL_NAME}/config")
        print_formatted_json(config)

    print_section_header("Report End")

if __name__ == "__main__":
    main()
