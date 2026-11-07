"""Ex0.py - projection of a plane out of a 3D volume (NRRD) into a video.

Usage:  python Ex0.py file.nrrd file.csv file.mp4 [fps]      (fps = playback speed, default 10)

CSV: one plane per line, either
     3 points (a, b, c)      -> 9 numbers  (isosceles triangle, |ab| == |ac|)
     4 points (a1, a2, b, c) -> 12 numbers (isosceles trapezoid, |a1 b| == |a2 c|)
"""
import csv
import sys
import time

import numpy as np

EPS = 0.001
MIN_SIDE = 256  # minimal video size so that the error text always fits
DEFAULT_FPS = 10.0  # playback speed of the video (NOT the computation speed)


class InvalidPlaneError(ValueError):
    """Raised when a CSV row does not describe a valid plane."""


def _dist(p, q):
    return float(np.linalg.norm(p - q))


class Plane:
    """A plane patch given by a1, a2 (top edge) and b, c (bottom edge).

    A triangle (a, b, c) is the special case a1 == a2 == a.
    """

    def __init__(self, a1, a2, b, c):
        self.a1, self.a2, self.b, self.c = (
            np.asarray(p, dtype=float) for p in (a1, a2, b, c))
        self.validate()

    @classmethod
    def from_values(cls, values):
        if len(values) == 9:
            a, b, c = values[0:3], values[3:6], values[6:9]
            return cls(a, a, b, c)
        if len(values) == 12:
            return cls(values[0:3], values[3:6], values[6:9], values[9:12])
        raise InvalidPlaneError(f"expected 9 or 12 numbers, got {len(values)}")

    def validate(self):
        for p in (self.a1, self.a2, self.b, self.c):
            if p.shape != (3,) or not np.isfinite(p).all():
                raise InvalidPlaneError("points must be finite 3D coordinates")
        if abs(_dist(self.a1, self.b) - _dist(self.a2, self.c)) >= EPS:
            raise InvalidPlaneError("|a1b| != |a2c| (not isosceles)")
        if _dist(self.a1, self.b) < 1 or _dist(self.b, self.c) < 1:
            raise InvalidPlaneError("degenerate plane (edge shorter than 1 voxel)")
        if _dist(self.a1, self.a2) > _dist(self.b, self.c) + EPS:
            raise InvalidPlaneError("|a1a2| > |bc|")
        if _dist(self.a1, self.a2) > EPS:  # 4 points: must be coplanar
            u, v, w = self.a2 - self.a1, self.b - self.a1, self.c - self.a1
            scale = np.linalg.norm(u) * np.linalg.norm(v) * np.linalg.norm(w)
            if abs(np.dot(np.cross(u, v), w)) > EPS * scale:
                raise InvalidPlaneError("points are not on the same plane")


def project(volume, plane):
    """Return the 2D image (rows = along a->b, cols = along b->c) of the plane.

    Vectorised version of the course algorithm. Nearest voxel is used;
    pixels outside the patch or outside the volume are 0.
    """
    a1, a2, b, c = plane.a1, plane.a2, plane.b, plane.c
    length = _dist(a1, b)
    height, width = int(length) + 1, int(_dist(b, c)) + 1

    y = np.arange(height, dtype=float)[:, None]
    s = a1 + y * (b - a1) / length                    # row start  (H,3)
    e = a2 + y * (c - a2) / _dist(a2, c)              # row end    (H,3)
    d12 = np.linalg.norm(e - s, axis=1)               # row length (H,)
    direction = (e - s) / np.maximum(d12, 1e-12)[:, None]
    mid = (s + e) / 2

    u = np.arange(width) - (width - 1) / 2            # offset from row centre
    pts = mid[:, None, :] + u[None, :, None] * direction[:, None, :]
    idx = np.rint(pts).astype(np.int64)               # nearest voxel

    inside = np.abs(u)[None, :] <= d12[:, None] / 2 + 1e-9
    inside &= ((idx >= 0) & (idx < np.array(volume.shape))).all(axis=2)

    image = np.zeros((height, width), dtype=np.uint8)
    i = idx[inside]
    image[inside] = volume[i[:, 0], i[:, 1], i[:, 2]]
    return image


def to_uint8(data):
    """Scale any integer volume to 0..255 using the GLOBAL min/max."""
    if data.dtype == np.uint8:
        return data
    lo, hi = float(data.min()), float(data.max())
    if hi == lo:
        return np.zeros(data.shape, dtype=np.uint8)
    return ((data.astype(np.float32) - lo) * (255.0 / (hi - lo))).astype(np.uint8)


def load_volume(path):
    import nrrd
    data, _ = nrrd.read(path)
    if data.ndim != 3:
        raise ValueError(f"expected a 3D volume, got {data.ndim}D")
    return to_uint8(data)


def make_error_frame(width, height, title, detail=""):
    """Black frame with a red title and the reason (wrapped) below it."""
    import cv2
    font = cv2.FONT_HERSHEY_SIMPLEX
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    scale = 1.0
    while scale > 0.3 and cv2.getTextSize(title, font, scale, 2)[0][0] > width - 20:
        scale -= 0.05
    y = height // 2 - 20
    cv2.putText(frame, title, (10, y), font, scale, (0, 0, 255), 2)
    line, lines = "", []
    for word in detail.split():                      # simple word wrap
        if cv2.getTextSize((line + " " + word).strip(), font, 0.5, 1)[0][0] > width - 20:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    lines.append(line)
    for i, text in enumerate(lines[:6]):
        cv2.putText(frame, text, (10, y + 35 + 24 * i), font, 0.5, (255, 255, 255), 1)
    return frame


def read_planes(csv_path):
    """Yield (line_number, Plane or None, error message or None)."""
    with open(csv_path, newline="") as f:
        for n, row in enumerate(csv.reader(f), 1):
            if not any(cell.strip() for cell in row):
                continue  # skip blank lines
            while row and not row[-1].strip():
                row = row[:-1]  # tolerate trailing commas
            try:
                plane = Plane.from_values([float(cell) for cell in row])
                yield n, plane, None
            except ValueError as err:  # also catches InvalidPlaneError
                yield n, None, str(err)


def main(argv):
    if len(argv) not in (4, 5):
        print("Usage: python Ex0.py file.nrrd file.csv file.mp4 [fps]")
        return 1
    import cv2
    nrrd_path, csv_path, mp4_path = argv[1:4]
    fps = float(argv[4]) if len(argv) == 5 else DEFAULT_FPS

    volume = load_volume(nrrd_path)
    results = []  # (line, image or None, message)
    project_time = 0.0
    for n, plane, err in read_planes(csv_path):
        if err:
            print(f"line {n}: INVALID - {err}")
            results.append((n, None, err))
        else:
            t0 = time.perf_counter()
            image = project(volume, plane)
            project_time += time.perf_counter() - t0
            results.append((n, image, None))
            print(f"line {n}: ok")

    good = [img for _, img, _ in results if img is not None]
    w = max([MIN_SIDE] + [im.shape[1] for im in good])
    h = max([MIN_SIDE] + [im.shape[0] for im in good])
    w, h = w + w % 2, h + h % 2  # mp4 wants even sizes

    out = cv2.VideoWriter(mp4_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for n, img, err in results:
        if img is None:
            frame = make_error_frame(w, h, f"ERROR line {n}", err)
        else:
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            top, left = (h - img.shape[0]) // 2, (w - img.shape[1]) // 2
            frame[top:top + img.shape[0], left:left + img.shape[1]] = img[:, :, None]
        out.write(frame)
    out.release()
    if good:
        print(f"Projection speed: {len(good) / project_time:.0f} planes/sec "
              f"({len(good)} planes in {project_time:.2f}s)")
    print(f"Video saved to {mp4_path} ({len(results)} frames, {fps:g} fps)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))