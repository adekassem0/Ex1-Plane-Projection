"""make_planes.py - generate a planes.csv that sweeps through a whole NRRD volume.

Usage:  python make_planes.py file.nrrd planes.csv [--with-errors]
        --with-errors adds 3 deliberately invalid rows (for the error-frame demo)

The orientation of the volume (which array axis is left-right, front-back,
up-down) is read from the NRRD header ("space" + "space directions"), so the
head is shown upright for any file.  Every plane is a RECTANGLE given by 4
points (a1, a2, b, c):

    a1---a2     top edge    (image columns run a1 -> a2)
     |    |
     b----c     bottom edge (image rows run top -> bottom)

Sweeps:  1) sagittal (every slice, face on the left)
         2) coronal  (every 3rd slice, patient-right on the left)
         3) a triangle plane (3 points) spinning inside a coronal plane
"""
import csv
import math
import re
import sys

OPPOSITE = {"left": "right", "right": "left", "anterior": "posterior",
            "posterior": "anterior", "superior": "inferior", "inferior": "superior"}
ABBREV = {"l": "left", "r": "right", "a": "anterior", "p": "posterior",
          "s": "superior", "i": "inferior"}
ROLE_OF = {"left": "LR", "right": "LR", "anterior": "AP", "posterior": "AP",
           "superior": "SI", "inferior": "SI"}
POSITIVE_END = {"LR": "left", "AP": "posterior", "SI": "superior"}


def read_header(path):
    header = {}
    with open(path, "rb") as f:
        for raw in f:
            line = raw.decode("latin-1").strip()
            if not line:
                break
            if ": " in line and not line.startswith("#"):
                key, value = line.split(": ", 1)
                header[key.strip()] = value.strip()
    return header


def world_axis_names(space):
    """'left-posterior-superior' / 'LPS' -> ['left', 'posterior', 'superior']."""
    s = space.lower().replace("3d-", "").replace("-handed", "")
    parts = s.split("-") if "-" in s else [ABBREV[ch] for ch in s if ch in ABBREV]
    if len(parts) != 3 or any(p not in OPPOSITE for p in parts):
        raise ValueError(f"unknown space: {space}")
    return parts


def find_roles(header):
    """role ('LR'/'AP'/'SI') -> (array axis, True if the index grows toward the role's positive end)."""
    names = world_axis_names(header["space"])
    dirs = [[float(v) for v in m.split(",")]
            for m in re.findall(r"\(([^)]*)\)", header["space directions"])]
    roles = {}
    for axis, vec in enumerate(dirs):
        k = max(range(3), key=lambda j: abs(vec[j]))
        grows_toward = names[k] if vec[k] > 0 else OPPOSITE[names[k]]
        role = ROLE_OF[grows_toward]
        roles[role] = (axis, grows_toward == POSITIVE_END[role])
    if sorted(roles) != ["AP", "LR", "SI"]:
        raise ValueError("could not map the 3 array axes to LR / AP / SI")
    return roles


# --- settings of the last part (the spinning wedge) -------------------------
WEDGE_FRAMES = 64        # number of frames of the wedge part
WEDGE_LEG = 0.7          # leg length |ab| = |ac|, as a fraction of the up-down size (~180 voxels)
WEDGE_HALF_ANGLE = 30    # degrees between the wedge's centre line and each leg
WEDGE_AP_POS = 0.5       # coronal level of the wedge (0 = front, 1 = back)


def build(shape, roles, step_coronal=3):
    ext = {role: shape[roles[role][0]] - 1 for role in roles}
    L, P, S = ext["LR"], ext["AP"], ext["SI"]

    def vox(l, p, s):
        """l grows toward Left, p toward Posterior, s toward Superior (0..max)."""
        v = [0.0, 0.0, 0.0]
        for role, val in (("LR", l), ("AP", p), ("SI", s)):
            axis, grows = roles[role]
            v[axis] = val if grows else ext[role] - val
        return v

    rows = []
    for l in range(0, L + 1):                       # 1) sagittal, face on the left
        rows.append([*vox(l, 0, S), *vox(l, P, S), *vox(l, 0, 0), *vox(l, P, 0)])
    for p in range(0, P + 1, step_coronal):         # 2) coronal, patient-right on the left
        rows.append([*vox(0, p, S), *vox(L, p, S), *vox(0, p, 0), *vox(L, p, 0)])
    # 3) isosceles TRIANGLE (a, b, c) in a coronal plane, apex a at the centre,
    #    spinning around the plane's normal like a radar
    p0 = WEDGE_AP_POS * P
    cl, cs = L / 2, S / 2
    leg, alpha = WEDGE_LEG * S, math.radians(WEDGE_HALF_ANGLE)
    for k in range(WEDGE_FRAMES):
        phi = 2 * math.pi * k / WEDGE_FRAMES

        def tip(psi):                               # psi = 0 -> straight down
            return vox(cl + leg * math.sin(psi), p0, cs - leg * math.cos(psi))
        rows.append([*vox(cl, p0, cs), *tip(phi - alpha), *tip(phi + alpha)])
    return rows


def main(argv):
    nrrd_path, out = argv[1], argv[2]
    header = read_header(nrrd_path)
    shape = [int(v) for v in header["sizes"].split()]
    try:
        roles = find_roles(header)
    except (KeyError, ValueError) as err:
        print(f"WARNING: orientation unknown ({err}); assuming axis0=AP, axis1=SI, axis2=LR")
        roles = {"AP": (0, True), "SI": (1, True), "LR": (2, True)}
    print("axes:", {role: f"array axis {ax}" + ("" if grows else " (reversed)")
                    for role, (ax, grows) in roles.items()})
    rows = build(shape, roles)
    if "--with-errors" in argv:   # 3 invalid rows -> 3 "ERROR" frames in the video
        rows[100:100] = [[0, 0, 0, 100, 0, 0, 0, 90, 0],   # not isosceles
                         ["a", "b", "c"],                  # not numbers
                         [1, 2, 3, 4]]                     # wrong number of values
    with open(out, "w", newline="") as f:
        csv.writer(f).writerows(
            [[f"{v:.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else v for v in row]
             for row in rows])
    print(f"volume {shape}: wrote {len(rows)} planes to {out}")


if __name__ == "__main__":
    main(sys.argv)