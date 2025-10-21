# Changelog

All notable changes to the Vista3D Helm chart will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-10-10

### Added
- Built-in NiiVue colormap support with 23 pre-configured colormaps
- Support for the following built-in colormaps: gray, jet, hot, cool, warm, spring, summer, autumn, winter, rainbow, viridis, plasma, magma, inferno, parula, turbo, hsv, bone, copper, cubehelix, cividis, linspecer, batlow, blues
- Intelligent colormap loading that distinguishes between built-in and custom colormaps
- Enhanced colormap performance through optimized loading mechanism

### Changed
- Frontend now handles built-in colormaps natively without requiring JSON definitions
- Improved colormap selection UI with better organization
- Updated frontend constants.py with BUILTIN_NIIVUE_COLORMAPS dictionary

### Fixed
- Colormap loading performance issues
- Healthcare typo in Chart.yaml maintainer section (Helathcare → Healthcare)

## [1.1.0] - Previous Release

### Added
- Initial Helm chart for Vista3D platform
- Backend deployment for Vista3D AI server
- Frontend deployment for Streamlit interface
- Image server deployment for serving medical image files
- ConfigMap for centralized configuration
- PVC templates for persistent storage
- Ingress support for external access
- Service account and RBAC configuration
- Production-ready values file

### Features
- NVIDIA GPU support for backend
- Horizontal pod autoscaling
- Network policies
- ServiceMonitor for Prometheus
- Health checks and probes
- Security contexts and pod security policies

