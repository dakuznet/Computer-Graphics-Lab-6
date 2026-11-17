import math
import tkinter as tk
from tkinter import simpledialog, messagebox

import matrices3d as m3d
import projection as prj
from geom3d import Point3D

def rotate_around_center(center, axis, angle):
    if axis == "X":
        R = m3d.Matrix4.rotation_x(angle)
    elif axis == "Y":
        R = m3d.Matrix4.rotation_y(angle)
    else:
        R = m3d.Matrix4.rotation_z(angle)
    return m3d.Matrix4.around_center(R, center)


def rotate_around_line(a, b, angle):
    l = b.x - a.x
    m = b.y - a.y
    n = b.z - a.z
    length = math.sqrt(l * l + m * m + n * n)
    l, m, n = l / length, m / length, n / length

    d = math.sqrt(m * m + n * n)
    if d != 0:
        alpha = math.atan2(m, n)
    else:
        alpha = 0 
    beta = math.atan2(-l, d)

    T = m3d.Matrix4.translation(-a.x, -a.y, -a.z)
    Rx = m3d.Matrix4.rotation_x(alpha)
    Ry = m3d.Matrix4.rotation_y(beta)
    Rz = m3d.Matrix4.rotation_z(angle)
    Ry_inv = m3d.Matrix4.rotation_y(-beta)
    Rx_inv = m3d.Matrix4.rotation_x(-alpha)
    T_inv = m3d.Matrix4.translation(a.x, a.y, a.z)
    return m3d.compose(T, Rx, Ry, Rz, Ry_inv, Rx_inv, T_inv)


class RotationPanel:

    def __init__(self, app, parent):
        self.app = app
        self.line = None           
        self.line_vertices = None  

        self.old_render = app._render
        app._render = self.render

        tk.Label(parent, text="Пункты 5-6 — Вращение",
                 font=("Arial", 11, "bold"), bg="#f4f4f4").pack(pady=(12, 2))
        tk.Button(parent, text="Вращение вокруг прямой через центр",
                  command=self.rotate_center, width=32).pack(padx=8, pady=2)
        tk.Button(parent, text="Поворот вокруг прямой AB",
                  command=self.rotate_line, width=32).pack(padx=8, pady=2)

    def rotate_center(self):
        axis = simpledialog.askstring("Вращение вокруг центра",
                                      "Прямая параллельна оси (X, Y или Z):",
                                      parent=self.app.root, initialvalue="Y")
        if axis is None:
            return
        axis = axis.strip().upper()
        if axis not in ("X", "Y", "Z"):
            messagebox.showerror("Ошибка", "Ось должна быть X, Y или Z.")
            return
        deg = simpledialog.askfloat("Вращение вокруг центра", "Угол (градусы):",
                                    parent=self.app.root, initialvalue=30.0)
        if deg is None:
            return

        center = self.app.poly.center()
        M = rotate_around_center(center, axis, math.radians(deg))
        self.app._apply_matrix(M, f"п.5: вращение вокруг прямой через центр "
                                  f"параллельно O{axis} на {deg}°")

        k = 2 * self.app.base_radius
        dx, dy, dz = {"X": (k, 0, 0), "Y": (0, k, 0), "Z": (0, 0, k)}[axis]
        p1 = Point3D(center.x - dx, center.y - dy, center.z - dz)
        p2 = Point3D(center.x + dx, center.y + dy, center.z + dz)
        self.show_line(p1, p2)

    def rotate_line(self):
        names = ["x1", "y1", "z1", "x2", "y2", "z2"]
        defaults = [0, 0, 0, 1, 1, 1]
        vals = []
        for name, default in zip(names, defaults):
            v = simpledialog.askfloat("Поворот вокруг прямой",
                                      f"Точка {'A' if name[1] == '1' else 'B'}, {name}:",
                                      parent=self.app.root, initialvalue=default)
            if v is None:
                return
            vals.append(v)
        deg = simpledialog.askfloat("Поворот вокруг прямой", "Угол (градусы):",
                                    parent=self.app.root, initialvalue=30.0)
        if deg is None:
            return

        a = Point3D(vals[0], vals[1], vals[2])
        b = Point3D(vals[3], vals[4], vals[5])
        if a.x == b.x and a.y == b.y and a.z == b.z:
            messagebox.showerror("Ошибка", "Точки A и B совпадают.")
            return

        M = rotate_around_line(a, b, math.radians(deg))
        self.app._apply_matrix(M, f"п.6: поворот вокруг прямой "
                                  f"A({vals[0]}, {vals[1]}, {vals[2]}) "
                                  f"B({vals[3]}, {vals[4]}, {vals[5]}) на {deg}°")

        p1 = Point3D(a.x - (b.x - a.x), a.y - (b.y - a.y), a.z - (b.z - a.z))
        p2 = Point3D(b.x + (b.x - a.x), b.y + (b.y - a.y), b.z + (b.z - a.z))
        self.show_line(p1, p2)

    def show_line(self, p1, p2):
        self.line = (p1, p2)
        self.line_vertices = self.app.poly.vertices
        self.app._render()

    def render(self, event=None):
        self.old_render(event)

        if self.line is None:
            return
        if self.app.poly.vertices is not self.line_vertices:
            return

        canvas = self.app.canvas
        cw = max(canvas.winfo_width(), 100)
        ch = max(canvas.winfo_height(), 100)
        scale = min(cw, ch) / (3.2 * self.app.base_radius)
        mode = self.app.proj_mode.get()

        pts = []
        for p in self.line:
            x, y, _ = prj.project(p, mode, self.app.persp_distance)
            pts.append(cw / 2 + x * scale)
            pts.append(ch / 2 + y * scale)
        canvas.create_line(*pts, fill="red", width=2, dash=(6, 4))