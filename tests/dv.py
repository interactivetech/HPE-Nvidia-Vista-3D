import requests
import zipfile

base_url = "http://localhost:8000"

data = {
    "image": "https://assets.ngc.nvidia.com/products/api-catalog/vista3d/example-1.nii.gz",
}

def unzip_file(zip_filepath, dest_dir):
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)

response = requests.post(f"{base_url}/v1/vista3d/inference", json=data)
if response.status_code == 200:
    output_folder = "output"
    output_zip_name = "output.zip"

    with open(output_zip_name, "wb") as f:
        f.write(response.content)

    unzip_file(output_zip_name, output_folder)
