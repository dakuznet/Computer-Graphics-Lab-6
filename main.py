"""
MAIN (GUI) — интегратор лабораторной №7-9.

Распределение зон:
• Dev 1 (этот файл + polyhedra.py + projection.py): пункты 1-2 —
  отображение правильного многогранника, аффинные преобразования матрицами.
• Dev 2: пункт 3 (отражения), пункт 4 (масштаб отн. центра).
• Dev 3: пункт 5 (вращение вокруг прямой через центр), пункт 6 (произвольная прямая).

ТОЧКИ ИНТЕГРАЦИИ ДЛЯ СОКОМАНДНИКОВ:
1) matrices3d.Matrix4 — добавить статические фабрики матриц (секции размечены).
2) App._apply_matrix(M, msg) — единственная точка применения: трансформирует
   модель, логирует параметры и матрицу, перерисовывает сцену.
3) App.poly / App.base_poly — текущая модель и оригинал;
   Matrix4.around_center(M, c) — готовый хелпер T(c)·M·T(-c) для пунктов 4-5.
"""
import math
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

import numpy as np

import matrices3d as m3d
import polyhedra as ph
import projection as prj


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Лаб. 7-9: правильные многогранники и аффинные преобразования 3D")
        root.geometry("1150x720")

        self.base_poly = None          # оригинал модели (для сброса)
        self.poly = None               # текущая модель
        self.base_radius = 1.0         # радиус оригинала (фиксированный масштаб вида)
        self.proj_mode = tk.StringVar(value=prj.AXONOMETRIC)
        self.persp_distance = 8.0      # параметр перспективной проекции

        self._build_ui()
        self._load_polyhedron(self.combo.get())

    # ──────────────────────────── UI ────────────────────────────
    def _build_ui(self):
        left = tk.Frame(self.root, width=310, bg="#f4f4f4")
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        def section(title):
            tk.Label(left, text=title, font=("Arial", 11, "bold"),
                     bg="#f4f4f4").pack(pady=(12, 2))

        def btn(text, cmd):
            tk.Button(left, text=text, command=cmd, width=32).pack(padx=8, pady=2)

        # ── Пункт 1: выбор многогранника ──
        section("Пункт 1 · Многогранник")
        self.combo = ttk.Combobox(left, values=list(ph.REGISTRY),
                                  state="readonly", width=30)
        self.combo.set("Гексаэдр (куб)")
        self.combo.pack(padx=8, pady=2)
        self.combo.bind("<<ComboboxSelected>>",
                        lambda e: self._load_polyhedron(self.combo.get()))
        btn("Сброс к исходному", self._reset)

        # ── Пункт 2: аффинные преобразования матрицами ──
        section("Dev 1 · Пункт 2 — Преобразования")
        btn("Смещение (dx, dy, dz)", self._tr_translate)
        btn("Поворот вокруг оси (угол)", self._tr_rotate)
        btn("Масштаб (sx, sy, sz)", self._tr_scale)

        # ── Переключение проекций ──
        section("Проекции")
        for m in prj.MODES:
            tk.Radiobutton(left, text=m, variable=self.proj_mode, value=m,
                           bg="#f4f4f4", anchor="w",
                           command=lambda m=m: self._set_projection(m)
                           ).pack(fill=tk.X, padx=14)

        # ── Пункт 3: Отражения ──
        section("Dev 2 · Пункт 3 — Отражения")
        btn("Отражение отн. XY (Z -> -Z)",
            lambda: self._apply_matrix(m3d.Matrix4.reflection_xy(),
                                       "п.3: отражение отн. XY"))
        btn("Отражение отн. XZ (Y -> -Y)",
            lambda: self._apply_matrix(m3d.Matrix4.reflection_xz(),
                                       "п.3: отражение отн. XZ"))
        btn("Отражение отн. YZ (X -> -X)",
            lambda: self._apply_matrix(m3d.Matrix4.reflection_yz(),
                                       "п.3: отражение отн. YZ"))

        # ── Пункт 4: Масштабирование относительно центра ──
        section("Dev 2 · Пункт 4 — Масштаб отн. центра")
        btn("Масштаб отн. центра (sx, sy, sz)", self._tr_scale_center)

        # ═══════════ ЗОНА DEV 3 · ПУНКТЫ 5-6 (свободно) ═══════════
        # Пункт 5: M = m3d.Matrix4.around_center(m3d.Matrix4.rotation_x(a), c)
        # Пункт 6: план из лекции 9 через m3d.compose(...)
        section("Dev 3 · Пункты 5-6")
        tk.Label(left, text="(зона свободна: вращение вокруг\nпрямой через центр и произвольной)",
                 bg="#f4f4f4", fg="#888").pack()

        # ── Журнал ──
        section("Журнал")
        self.log_box = tk.Text(left, height=10, state="disabled",
                               wrap="word", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=8, pady=4)

        # ── Холст ──
        self.canvas = tk.Canvas(self.root, bg="white",
                                highlightthickness=1, highlightbackground="#aaa")
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)
        self.canvas.bind("<Configure>", self._render)

        self.status = tk.StringVar(value="Готово.")
        tk.Label(self.root, textvariable=self.status, anchor="w",
                 bg="#e0e0e0", font=("Arial", 10)).pack(side=tk.BOTTOM, fill="x")

    # ──────────────────────────── Журнал ────────────────────────────
    def log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ─────────────── ТОЧКА ИНТЕГРАЦИИ ПРЕОБРАЗОВАНИЙ ───────────────
    def _apply_matrix(self, M: np.ndarray, msg: str) -> None:
        """Применить матрицу к модели, залогировать параметры и матрицу, перерисовать."""
        self.poly.transform(M)
        self.log(f"{msg}\n     M =\n     {m3d.fmt(M)}")
        self.status.set(msg)
        self._render()

    # ──────────────────────────── Пункт 1 ────────────────────────────
    def _load_polyhedron(self, name: str):
        self.base_poly = ph.REGISTRY[name]()
        self.poly = self.base_poly.copy()
        self.base_radius = self.base_poly.radius()
        self.log(f"п.1: загружен '{name}': вершин={len(self.poly.vertices)}, "
                 f"граней={len(self.poly.faces)}")
        self._render()

    def _reset(self):
        if self.base_poly is None:
            return
        self.poly = self.base_poly.copy()
        self.log("Модель сброшена к исходной.")
        self._render()

    # ──────────────────────────── Пункт 2 ────────────────────────────
    def _tr_translate(self):
        vals = []
        for name in ("dx", "dy", "dz"):
            v = simpledialog.askfloat("Смещение", f"{name}:",
                                      parent=self.root, initialvalue=0.0)
            if v is None:
                return
            vals.append(v)
        M = m3d.Matrix4.translation(*vals)
        self._apply_matrix(M, f"п.2: смещение ({vals[0]}, {vals[1]}, {vals[2]})")

    def _tr_rotate(self):
        axis = simpledialog.askstring("Поворот", "Ось (X, Y или Z):",
                                      parent=self.root, initialvalue="Y")
        if axis is None:
            return
        axis = axis.strip().lower()
        if axis not in ("x", "y", "z"):
            messagebox.showerror("Ошибка", "Ось должна быть X, Y или Z.")
            return
        deg = simpledialog.askfloat("Поворот", "Угол (градусы):",
                                    parent=self.root, initialvalue=30.0)
        if deg is None:
            return
        rot = {"x": m3d.Matrix4.rotation_x,
               "y": m3d.Matrix4.rotation_y,
               "z": m3d.Matrix4.rotation_z}[axis]
        M = rot(math.radians(deg))
        self._apply_matrix(M, f"п.2: поворот вокруг O{axis.upper()} на {deg}°")

    def _tr_scale(self):
        vals = []
        for name in ("sx", "sy", "sz"):
            v = simpledialog.askfloat("Масштаб", f"{name}:",
                                      parent=self.root, initialvalue=1.5)
            if v is None:
                return
            vals.append(v)
        M = m3d.Matrix4.scaling(*vals)
        self._apply_matrix(M, f"п.2: масштаб ({vals[0]}, {vals[1]}, {vals[2]})")

    def _tr_scale_center(self):
        vals = []
        for name in ("sx", "sy", "sz"):
            v = simpledialog.askfloat("Масштаб отн. центра", f"{name}:",
                                      parent=self.root, initialvalue=1.5)
            if v is None:
                return
            vals.append(v)
        
        # 1. Создаем базовую матрицу масштаба
        M_scale = m3d.Matrix4.scaling(*vals)
        
        # 2. Получаем центр текущего многогранника
        center = self.poly.center()
        
        # 3. Используем хелпер around_center: T(c) * M * T(-c)
        M_final = m3d.Matrix4.around_center(M_scale, center)
        
        self._apply_matrix(M_final, f"п.4: масштаб отн. центра ({vals[0]}, {vals[1]}, {vals[2]})")
        
    # ──────────────────────────── Проекции ────────────────────────────
    def _set_projection(self, mode: str):
        self.proj_mode.set(mode)
        self.log(f"Проекция переключена: {mode}")
        self._render()

    # ──────────────────────────── Рендер ────────────────────────────
    def _render(self, _event=None):
        self.canvas.delete("all")
        if self.poly is None:
            return

        cw = max(self.canvas.winfo_width(), 100)
        ch = max(self.canvas.winfo_height(), 100)
        cx, cy = cw / 2, ch / 2
        # Фиксированный масштаб кадра по оригиналу: преобразования ВИДНЫ
        scale = min(cw, ch) / (3.2 * max(self.base_radius, 1e-6))

        mode = self.proj_mode.get()
        faces = []
        for face in self.poly.faces:
            pts = face.points(self.poly.vertices)
            proj = [prj.project(p, mode, self.persp_distance) for p in pts]
            depth = sum(q[2] for q in proj) / len(proj)
            screen = [(cx + q[0] * scale, cy + q[1] * scale) for q in proj]
            faces.append((depth, screen))

        # Алгоритм художника: дальние грани (большой depth) рисуем первыми.
        # Для выпуклых многогранников это даёт точный порядок без z-buffer.
        faces.sort(key=lambda f: -f[0])

        depths = [f[0] for f in faces]
        dmin, dmax = min(depths), max(depths)
        span = (dmax - dmin) or 1.0
        for depth, screen in faces:
            t = (depth - dmin) / span          # 0 = ближняя грань, 1 = дальняя
            coords = [c for pt in screen for c in pt]
            self.canvas.create_polygon(coords, fill=self._shade(t),
                                       outline="#222", width=1.5)

    @staticmethod
    def _shade(t: float) -> str:
        """Тонирование по глубине: ближние грани светлее."""
        near = np.array([210, 235, 255])
        far = np.array([70, 110, 170])
        c = (near * (1 - t) + far * t).astype(int)
        return "#%02x%02x%02x" % (c[0], c[1], c[2])


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()