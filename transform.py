import math

class Transform:
    """Simple 2D rotation and translation class.

    A Transform (T) is a translation (X) followed by a rotation (R).
    The Transform would be written R(X(p)) to transform a point p.
    Or as (R o X)(p) where o is function composition.

    Multiple Transforms (T1 followed by T2 followed by T3) can be
    composed (T3 o T2 o T1) with the matrix multiplication operator @,
    The resulting Transform is R3(X3(R2(X2(R1(X1(p))))))."""

    def __init__(self, x, y, theta):
        self.x = x
        self.y = y
        self.theta = theta

    @classmethod
    def from_translation(cls, x, y):
        """Construct a new Transform that is a pure translation"""
        return cls(x, y, 0)

    @classmethod
    def from_rotation(cls, theta):
        """Construct a new Transform that is a pure rotation"""
        return cls(0, 0, theta)

    def __repr__(self):
        return f'Transform({self.x}x{self.y},{self.theta})'

    def __matmul__(self, transform):
        """Combine two Transforms so that the RHS Transform happens
        first, then the LHS Transform happens.  The new combined
        Transform is returned."""
        s = math.sin(transform.theta)
        c = math.cos(transform.theta)

        return Transform(transform.x     + c * self.x - s * self.y,
                         transform.y     + s * self.x + c * self.y,
                         transform.theta + self.theta)
