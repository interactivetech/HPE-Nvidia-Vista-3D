# Key Terms

This document defines key terms used in the HPE-NVIDIA Vista 3D Medical Imaging Platform.

## DICOM (Digital Imaging and Communications in Medicine)

DICOM refers to both a standard protocol for handling, storing, and transmitting medical imaging information, and its associated file format. Developed by the National Electrical Manufacturers Association (NEMA), DICOM ensures interoperability between medical imaging equipment from different vendors. DICOM files contain not only the image data itself but also comprehensive metadata including patient demographics, study information, acquisition parameters, and technical details about the imaging procedure. This rich metadata structure makes DICOM files self-contained medical records that preserve the complete context of the imaging study, which is essential for clinical diagnosis and treatment planning.

## NIfTI (Neuroimaging Informatics Technology Initiative)

NIfTI refers to an open, NIH-sponsored initiative and its associated file format, primarily used in neuroimaging for storing data from sources like MRI scanners. The NIfTI format provides advantages over older formats by unambiguously storing orientation and coordinate system information, facilitating software interoperability and the analysis of complex brain scans. The NIfTI file can be a single .nii file or a pair of .hdr and .img files, containing both image data and associated metadata. Unlike DICOM's clinical focus, NIfTI is optimized for research and computational analysis, making it the preferred format for neuroimaging studies, brain mapping research, and AI/ML applications in medical imaging.

## NiiVue Viewer

NiiVue is a modern, web-based neuroimaging viewer designed for displaying NIfTI format brain images directly in web browsers. Developed as a JavaScript library, NiiVue provides interactive 3D visualization capabilities for neuroimaging data without requiring specialized desktop software. It supports real-time manipulation of brain scans, including slice viewing, 3D rendering, overlay visualization, and custom colormap applications. NiiVue is particularly valuable in research and clinical settings where quick, accessible visualization of neuroimaging data is needed, offering features like cross-sectional views, volume rendering, and the ability to overlay statistical maps or segmentation results onto anatomical images.

## Voxels

Voxels, short for "volume pixels," are the three-dimensional equivalent of pixels in 2D images, representing the smallest unit of volume in 3D medical imaging data. Each voxel contains specific intensity values that correspond to tissue properties at that spatial location within the body, such as bone density, soft tissue characteristics, or contrast agent concentration. In medical imaging, voxels form the building blocks of 3D anatomical structures, enabling detailed volumetric analysis and precise spatial measurements. The size and resolution of voxels directly impact image quality and diagnostic accuracy, with smaller voxels providing higher resolution but requiring more computational resources and storage space. In the context of Vista3D segmentation, voxels are individually classified and labeled to identify different anatomical structures, organs, or pathological regions within the medical scan.

## PLY (Polygon File Format)

PLY, which stands for "Polygon File Format" or "Stanford Triangle Format," is a computer file format used to store 3D graphics data, particularly 3D mesh models composed of polygons (typically triangles). Developed at Stanford University, PLY files store geometric data such as vertex coordinates, face indices, and associated properties like colors, normals, and texture coordinates. In the context of medical imaging and Vista3D segmentation, PLY files represent the 3D surface meshes generated from segmented anatomical structures, converting voxel-based medical data into smooth, renderable 3D models. These PLY files enable interactive 3D visualization of organs, vessels, and other anatomical structures, making them valuable for surgical planning, medical education, and patient communication. The format's simplicity and widespread support make it ideal for transferring 3D medical models between different visualization and analysis software packages.
