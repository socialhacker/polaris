import math
import unittest

from source.transform import Transform

class TestAST(unittest.TestCase):

    def test_from_translation(self):
        self.assertEqual(Transform.from_translation(1,2).x, 1)
        self.assertEqual(Transform.from_translation(1,2).y, 2)
        self.assertEqual(Transform.from_translation(1,2).theta, 0)

    def test_from_rotation(self):
        self.assertEqual(Transform.from_rotation(1).x, 0)
        self.assertEqual(Transform.from_rotation(1).y, 0)
        self.assertEqual(Transform.from_rotation(1).theta, 1)

    def test_composition(self):
        t = (Transform.from_translation(10, 5) @
             Transform.from_rotation(math.pi / 2))

        self.assertAlmostEqual(t.x,     -5)
        self.assertAlmostEqual(t.y,     10)
        self.assertAlmostEqual(t.theta, math.pi / 2)

if __name__ == '__main__':
    unittest.main()
