# Data Set and Testing Strategy

## 4. Data Set
The project utilizes 3D volumetric data files in NRRD format. The primary data source will be the MRI datasets provided by the 3D Slicer open-source project.

## 5. Testing Strategy & Demo
The testing strategy focuses on validating the projection algorithm's accuracy and performance.

*   **Edge Cases:** Validate scenarios where projection points fall outside the 3D matrix boundaries (ensuring `v=0`).
*   **Performance:** Ensure the algorithm runs at a minimum of 30 FPS, targeting 100+ FPS for 500^3 byte matrices.
*   **Demo Execution:** The main script will be tested via the command line format: `python Ex0.py file.nrrd file.csv file.mp4`.
*   **Demo Validation:** The output `.mp4` video will be visually inspected to confirm each frame correctly corresponds to the exact plane coordinates listed in the `.csv` file.