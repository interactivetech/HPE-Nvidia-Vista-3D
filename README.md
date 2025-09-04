# NIfTI Vessel Segmentation and Viewer

This project provides a web-based application for viewing 3D NIfTI files and a command-line tool for segmenting blood vessels in those files using the Vista3D model.

## Features

*   **NIfTI Viewer**: A Streamlit-based web application to view NIfTI files in 3D.
*   **Vessel Segmentation**: A Python script to perform vessel segmentation on NIfTI files using a Vista3D inference server.
*   **Side-by-Side Comparison**: View original and segmented scans in the same application.

## Prerequisites

*   Python 3.11+
*   Docker
*   `uv` (for Python package management)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

3.  **Start the services:**
    The application requires a running Vista3D container and the image server. A convenience script is provided to start both:
    ```bash
    python3 utils/vista3d.py
    ```

## Usage

### NIfTI Viewer

To use the NIfTI viewer, run the following command:

```bash
streamlit run app.py
```

This will open a web application in your browser. You can then select a patient and a NIfTI file to view. You can also switch between viewing the original and segmented scans.

### Vessel Segmentation

To run the vessel segmentation script, use the following command:

```bash
python3 segment_vessels.py
```

This script will:
1.  Scan the `output/nifti` directory for NIfTI files.
2.  Send each file to the Vista3D inference server for segmentation.
3.  Save the segmented files in the `output/segmentation` directory.

You can configure the vessels of interest by setting the `VESSELS_OF_INTEREST` environment variable.

## Testing

A comprehensive test suite is provided to ensure that all services are running correctly.

To run the tests, execute the following command:

```bash
python3 tests/test_vista3d_services.py
```

This will run a series of tests to verify the status of the Docker container, the image server, and the communication between them.
