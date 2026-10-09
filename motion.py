"""Small deterministic motion curves and colour blending."""


def smooth(value):
    """Quintic ease with zero velocity and acceleration at both ends."""
    t = max(0.0, min(1.0, value))
    return t*t*t*(t*(t*6-15)+10)


def blend(first, second, amount):
    t = max(0.0, min(1.0, amount))
    return "#" + "".join(f"{round(int(first[i:i+2], 16)*(1-t)+int(second[i:i+2], 16)*t):02x}"
                         for i in (1, 3, 5))
