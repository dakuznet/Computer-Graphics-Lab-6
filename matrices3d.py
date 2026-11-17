import math
import numpy as np

from geom3d import Point3D


class Matrix4:
    """Фабрика матриц аффинных преобразований 4×4."""

    @staticmethod
    def identity() -> np.ndarray:
        return np.eye(4, dtype=float)

    # ── Смещение ──
    @staticmethod
    def translation(dx: float, dy: float, dz: float) -> np.ndarray:
        return np.array([
            [1, 0, 0, dx],
            [0, 1, 0, dy],
            [0, 0, 1, dz],
            [0, 0, 0, 1],
        ], dtype=float)

    # ── Масштаб ──
    @staticmethod
    def scaling(sx: float, sy: float, sz: float) -> np.ndarray:
        return np.array([
            [sx, 0, 0, 0],
            [0, sy, 0, 0],
            [0, 0, sz, 0],
            [0, 0, 0, 1],
        ], dtype=float)

    # ── Повороты вокруг координатных осей (через начало координат) ──
    @staticmethod
    def rotation_x(a: float) -> np.ndarray:
        c, s = math.cos(a), math.sin(a)
        return np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1],
        ], dtype=float)

    @staticmethod
    def rotation_y(a: float) -> np.ndarray:
        c, s = math.cos(a), math.sin(a)
        return np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1],
        ], dtype=float)

    @staticmethod
    def rotation_z(a: float) -> np.ndarray:
        c, s = math.cos(a), math.sin(a)
        return np.array([
            [c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=float)

    @staticmethod
    def around_center(M_centered: np.ndarray, c: Point3D) -> np.ndarray:
        """Применить матрицу M относительно точки c (центр многогранника и т.п.)."""
        t = Matrix4.translation(c.x, c.y, c.z)
        t_inv = Matrix4.translation(-c.x, -c.y, -c.z)
        return t @ M_centered @ t_inv

    # ПУНКТ 3 — отражения относительно координатных плоскостей
    @staticmethod
    def reflection_xy() -> np.ndarray:   # z -> -z
        return Matrix4.scaling(1, 1, -1)

    @staticmethod
    def reflection_xz() -> np.ndarray:   # y -> -y
        return Matrix4.scaling(1, -1, 1)

    @staticmethod
    def reflection_yz() -> np.ndarray:   # x -> -x
        return Matrix4.scaling(-1, 1, 1)

def compose(*matrices: np.ndarray) -> np.ndarray:
    """Композиция: compose(A, B) = B·A, т.е. первым применяется A."""
    result = matrices[0]
    for m in matrices[1:]:
        result = m @ result
    return result


def fmt(M: np.ndarray, prec: int = 2) -> str:
    """Компактный вывод матрицы 4×4 в журнал."""
    return "\n     ".join(
        "[" + "  ".join(f"{v:{prec + 5}.{prec}f}" for v in row) + "]" for row in M
    )