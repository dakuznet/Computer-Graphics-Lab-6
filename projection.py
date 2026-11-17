import math
import numpy as np
from geom3d import Point3D
from matrices3d import Matrix4

AXONOMETRIC = "аксонометрическая"
PERSPECTIVE = "перспективная"
MODES = (AXONOMETRIC, PERSPECTIVE)


def view_matrix() -> np.ndarray:
    """
    «Камера»: изометрический ракурс.
    Поворот 45° вокруг OY, затем 35.264° вокруг OX
    (35.264° = arcsin(tg 30°) — классический изометрический угол).
    """
    ax = math.asin(math.tan(math.radians(30)))
    return Matrix4.rotation_x(ax) @ Matrix4.rotation_y(math.radians(45))


def project(p: Point3D, mode: str, distance: float = 8.0):
    """
    Point3D -> (sx, sy, depth).
    sx, sy — экранные координаты (Y вниз, как в canvas);
    depth  — глубина для алгоритма художника (больше = дальше от наблюдателя).
    """
    v = view_matrix() @ p.as_vector()
    x, y, z = float(v[0]), float(v[1]), float(v[2])

    if mode == PERSPECTIVE:
        # Центральная проекция: наблюдатель в z = -distance, смотрит вдоль +Z.
        # Перспективное деление: scale = d / (d + z)  <=>  деление на w = 1 + z/d.
        w = 1.0 + z / max(distance, 1e-6)
        if w < 0.1:                      # защита от деления на ~0
            w = 0.1
        return (x / w, -y / w, z)

    # Параллельная (аксонометрическая): просто отбрасываем Z.
    return (x, -y, z)