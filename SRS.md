# Software Requirements Specification (SRS) - Ex1

## 1. Functional Requirements
* **Input:** The system must accept a 3D volumetric data file in NRRD format and a CSV file containing lists of 3 or 4 point coordinates representing target planes.
* **Processing:** The system must project the 3D matrix (M) onto a 2D image matrix for each given plane using the defined isosceles triangle or trapezoid projection algorithm.
* **Output:** The system must generate an MP4 video file containing one frame for each corresponding plane presented in the CSV file, strictly in the list order.

## 2. Non-Functional Requirements
* **Performance:** The implementation must achieve a minimum of 30 frames per second (FPS). For a matrix size of 500^3 bytes, a runtime of at least 100 FPS is expected.
* **Reliability:** The code must be correct, robust, and stable during edge-case memory access and matrix sampling.