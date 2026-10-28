import sys
import numpy as np
import nrrd
import cv2
import csv


def dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def project_plane(M, points):
    a, b, c = np.array(points[0]), np.array(points[1]), np.array(points[2])
    Dab, Dbc = int(dist(a, b)), int(dist(b, c))

    v_ab = (b - a) / dist(a, b) if dist(a, b) != 0 else np.zeros(3)
    v_ac = (c - a) / dist(a, c) if dist(a, c) != 0 else np.zeros(3)

    E = np.zeros((Dbc + 1, Dab + 1), dtype=np.uint8)
    a1, a2 = np.copy(a), np.copy(a)

    for y in range(Dab + 1):
        p = np.copy(a1)
        d12 = dist(a1, a2)
        dp = (a2 - a1) / d12 if d12 > 0 else np.zeros(3)

        for x1 in range(int(d12) + 1):
            px, py, pz = int(p[0]), int(p[1]), int(p[2])

            # דגימה מהמטריצה התלת-ממדית בגבולות המותרים
            if 0 <= px < M.shape[0] and 0 <= py < M.shape[1] and 0 <= pz < M.shape[2]:
                v = M[px, py, pz]
            else:
                v = 0

            x = int((Dbc / 2) - (d12 / 2) + x1)
            if 0 <= x < E.shape[0] and 0 <= y < E.shape[1]:
                E[x, y] = v

            p = p + dp

        a1 = a1 + v_ab
        a2 = a2 + v_ac

    return E


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python Ex0.py file.nrrd file.csv file.mp4")
        sys.exit(1)

    nrrd_file, csv_file, mp4_file = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"Loading {nrrd_file}...")
    M, _ = nrrd.read(nrrd_file)

    planes = []
    with open(csv_file, 'r') as f:
        for row in csv.reader(f):
            if row:
                pts = [float(val) for val in row]
                # חילוץ 3 נקודות מהשורה
                planes.append([(pts[0], pts[1], pts[2]), (pts[3], pts[4], pts[5]), (pts[6], pts[7], pts[8])])

    frames = []
    for i, plane in enumerate(planes):
        print(f"Processing plane {i + 1}/{len(planes)}...")
        frames.append(project_plane(M, plane))

    if frames:
        height, width = frames[0].shape
        out = cv2.VideoWriter(mp4_file, cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (width, height), False)
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"Video saved to {mp4_file}")