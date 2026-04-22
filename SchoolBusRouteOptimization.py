"""
School Bus Route Optimization
==============================
A Tkinter GUI application for optimizing school bus routes using
heuristic algorithms (Nearest Neighbor, 2-opt, Cluster-first).

Features:
  ① Interactive Map     — place school, bus stops, bus depot on canvas
  ② Multiple Buses      — assign stops to buses with capacity constraints
  ③ Algorithms          — Nearest Neighbor, 2-Opt improvement, Cluster-then-Route
  ④ Route Visualization — color-coded routes per bus, animated traversal
  ⑤ Statistics Panel    — total distance, per-bus load, efficiency metrics

No external dependencies — uses only Python standard library.

Run:
    python SchoolBusRouteOptimization.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import random
import time
import itertools

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#f0f4f8"
SURFACE  = "#ffffff"
SIDEBAR  = "#1e293b"
BORDER   = "#cbd5e1"
INPUT_BG = "#f8fafc"

ACCENT  = "#f97316"   # orange
BLUE    = "#3b82f6"
GREEN   = "#22c55e"
RED     = "#ef4444"
PURPLE  = "#8b5cf6"
TEAL    = "#14b8a6"
AMBER   = "#f59e0b"
DARK    = "#0f172a"
MID     = "#64748b"
LIGHT   = "#94a3b8"
WHITE   = "#ffffff"

FONT_H1   = ("Georgia", 18, "bold")
FONT_H2   = ("Georgia", 12, "bold")
FONT_H3   = ("Georgia", 10, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SM   = ("Helvetica", 9)
FONT_MONO = ("Courier New", 10)
FONT_BTN  = ("Helvetica", 10, "bold")
FONT_TINY = ("Helvetica", 8)

# Bus route colors (one per bus)
BUS_COLORS = [
    "#e74c3c","#3498db","#2ecc71","#f39c12",
    "#9b59b6","#1abc9c","#e67e22","#e91e63",
    "#00bcd4","#8bc34a",
]

STOP_RADIUS  = 10
SCHOOL_SIZE  = 18
DEPOT_SIZE   = 14


# ── Data Structures ───────────────────────────────────────────────────────────
class Stop:
    def __init__(self, sid, x, y, label, students=5):
        self.id       = sid
        self.x        = x
        self.y        = y
        self.label    = label
        self.students = students
        self.bus      = -1   # assigned bus index


class RouteData:
    def __init__(self):
        self.stops       = {}    # sid -> Stop
        self.school      = None  # (x, y)
        self.depot       = None  # (x, y)
        self.num_buses   = 3
        self.capacity    = 30    # per bus
        self.routes      = []    # list of [sid, ...] per bus
        self.distances   = []    # total distance per bus
        self._sid        = 0

    def add_stop(self, x, y, label=None, students=5):
        sid = self._sid
        self._sid += 1
        lbl = label or f"S{sid}"
        self.stops[sid] = Stop(sid, x, y, lbl, students)
        return sid

    def remove_stop(self, sid):
        self.stops.pop(sid, None)
        self.routes = [[s for s in r if s != sid] for r in self.routes]

    def clear_stops(self):
        self.stops.clear()
        self.routes = []
        self.distances = []
        self._sid = 0

    def dist(self, ax, ay, bx, by):
        return math.hypot(ax-bx, ay-by)

    def stop_dist(self, a, b):
        sa, sb = self.stops[a], self.stops[b]
        return self.dist(sa.x, sa.y, sb.x, sb.y)

    def dist_to_school(self, sid):
        s = self.stops[sid]
        sx, sy = self.school
        return self.dist(s.x, s.y, sx, sy)

    def route_distance(self, route):
        if not route or self.school is None:
            return 0.0
        total = 0.0
        start = self.depot if self.depot else self.school
        prev_x, prev_y = start
        for sid in route:
            s = self.stops[sid]
            total += self.dist(prev_x, prev_y, s.x, s.y)
            prev_x, prev_y = s.x, s.y
        total += self.dist(prev_x, prev_y, *self.school)
        return round(total, 1)


# ── Algorithms ────────────────────────────────────────────────────────────────
class RouteOptimizer:

    @staticmethod
    def nearest_neighbor(data: RouteData):
        """
        Nearest Neighbor heuristic:
        1. Assign stops to buses by capacity (cluster by proximity to school).
        2. For each bus, build route by nearest-unvisited.
        """
        stops = list(data.stops.values())
        if not stops or data.school is None:
            return [], 0

        # Sort stops by distance to school
        sx, sy = data.school
        stops.sort(key=lambda s: math.hypot(s.x-sx, s.y-sy))

        # Assign to buses respecting capacity
        routes = [[] for _ in range(data.num_buses)]
        loads  = [0] * data.num_buses
        for s in stops:
            assigned = False
            for i in range(data.num_buses):
                if loads[i] + s.students <= data.capacity:
                    routes[i].append(s.id)
                    loads[i] += s.students
                    assigned = True
                    break
            if not assigned:
                routes[-1].append(s.id)  # overflow to last bus

        # Order each route by nearest neighbor from depot/school
        steps = 0
        start = data.depot if data.depot else data.school
        ordered_routes = []
        for route in routes:
            if not route:
                ordered_routes.append([])
                continue
            unvisited = list(route)
            ordered = []
            cur_x, cur_y = start
            while unvisited:
                nearest = min(unvisited,
                    key=lambda sid: math.hypot(
                        data.stops[sid].x - cur_x,
                        data.stops[sid].y - cur_y))
                ordered.append(nearest)
                unvisited.remove(nearest)
                cur_x, cur_y = data.stops[nearest].x, data.stops[nearest].y
                steps += 1
            ordered_routes.append(ordered)

        return ordered_routes, steps

    @staticmethod
    def two_opt(route, data: RouteData, max_iter=100):
        """2-opt improvement on a single route."""
        if len(route) < 4:
            return route, 0
        best = list(route)
        improved = True
        iters = 0
        while improved and iters < max_iter:
            improved = False
            for i in range(len(best)-1):
                for j in range(i+2, len(best)):
                    new_route = best[:i+1] + best[i+1:j+1][::-1] + best[j+1:]
                    if (data.route_distance(new_route) <
                            data.route_distance(best) - 0.01):
                        best = new_route
                        improved = True
            iters += 1
        return best, iters

    @staticmethod
    def cluster_then_route(data: RouteData):
        """
        Cluster stops into k groups (k-means style), then NN within each.
        """
        stops = list(data.stops.values())
        k = data.num_buses
        if not stops or data.school is None:
            return [], 0

        # Initialize centroids evenly distributed around school
        sx, sy = data.school
        centroids = []
        for i in range(k):
            angle = math.radians(i * 360 / k)
            cx = sx + 150 * math.cos(angle)
            cy = sy + 150 * math.sin(angle)
            centroids.append((cx, cy))

        # K-means iterations
        assignments = [-1] * len(stops)
        for _ in range(20):
            # Assign
            for idx, s in enumerate(stops):
                best_c = min(range(k),
                    key=lambda c: math.hypot(s.x-centroids[c][0],
                                             s.y-centroids[c][1]))
                assignments[idx] = best_c
            # Recompute centroids
            new_centroids = []
            for c in range(k):
                members = [stops[i] for i, a in enumerate(assignments) if a == c]
                if members:
                    new_centroids.append((
                        sum(s.x for s in members) / len(members),
                        sum(s.y for s in members) / len(members),
                    ))
                else:
                    new_centroids.append(centroids[c])
            if new_centroids == centroids:
                break
            centroids = new_centroids

        # Build routes from clusters with capacity check
        clusters = [[] for _ in range(k)]
        for idx, s in enumerate(stops):
            clusters[assignments[idx]].append(s.id)

        # Rebalance clusters by capacity
        loads = [sum(data.stops[sid].students for sid in c) for c in clusters]
        for c_idx, load in enumerate(loads):
            while load > data.capacity and clusters[c_idx]:
                overflow = clusters[c_idx].pop()
                target = min(range(k), key=lambda i: loads[i])
                clusters[target].append(overflow)
                loads[c_idx] -= data.stops[overflow].students
                loads[target] += data.stops[overflow].students

        # NN ordering within each cluster
        start = data.depot if data.depot else data.school
        steps = 0
        ordered_routes = []
        for route in clusters:
            if not route:
                ordered_routes.append([])
                continue
            unvisited = list(route)
            ordered = []
            cur_x, cur_y = start
            while unvisited:
                nearest = min(unvisited,
                    key=lambda sid: math.hypot(
                        data.stops[sid].x-cur_x,
                        data.stops[sid].y-cur_y))
                ordered.append(nearest)
                unvisited.remove(nearest)
                cur_x, cur_y = data.stops[nearest].x, data.stops[nearest].y
                steps += 1
            ordered_routes.append(ordered)

        return ordered_routes, steps


# ── Main App ──────────────────────────────────────────────────────────────────
class BusRouteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Bus Route Optimization")
        self.configure(bg=BG)
        self.minsize(1080, 700)
        self.resizable(True, True)

        self.data       = RouteData()
        self.place_mode = "stop"   # stop | school | depot
        self.anim_after = None

        self._build_ui()
        self._load_sample()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        sb = tk.Frame(root, bg=SIDEBAR, width=230)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self._build_sidebar(sb)

        right = tk.Frame(root, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_header(right)

        paned = tk.Frame(right, bg=BG)
        paned.pack(fill="both", expand=True)
        paned.columnconfigure(0, weight=3)
        paned.columnconfigure(1, weight=1)
        paned.rowconfigure(0, weight=1)

        self._build_canvas(paned)
        self._build_info_panel(paned)
        self._build_statusbar(right)

    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=SURFACE,
                       highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🚌  School Bus Route Optimizer",
                 font=FONT_H1, bg=SURFACE, fg=DARK,
                 pady=12, padx=20, anchor="w").pack(side="left")
        self.hdr_stats_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self.hdr_stats_var,
                 font=FONT_SM, bg=SURFACE, fg=MID,
                 padx=16).pack(side="right")

    def _build_sidebar(self, sb):
        tk.Label(sb, text="🚌 Route\nOptimizer",
                 font=("Georgia", 13, "bold"),
                 bg=SIDEBAR, fg=WHITE,
                 pady=16, padx=16, justify="left").pack(fill="x")
        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16)

        # Place mode
        self._sec_label(sb, "PLACE ON MAP")
        modes = [
            ("🏫 School",   "school", GREEN),
            ("🚌 Bus Depot","depot",  AMBER),
            ("📍 Bus Stop", "stop",   ACCENT),
        ]
        self._mode_btns = {}
        for label, mode, color in modes:
            b = tk.Button(sb, text=label, font=FONT_BODY,
                          bg=SIDEBAR, fg=LIGHT,
                          activebackground=color, activeforeground=WHITE,
                          relief="flat", anchor="w",
                          padx=20, pady=9, cursor="hand2",
                          command=lambda m=mode, c=color: self._set_mode(m, c))
            b.pack(fill="x")
            self._mode_btns[mode] = (b, color)
        self._set_mode("stop", ACCENT)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Bus settings
        self._sec_label(sb, "BUS SETTINGS")
        for label, key, default in [
            ("Number of Buses", "num_buses", "3"),
            ("Capacity / Bus",  "capacity",  "30"),
        ]:
            f = tk.Frame(sb, bg=SIDEBAR)
            f.pack(fill="x", padx=16, pady=3)
            tk.Label(f, text=label, font=FONT_TINY,
                     bg=SIDEBAR, fg=LIGHT, anchor="w").pack(fill="x")
            v = tk.StringVar(value=default)
            setattr(self, f"_{key}_var", v)
            tk.Entry(f, textvariable=v, font=FONT_MONO,
                     bg="#2d3748", fg=WHITE, relief="flat",
                     insertbackground=WHITE, width=10).pack(
                fill="x", ipady=4)
        self._sb_btn(sb, "Apply Settings", self._apply_settings, TEAL)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Algorithm
        self._sec_label(sb, "ALGORITHM")
        self.algo_var = tk.StringVar(value="Cluster-then-Route")
        ttk.Combobox(sb, textvariable=self.algo_var,
                     state="readonly",
                     values=["Nearest Neighbor",
                             "Nearest Neighbor + 2-Opt",
                             "Cluster-then-Route"]).pack(
            fill="x", padx=16, pady=4, ipady=4)

        self._sb_btn(sb, "▶  Optimize Routes", self._run_optimization, GREEN)
        self._sb_btn(sb, "▶  Animate Route",   self._animate_routes,  BLUE)
        self._sb_btn(sb, "⟳  Clear Routes",    self._clear_routes,    MID)
        self._sb_btn(sb, "🗑  Clear All Stops", self._clear_all,       RED)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Presets
        self._sec_label(sb, "PRESETS")
        self.preset_var = tk.StringVar(value="Sample Town")
        ttk.Combobox(sb, textvariable=self.preset_var,
                     state="readonly",
                     values=["Sample Town","Dense City",
                              "Suburban","Random 20"]).pack(
            fill="x", padx=16, pady=4, ipady=4)
        self._sb_btn(sb, "Load Preset",
                     lambda: self._load_preset(self.preset_var.get()), ACCENT)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Stats
        self._sec_label(sb, "STATISTICS")
        stat_defs = [
            ("Total Stops",    "stat_stops"),
            ("Total Students", "stat_students"),
            ("Buses Used",     "stat_buses"),
            ("Total Distance", "stat_dist"),
            ("Avg Distance",   "stat_avg"),
            ("Algorithm",      "stat_algo"),
            ("Time (ms)",      "stat_time"),
        ]
        self._stat_vars = {}
        for label, key in stat_defs:
            f = tk.Frame(sb, bg=SIDEBAR)
            f.pack(fill="x", padx=20, pady=2)
            tk.Label(f, text=label+":", font=FONT_TINY,
                     bg=SIDEBAR, fg="#64748b", anchor="w").pack(fill="x")
            v = tk.StringVar(value="—")
            tk.Label(f, textvariable=v,
                     font=("Helvetica", 10, "bold"),
                     bg=SIDEBAR, fg=WHITE, anchor="w").pack(fill="x")
            self._stat_vars[key] = v

    def _sec_label(self, parent, text):
        tk.Label(parent, text=text, font=FONT_TINY,
                 bg=SIDEBAR, fg="#475569",
                 anchor="w", pady=4).pack(fill="x", padx=20)

    def _sb_btn(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_BTN, bg=color, fg=WHITE,
                  relief="flat", cursor="hand2",
                  pady=7, padx=16).pack(fill="x", padx=16, pady=3)

    def _set_mode(self, mode, color):
        self.place_mode = mode
        for m, (b, c) in self._mode_btns.items():
            b.configure(bg=c if m == mode else SIDEBAR,
                        fg=WHITE if m == mode else LIGHT)
        hints = {
            "school": "Click map to place the SCHOOL",
            "depot":  "Click map to place the BUS DEPOT",
            "stop":   "Click map to place BUS STOPS  |  Right-click stop to edit",
        }
        self.status_var.set(hints.get(mode, ""))

    def _apply_settings(self):
        try:
            self.data.num_buses = max(1, int(self._num_buses_var.get()))
            self.data.capacity  = max(1, int(self._capacity_var.get()))
        except ValueError:
            messagebox.showerror("Error", "Enter valid integers.")

    # ── Canvas ────────────────────────────────────────────────────────────────
    def _build_canvas(self, parent):
        f = tk.Frame(parent, bg=SURFACE,
                     highlightthickness=1, highlightbackground=BORDER)
        f.grid(row=0, column=0, sticky="nsew", padx=(8,4), pady=8)

        self.canvas = tk.Canvas(f, bg="#e8f4f8", highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>",        self._canvas_click)
        self.canvas.bind("<Button-3>",        self._canvas_right)
        self.canvas.bind("<Configure>",       lambda e: self._redraw())

    def _build_info_panel(self, parent):
        f = tk.Frame(parent, bg=SURFACE,
                     highlightthickness=1, highlightbackground=BORDER)
        f.grid(row=0, column=1, sticky="nsew", padx=(4,8), pady=8)

        tk.Label(f, text="Route Details", font=FONT_H2,
                 bg=SURFACE, fg=DARK, pady=10, padx=10,
                 anchor="w").pack(fill="x")
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x")

        self.route_text = tk.Text(f, font=FONT_SM,
                                  bg=INPUT_BG, fg=DARK,
                                  relief="flat", padx=8, pady=6,
                                  state="disabled", wrap="word")
        self.route_text.pack(fill="both", expand=True)

        # Mini distance chart
        tk.Label(f, text="Distance per Bus", font=FONT_H3,
                 bg=SURFACE, fg=MID, pady=6, padx=10,
                 anchor="w").pack(fill="x")
        self.dist_canvas = tk.Canvas(f, bg=INPUT_BG, height=100,
                                     highlightthickness=0)
        self.dist_canvas.pack(fill="x", padx=8, pady=(0,8))

    def _build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=INPUT_BG,
                       highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x", padx=8, pady=(0,6))
        self.status_var = tk.StringVar(
            value="Ready  |  Select a mode and click the map")
        tk.Label(bar, textvariable=self.status_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID,
                 anchor="w", pady=5, padx=10).pack(fill="x")

    # ── Canvas Interaction ────────────────────────────────────────────────────
    def _canvas_click(self, event):
        x, y = event.x, event.y
        if self.place_mode == "school":
            self.data.school = (x, y)
            self.status_var.set(f"School placed at ({x},{y})")
        elif self.place_mode == "depot":
            self.data.depot = (x, y)
            self.status_var.set(f"Depot placed at ({x},{y})")
        elif self.place_mode == "stop":
            sid = self.data.add_stop(x, y)
            self.status_var.set(f"Stop {self.data.stops[sid].label} added")
        self._update_stats()
        self._redraw()

    def _canvas_right(self, event):
        # Find clicked stop
        x, y = event.x, event.y
        hit = self._hit_stop(x, y)
        if hit is not None:
            s = self.data.stops[hit]
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label=f"Edit '{s.label}'",
                             command=lambda: self._edit_stop(hit))
            menu.add_command(label="Delete Stop",
                             command=lambda: self._del_stop(hit))
            menu.post(event.x_root, event.y_root)

    def _edit_stop(self, sid):
        s = self.data.stops[sid]
        new_students = simpledialog.askinteger(
            "Edit Stop",
            f"Students at stop '{s.label}':",
            initialvalue=s.students, minvalue=1, maxvalue=100,
            parent=self)
        if new_students is not None:
            s.students = new_students
            self._update_stats()
            self._redraw()

    def _del_stop(self, sid):
        self.data.remove_stop(sid)
        self._update_stats()
        self._redraw()

    def _hit_stop(self, x, y):
        for sid, s in self.data.stops.items():
            if math.hypot(s.x-x, s.y-y) <= STOP_RADIUS + 4:
                return sid
        return None

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _redraw(self):
        self.canvas.delete("all")
        W = self.canvas.winfo_width()
        H = self.canvas.winfo_height()

        # Background map texture
        for gx in range(0, W, 50):
            self.canvas.create_line(gx, 0, gx, H, fill="#d4e6f0", width=1)
        for gy in range(0, H, 50):
            self.canvas.create_line(0, gy, W, gy, fill="#d4e6f0", width=1)

        # Routes
        if self.data.routes:
            for bus_idx, route in enumerate(self.data.routes):
                if not route:
                    continue
                color = BUS_COLORS[bus_idx % len(BUS_COLORS)]
                start = self.data.depot or self.data.school
                if start is None:
                    continue
                pts = [start] + [(self.data.stops[sid].x, self.data.stops[sid].y)
                                  for sid in route if sid in self.data.stops]
                if self.data.school:
                    pts.append(self.data.school)
                for i in range(len(pts)-1):
                    x1,y1 = pts[i]; x2,y2 = pts[i+1]
                    # Arrow line
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color, width=3, arrow=tk.LAST,
                        arrowshape=(10,12,4), dash=(8,3))
                    # Distance label on midpoint
                    mx, my = (x1+x2)/2, (y1+y2)/2
                    d = math.hypot(x2-x1, y2-y1)
                    self.canvas.create_text(
                        mx, my-8, text=f"{d:.0f}",
                        font=FONT_TINY, fill=color)

        # Depot
        if self.data.depot:
            dx, dy = self.data.depot
            self.canvas.create_rectangle(
                dx-DEPOT_SIZE, dy-DEPOT_SIZE,
                dx+DEPOT_SIZE, dy+DEPOT_SIZE,
                fill=AMBER, outline=DARK, width=2)
            self.canvas.create_text(dx, dy, text="🏭",
                                    font=("Helvetica", 12))
            self.canvas.create_text(dx, dy+DEPOT_SIZE+10,
                                    text="DEPOT", font=FONT_TINY, fill=AMBER)

        # School
        if self.data.school:
            sx, sy = self.data.school
            pts = [sx, sy-SCHOOL_SIZE,
                   sx+SCHOOL_SIZE, sy+SCHOOL_SIZE//2,
                   sx-SCHOOL_SIZE, sy+SCHOOL_SIZE//2]
            self.canvas.create_polygon(pts, fill=RED, outline=DARK, width=2)
            self.canvas.create_text(sx, sy+3, text="🏫",
                                    font=("Helvetica", 12))
            self.canvas.create_text(sx, sy+SCHOOL_SIZE+10,
                                    text="SCHOOL", font=FONT_TINY, fill=RED)

        # Stops
        for sid, s in self.data.stops.items():
            bus_idx = s.bus
            fill = BUS_COLORS[bus_idx % len(BUS_COLORS)] if bus_idx >= 0 else "#94a3b8"
            # Shadow
            self.canvas.create_oval(
                s.x-STOP_RADIUS+2, s.y-STOP_RADIUS+2,
                s.x+STOP_RADIUS+2, s.y+STOP_RADIUS+2,
                fill="#00000020", outline="")
            # Circle
            self.canvas.create_oval(
                s.x-STOP_RADIUS, s.y-STOP_RADIUS,
                s.x+STOP_RADIUS, s.y+STOP_RADIUS,
                fill=fill, outline=DARK, width=1.5)
            # Label
            self.canvas.create_text(s.x, s.y,
                                    text=str(s.students),
                                    font=("Helvetica", 8, "bold"),
                                    fill=WHITE)
            self.canvas.create_text(s.x, s.y+STOP_RADIUS+8,
                                    text=s.label,
                                    font=FONT_TINY, fill=DARK)

        # Legend
        if self.data.routes:
            lx, ly = 12, 12
            for i, route in enumerate(self.data.routes):
                if not route:
                    continue
                color = BUS_COLORS[i % len(BUS_COLORS)]
                load  = sum(self.data.stops[sid].students
                            for sid in route if sid in self.data.stops)
                self.canvas.create_rectangle(lx, ly, lx+14, ly+14,
                                             fill=color, outline="")
                self.canvas.create_text(lx+20, ly+7,
                                        text=f"Bus {i+1}: {len(route)} stops,"
                                             f" {load} students",
                                        font=FONT_TINY, fill=DARK, anchor="w")
                ly += 18

    # ── Optimization ──────────────────────────────────────────────────────────
    def _run_optimization(self):
        if not self.data.stops:
            messagebox.showwarning("Empty", "Add bus stops first.")
            return
        if self.data.school is None:
            messagebox.showwarning("No School",
                                   "Place the school on the map first.")
            return

        self._apply_settings()
        algo = self.algo_var.get()
        t0 = time.perf_counter()

        if algo == "Nearest Neighbor":
            routes, steps = RouteOptimizer.nearest_neighbor(self.data)
        elif algo == "Nearest Neighbor + 2-Opt":
            routes, steps = RouteOptimizer.nearest_neighbor(self.data)
            improved = []
            for r in routes:
                r2, extra = RouteOptimizer.two_opt(r, self.data)
                improved.append(r2)
                steps += extra
            routes = improved
        else:  # Cluster-then-Route
            routes, steps = RouteOptimizer.cluster_then_route(self.data)

        elapsed = (time.perf_counter() - t0) * 1000
        self.data.routes = routes

        # Assign bus indices to stops
        for s in self.data.stops.values():
            s.bus = -1
        for i, route in enumerate(routes):
            for sid in route:
                if sid in self.data.stops:
                    self.data.stops[sid].bus = i

        # Compute distances
        self.data.distances = [self.data.route_distance(r) for r in routes]
        total_dist = sum(self.data.distances)
        active = sum(1 for r in routes if r)

        self._stat_vars["stat_algo"].set(algo.split()[0])
        self._stat_vars["stat_time"].set(f"{elapsed:.2f}")
        self._stat_vars["stat_dist"].set(f"{total_dist:.0f} px")
        avg = total_dist / active if active else 0
        self._stat_vars["stat_avg"].set(f"{avg:.0f} px")

        self._update_stats()
        self._redraw()
        self._update_route_details()
        self._draw_dist_chart()
        self.status_var.set(
            f"{algo} complete — {active} routes, "
            f"total dist={total_dist:.0f}, {elapsed:.1f} ms")

    def _clear_routes(self):
        self.data.routes = []
        self.data.distances = []
        for s in self.data.stops.values():
            s.bus = -1
        self._redraw()
        self._update_route_details()
        self.dist_canvas.delete("all")

    def _clear_all(self):
        if messagebox.askyesno("Clear", "Remove all stops, school, and depot?"):
            if self.anim_after:
                self.after_cancel(self.anim_after)
            self.data.clear_stops()
            self.data.school = None
            self.data.depot  = None
            self._redraw()
            self._update_stats()
            self._update_route_details()
            self.dist_canvas.delete("all")
            self.status_var.set("Cleared.")

    # ── Animation ─────────────────────────────────────────────────────────────
    def _animate_routes(self):
        if not self.data.routes or not any(self.data.routes):
            messagebox.showwarning("No Routes",
                                   "Run optimization first.")
            return
        if self.anim_after:
            self.after_cancel(self.anim_after)

        all_pts = []
        for i, route in enumerate(self.data.routes):
            if not route:
                continue
            color = BUS_COLORS[i % len(BUS_COLORS)]
            start = self.data.depot or self.data.school
            pts = [start] + [(self.data.stops[sid].x, self.data.stops[sid].y)
                              for sid in route if sid in self.data.stops]
            if self.data.school:
                pts.append(self.data.school)
            all_pts.append((color, pts, i+1))

        self._redraw()
        self._anim_step(all_pts, 0, 0)

    def _anim_step(self, all_routes, route_idx, pt_idx):
        if route_idx >= len(all_routes):
            self.status_var.set("Animation complete.")
            return

        color, pts, bus_num = all_routes[route_idx]
        if pt_idx >= len(pts)-1:
            # Move to next route
            self.anim_after = self.after(
                200, self._anim_step, all_routes, route_idx+1, 0)
            return

        x1, y1 = pts[pt_idx]
        x2, y2 = pts[pt_idx+1]
        self.canvas.create_line(
            x1, y1, x2, y2,
            fill=color, width=5, arrow=tk.LAST,
            arrowshape=(12,14,5))
        # Animated bus icon
        mx, my = (x1+x2)/2, (y1+y2)/2
        self.canvas.create_text(mx, my-14,
                                text=f"🚌 Bus {bus_num}",
                                font=("Helvetica", 9, "bold"),
                                fill=color)
        self.status_var.set(
            f"Animating Bus {bus_num} — stop {pt_idx+1}/{len(pts)-1}")
        self.anim_after = self.after(
            400, self._anim_step, all_routes, route_idx, pt_idx+1)

    # ── Route Details Panel ───────────────────────────────────────────────────
    def _update_route_details(self):
        self.route_text.config(state="normal")
        self.route_text.delete("1.0", "end")

        if not self.data.routes:
            self.route_text.insert("1.0", "No routes yet.\nRun optimization first.")
            self.route_text.config(state="disabled")
            return

        for i, route in enumerate(self.data.routes):
            if not route:
                continue
            color = BUS_COLORS[i % len(BUS_COLORS)]
            load  = sum(self.data.stops[sid].students
                        for sid in route if sid in self.data.stops)
            dist  = self.data.distances[i] if i < len(self.data.distances) else 0
            cap   = self.data.capacity
            pct   = load / cap * 100 if cap > 0 else 0

            self.route_text.insert("end",
                f"━━ Bus {i+1} ━━━━━━━━━━━━━━━━\n")
            self.route_text.insert("end",
                f"Stops    : {len(route)}\n")
            self.route_text.insert("end",
                f"Students : {load}/{cap} ({pct:.0f}%)\n")
            self.route_text.insert("end",
                f"Distance : {dist:.0f} px\n")
            self.route_text.insert("end", "Route:\n")
            start_lbl = "DEPOT" if self.data.depot else "SCHOOL"
            stop_labels = [self.data.stops[sid].label
                           for sid in route if sid in self.data.stops]
            self.route_text.insert("end",
                f"  {start_lbl} → " +
                " → ".join(stop_labels) +
                " → SCHOOL\n\n")

        self.route_text.config(state="disabled")

    def _draw_dist_chart(self):
        c = self.dist_canvas
        c.delete("all")
        self.update_idletasks()
        W = c.winfo_width() or 200
        H = 100
        dists = [d for d in self.data.distances if d > 0]
        if not dists:
            return
        max_d = max(dists)
        bar_w = max(10, (W - 20) // len(dists) - 6)
        x = 14
        for i, d in enumerate(dists):
            bh = int((d / max_d) * (H - 30))
            color = BUS_COLORS[i % len(BUS_COLORS)]
            c.create_rectangle(x, H-20-bh, x+bar_w, H-20,
                                fill=color, outline="")
            c.create_text(x+bar_w//2, H-10,
                          text=f"B{i+1}", font=FONT_TINY, fill=MID)
            c.create_text(x+bar_w//2, H-24-bh,
                          text=f"{d:.0f}", font=FONT_TINY, fill=DARK)
            x += bar_w + 6

    # ── Stats ─────────────────────────────────────────────────────────────────
    def _update_stats(self):
        stops = len(self.data.stops)
        students = sum(s.students for s in self.data.stops.values())
        active = sum(1 for r in self.data.routes if r)
        self._stat_vars["stat_stops"].set(str(stops))
        self._stat_vars["stat_students"].set(str(students))
        self._stat_vars["stat_buses"].set(
            f"{active}/{self.data.num_buses}" if active > 0 else
            str(self.data.num_buses))
        self.hdr_stats_var.set(
            f"Stops: {stops}  ·  Students: {students}  ·  Buses: {self.data.num_buses}")

    # ── Presets ───────────────────────────────────────────────────────────────
    def _load_preset(self, name):
        self.data.clear_stops()
        self.data.school = None
        self.data.depot  = None
        self.update_idletasks()
        W = max(self.canvas.winfo_width(), 600)
        H = max(self.canvas.winfo_height(), 480)
        cx, cy = W//2, H//2

        if name == "Sample Town":
            self.data.school = (cx, cy)
            self.data.depot  = (cx-200, cy-120)
            self.data.num_buses  = 3
            self.data.capacity   = 30
            stops_data = [
                (cx-180, cy-60,  "S1", 8),  (cx-150, cy+40, "S2", 6),
                (cx-80,  cy-120, "S3", 5),  (cx-200, cy+80, "S4", 9),
                (cx+80,  cy-100, "S5", 7),  (cx+160, cy-40, "S6", 6),
                (cx+120, cy+80,  "S7", 8),  (cx+40,  cy+130,"S8", 5),
                (cx-60,  cy+100, "S9", 7),  (cx-120, cy-80, "S10",6),
                (cx+200, cy+40,  "S11",5),  (cx-30,  cy-140,"S12",8),
            ]
            for x, y, lbl, stu in stops_data:
                self.data.add_stop(x, y, lbl, stu)

        elif name == "Dense City":
            self.data.school = (cx+10, cy+10)
            self.data.depot  = (cx-250, cy-150)
            self.data.num_buses = 4
            self.data.capacity  = 25
            random.seed(7)
            for i in range(18):
                x = random.randint(cx-240, cx+240)
                y = random.randint(cy-160, cy+160)
                self.data.add_stop(x, y, f"C{i+1}", random.randint(3,12))

        elif name == "Suburban":
            self.data.school = (cx, cy+120)
            self.data.depot  = (cx-280, cy+120)
            self.data.num_buses = 2
            self.data.capacity  = 40
            for i in range(10):
                x = cx - 240 + i*55
                y = cy - 80 + (i%3)*60
                self.data.add_stop(x, y, f"B{i+1}", random.randint(5,15))

        elif name == "Random 20":
            self.data.school = (cx, cy)
            self.data.depot  = (cx-220, cy-120)
            self.data.num_buses = 4
            self.data.capacity  = 30
            random.seed(99)
            for i in range(20):
                x = random.randint(cx-260, cx+260)
                y = random.randint(cy-180, cy+180)
                self.data.add_stop(x, y, f"R{i+1}", random.randint(3,10))

        self._num_buses_var.set(str(self.data.num_buses))
        self._capacity_var.set(str(self.data.capacity))
        self.data.routes = []
        self.data.distances = []
        self._update_stats()
        self._redraw()
        self._update_route_details()
        self.dist_canvas.delete("all")
        self.status_var.set(f"Loaded preset: {name}")

    def _load_sample(self):
        self.after(100, lambda: self._load_preset("Sample Town"))


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = BusRouteApp()
    app.mainloop()
