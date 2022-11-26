import math

from .Vector import dot


def lerp_one(x, y, t):
    return (1-t)*x + t*y

def lerp(x, y, t):
    return [(1-t)*xi + t*yi for xi, yi in zip(x, y)]


def slerp(x, y, t):
    omega = math.acos(dot(x, y))
    if omega == 0 or math.isnan(omega):
        return x
    factor_1 = math.sin((1-t)*omega)
    factor_2 = math.sin(t*omega)
    invsomega = 1/math.sin(omega)

    return [(t1*factor_1 + t2*factor_2)*invsomega for t1, t2 in zip(x, y)]
