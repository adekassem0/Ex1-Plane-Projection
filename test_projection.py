import unittest
import numpy as np
from Ex0 import Plane, InvalidPlaneError, project, to_uint8


def volume():
    # value encodes z so we can see which slice was sampled
    M = np.zeros((200, 200, 200), dtype=np.uint8)
    for z in range(200):
        M[:, :, z] = z
    return M


class TestPlane(unittest.TestCase):
    def test_valid_triangle(self):
        Plane.from_values([50, 50, 50, 150, 50, 50, 50, 150, 50])

    def test_not_isosceles(self):
        with self.assertRaises(InvalidPlaneError):
            Plane.from_values([0, 0, 0, 100, 0, 0, 0, 90, 0])

    def test_wrong_count(self):
        with self.assertRaises(InvalidPlaneError):
            Plane.from_values([1, 2, 3, 4])

    def test_trapezoid_ok(self):
        Plane.from_values([45, 0, 0, 55, 0, 0, 0, 0, 100, 100, 0, 100])

    def test_trapezoid_not_coplanar(self):
        with self.assertRaises(InvalidPlaneError):
            Plane.from_values([45, 0, 0, 55, 0, 0, 0, 0, 100, 100, 60, 80])


class TestProject(unittest.TestCase):
    def test_axial_plane_samples_single_slice(self):
        img = project(volume(), Plane.from_values([50, 50, 60, 150, 50, 60, 50, 150, 60]))
        vals = np.unique(img[img > 0])
        self.assertEqual(list(vals), [60])
        self.assertEqual(img.shape, (101, 142))

    def test_outside_volume_is_black(self):
        img = project(volume(), Plane.from_values([500, 500, 500, 600, 500, 500, 500, 600, 500]))
        self.assertEqual(img.max(), 0)

    def test_tilted_plane_samples_many_slices(self):
        img = project(volume(), Plane.from_values([50, 50, 50, 100, 50, 100, 50, 100, 100]))
        self.assertGreater(len(np.unique(img[img > 0])), 20)

    def test_to_uint8(self):
        d = np.array([0, 500, 1000], dtype=np.uint16)
        self.assertEqual(list(to_uint8(d)), [0, 127, 255])


if __name__ == "__main__":
    unittest.main()