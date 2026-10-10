"""Small deterministic motion curves."""


def smooth(value):
    """Quintic ease with zero velocity and acceleration at both ends."""
    t = max(0.0, min(1.0, value))
    return t*t*t*(t*(t*6-15)+10)
