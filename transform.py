import math

class Transform:
    """Simple 2D rotation and translation class"""
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

    def __mul__(self, transform):
        """Combine two Transforms so that the LHS Transform happens
        first, then the RHS Transform happens.  The new combined
        Transform is returned."""
        s = math.sin(self.theta)
        c = math.cos(self.theta)

        return Transform(self.x     + c * transform.x - s * transform.y,
                         self.y     + s * transform.x + c * transform.y,
                         self.theta + transform.theta)
