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
        print(f"Querying: {url}...")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error querying {url}: {e}")
        print("  Please ensure the Vista3D Docker container is running.")
        return None
    except json.JSONDecodeError:
        print(f"  Error: Could not decode JSON response from {url}.")
        return None

def print_formatted_json(data):
    """Prints a Python dictionary as a formatted JSON string."""
    if data:
        print(json.dumps(data, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Get information about the running Nvidia Vista3D Model.")
    parser.add_argument("--all", action="store_true", help="Get all available information.")
    parser.add_argument("--models", action="store_true", help="List available models.")
    parser.add_argument("--status", action="store_true", help="Get server status.")
    parser.add_argument("--config", action="store_true", help=f"Get the configuration for the '{MODEL_NAME}' model.")
    parser.add_argument("--metadata", action="store_true", help=f"Get the metadata for the '{MODEL_NAME}' model.")
    args = parser.parse_args()

    print("--- Vista3D Model Information ---")

    # If no specific flag is provided, default to --all
    get_all = args.all or not any([args.models, args.status, args.config, args.metadata])

    if args.models or get_all:
        print("\n[+] Available Models:")
        models_info = query_api("models")
        print_formatted_json(models_info)

    if args.status or get_all:
        print(f"\n[+] Server Status:")
        status_info = query_api("status")
        print_formatted_json(status_info)

    if args.metadata or get_all:
        print(f"\n[+] Metadata for model '{MODEL_NAME}':")
        metadata = query_api(f"models/{MODEL_NAME}")
        print_formatted_json(metadata)

    if args.config or get_all:
        print(f"\n[+] Configuration for model '{MODEL_NAME}':")
        config = query_api(f"models/{MODEL_NAME}/config")
        print_formatted_json(config)

    print("\n--- End of Report ---")

if __name__ == "__main__":
    main()
