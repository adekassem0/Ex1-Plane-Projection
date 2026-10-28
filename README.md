# Ex1: Algorithm - Implementing a plane projection of 3D volume

## Problem Definition
Given a 3D raster data matrix (M) and a plane (p), the goal is to compute the 2D matrix (image) of the projection of p in M. 

## Project Scope
*   **Design and Implementation:** Design and implement a plane projection algorithm for 3D volumes in a robust and runtime-efficient manner. 
*   **Performance:** The code must run at +30 FPS minimum, with an expected runtime of at least 100 FPS for a matrix of size 500^3 bytes.
*   **Data:** Use NRRD format data, specifically utilizing MRI files from the 3D Slicer open-source project.
*   **Deliverables:** Create a demo script that receives a 3D volumetric data file (.nrrd) and a CSV file containing plane coordinates, and outputs an MP4 video file presenting the corresponding projected frames.