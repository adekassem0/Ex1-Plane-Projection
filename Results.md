# Experiment Results

## Execution
An experiment was conducted using the 3D Slicer MRI dataset (`MRHead_1.nrrd`). A `planes.csv` file was created with 3 planes, each defined by 3 coordinate points. 
The demo script was executed via the command line:
`python Ex0.py MRHead_1.nrrd planes.csv output.mp4`

## Results
The algorithm successfully projected the 3D volume onto the requested 2D planes. The output is saved in `output.mp4`, containing exactly 3 frames corresponding to the planes from the CSV file. Visual inspection confirms the MRI cross-sections were correctly extracted.