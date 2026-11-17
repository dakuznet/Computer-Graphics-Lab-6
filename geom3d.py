from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np


@dataclass
class Point3D:
    """Точка в 3D в однородных координатах."""
    x: float
    y: float
    z: float
    w: float = 1.0

    def as_vector(self) -> np.ndarray:
        """Вектор-столбец [x, y, z, w]."""
        return np.array([self.x, self.y, self.z, self.w], dtype=float)

    @staticmethod
    def from_vector(v: np.ndarray) -> "Point3D":
        """Из результата умножения матрицы: нормализуем по w."""
        w = v[3]
        if abs(w) > 1e-12:
            return Point3D(v[0] / w, v[1] / w, v[2] / w, 1.0)
        return Point3D(v[0], v[1], v[2], 1.0)

    def transformed(self, M: np.ndarray) -> "Point3D":
        """Применить матрицу 4×4: p' = M · p."""
        return Point3D.from_vector(M @ self.as_vector())

    def to_tuple(self) -> tuple:
        return (self.x, self.y, self.z)


class Face:
    """Грань многогранника — плоский многоугольник, заданный индексами вершин."""

    def __init__(self, indices: Sequence[int]):
        self.indices: List[int] = list(indices)

    def points(self, vertices: List[Point3D]) -> List[Point3D]:
        return [vertices[i] for i in self.indices]

    def centroid(self, vertices: List[Point3D]) -> Point3D:
        pts = self.points(vertices)
        n = len(pts)
        return Point3D(sum(p.x for p in pts) / n,
                       sum(p.y for p in pts) / n,
                       sum(p.z for p in pts) / n)

    def normal(self, vertices: List[Point3D]) -> np.ndarray:
        """Нормаль по методу Ньюэлла."""
        pts = self.points(vertices)
        n = np.zeros(3)
        m = len(pts)
        for i in range(m):
            a, b = pts[i], pts[(i + 1) % m]
            n[0] += (a.y - b.y) * (a.z + b.z)
            n[1] += (a.z - b.z) * (a.x + b.x)
            n[2] += (a.x - b.x) * (a.y + b.y)
        norm = np.linalg.norm(n)
        return n / norm if norm > 1e-12 else np.array([0.0, 0.0, 1.0])


class Polyhedron:
    """Многогранник: список вершин + список граней."""

    def __init__(self, name: str, vertices: List[Point3D], faces: List[Face]):
        self.name = name
        self.vertices = vertices
        self.faces = faces

    def copy(self) -> "Polyhedron":
        return Polyhedron(self.name,
                          [Point3D(p.x, p.y, p.z, p.w) for p in self.vertices],
                          [Face(f.indices) for f in self.faces])

    def transform(self, M: np.ndarray) -> None:
        """Применить матрицу M ко всем вершинам (in-place)."""
        self.vertices = [p.transformed(M) for p in self.vertices]

    def center(self) -> Point3D:
        """Центр (среднее арифметическое вершин)."""
        n = len(self.vertices)
        if n == 0:
            return Point3D(0.0, 0.0, 0.0)
        return Point3D(sum(v.x for v in self.vertices) / n,
                       sum(v.y for v in self.vertices) / n,
                       sum(v.z for v in self.vertices) / n)

    def radius(self) -> float:
        """Радиус описанной сферы (для автомасштаба вида)."""
        c = self.center()
        return max(np.hypot(np.hypot(v.x - c.x, v.y - c.y), v.z - c.z)
                   for v in self.vertices)