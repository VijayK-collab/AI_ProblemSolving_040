"""
Map Coloring Problem
====================
A Tkinter GUI application that demonstrates graph coloring algorithms.
Draw regions/nodes, define adjacency, and apply coloring algorithms.

Features:
  ① Interactive Canvas  — add nodes (regions), draw edges (borders)
  ② Algorithms          — Greedy, Welsh-Powell, Backtracking (exact min colors)
  ③ Presets             — Classic maps: Australia, US Regions, Petersen Graph
  ④ Statistics Panel    — chromatic number, algorithm steps, color usage
  ⑤ Color Themes        — multiple palettes (4-color, pastel, vivid, etc.)

No external dependencies — uses only Python standard library.

Run:
    python MapColoringProblem.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
import time
import copy

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#f8fafc"
SURFACE  = "#ffffff"
SIDEBAR  = "#1a1f2e"
BORDER   = "#e2e8f0"
INPUT_BG = "#f1f5f9"

ACCENT   = "#6366f1"   # indigo
GREEN    = "#22c55e"
RED      = "#ef4444"
AMBER    = "#f59e0b"
TEAL     = "#14b8a6"
DARK     = "#0f172a"
MID      = "#64748b"
LIGHT    = "#94a3b8"
WHITE    = "#ffffff"

FONT_H1   = ("Georgia", 18, "bold")
FONT_H2   = ("Georgia", 12, "bold")
FONT_H3   = ("Georgia", 10, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SM   = ("Helvetica", 9)
FONT_MONO = ("Courier New", 10)
FONT_BTN  = ("Helvetica", 10, "bold")
FONT_TINY = ("Helvetica", 8)

# ── Color Palettes ────────────────────────────────────────────────────────────
PALETTES = {
    "Four-Color Classic": [
        "#e74c3c","#3498db","#2ecc71","#f39c12",
        "#9b59b6","#1abc9c","#e67e22","#34495e",
    ],
    "Pastel": [
        "#FFB3BA","#FFDFBA","#FFFFBA","#BAFFC9",
        "#BAE1FF","#D5BAFF","#FFB3F7","#B3FFF0",
    ],
    "Vivid": [
        "#FF0000","#0000FF","#00AA00","#FF8800",
        "#AA00AA","#00AAAA","#FF00AA","#888800",
    ],
    "Earth Tones": [
        "#8B4513","#228B22","#4682B4","#DAA520",
        "#800080","#008080","#B22222","#2F4F4F",
    ],
    "Neon": [
        "#FF073A","#00FFFF","#39FF14","#FF6700",
        "#FF00FF","#CCFF00","#7DF9FF","#FF1493",
    ],
}

DEFAULT_PALETTE = "Four-Color Classic"
NODE_RADIUS = 22


# ── Graph Data Structure ──────────────────────────────────────────────────────
class Graph:
    def __init__(self):
        self.nodes   = {}   # id -> {x, y, label, color_idx}
        self.edges   = set()  # frozenset({id1, id2})
        self._nid    = 0

    def add_node(self, x, y, label=None):
        nid = self._nid
        self._nid += 1
        self.nodes[nid] = {"x": x, "y": y,
                           "label": label or str(nid),
                           "color_idx": -1}
        return nid

    def remove_node(self, nid):
        self.nodes.pop(nid, None)
        self.edges = {e for e in self.edges if nid not in e}

    def add_edge(self, a, b):
        if a != b:
            self.edges.add(frozenset({a, b}))

    def remove_edge(self, a, b):
        self.edges.discard(frozenset({a, b}))

    def neighbors(self, nid):
        result = set()
        for e in self.edges:
            lst = list(e)
            if nid in lst:
                other = lst[0] if lst[1] == nid else lst[1]
                result.add(other)
        return result

    def adjacency_list(self):
        adj = {nid: set() for nid in self.nodes}
        for e in self.edges:
            a, b = list(e)
            adj[a].add(b)
            adj[b].add(a)
        return adj

    def reset_colors(self):
        for n in self.nodes.values():
            n["color_idx"] = -1

    def clear(self):
        self.nodes.clear()
        self.edges.clear()
        self._nid = 0


# ── Coloring Algorithms ───────────────────────────────────────────────────────
class Algorithms:

    @staticmethod
    def greedy(graph):
        """Standard greedy coloring in node-id order."""
        adj  = graph.adjacency_list()
        order = list(graph.nodes.keys())
        coloring = {}
        steps = 0
        for node in order:
            used = {coloring[nb] for nb in adj[node] if nb in coloring}
            c = 0
            while c in used:
                c += 1
            coloring[node] = c
            steps += 1
        return coloring, steps

    @staticmethod
    def welsh_powell(graph):
        """Welsh-Powell: color highest-degree nodes first."""
        adj   = graph.adjacency_list()
        order = sorted(graph.nodes.keys(),
                       key=lambda n: len(adj[n]), reverse=True)
        coloring = {}
        steps = 0
        for node in order:
            used = {coloring[nb] for nb in adj[node] if nb in coloring}
            c = 0
            while c in used:
                c += 1
            coloring[node] = c
            steps += 1
        return coloring, steps

    @staticmethod
    def backtracking(graph, max_colors=8):
        """Exact minimum coloring via backtracking with forward checking."""
        nodes = list(graph.nodes.keys())
        adj   = graph.adjacency_list()
        if not nodes:
            return {}, 0

        best = [None]
        steps_count = [0]

        def is_safe(node, color, coloring):
            return all(coloring.get(nb, -1) != color for nb in adj[node])

        def backtrack(idx, coloring, num_colors):
            steps_count[0] += 1
            if idx == len(nodes):
                used = len(set(coloring.values()))
                if best[0] is None or used < len(set(best[0].values())):
                    best[0] = dict(coloring)
                return
            # Prune: if current colors already >= best, stop
            if best[0] is not None:
                if num_colors >= len(set(best[0].values())):
                    return

            node = nodes[idx]
            for c in range(num_colors + 1):
                if c >= max_colors:
                    break
                if is_safe(node, c, coloring):
                    coloring[node] = c
                    backtrack(idx + 1, coloring,
                              max(num_colors, c + 1))
                    del coloring[node]
                    if steps_count[0] > 50000:
                        return

        backtrack(0, {}, 0)
        if best[0] is None:
            # Fall back to greedy
            best[0], _ = Algorithms.greedy(graph)
        return best[0], steps_count[0]

    @staticmethod
    def dsatur(graph):
        """DSatur: dynamic saturation-based greedy — often near-optimal."""
        adj  = graph.adjacency_list()
        nodes = set(graph.nodes.keys())
        coloring = {}
        saturation = {n: set() for n in nodes}
        degree     = {n: len(adj[n]) for n in nodes}
        steps = 0

        for _ in range(len(nodes)):
            # Pick uncolored node with max saturation (tie-break: max degree)
            uncolored = [n for n in nodes if n not in coloring]
            if not uncolored:
                break
            node = max(uncolored,
                       key=lambda n: (len(saturation[n]), degree[n]))
            used = {coloring[nb] for nb in adj[node] if nb in coloring}
            c = 0
            while c in used:
                c += 1
            coloring[node] = c
            for nb in adj[node]:
                saturation[nb].add(c)
            steps += 1

        return coloring, steps


# ── Main App ──────────────────────────────────────────────────────────────────
class MapColoringApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Map Coloring Problem")
        self.configure(bg=BG)
        self.minsize(1080, 700)
        self.resizable(True, True)

        self.graph       = Graph()
        self.palette_name = DEFAULT_PALETTE
        self.palette     = PALETTES[DEFAULT_PALETTE]
        self.mode        = "add_node"   # add_node | add_edge | delete | select
        self.selected    = None         # selected node id
        self.edge_start  = None         # first node of edge being drawn
        self.drag_node   = None
        self.drag_ox = self.drag_oy = 0
        self.stats       = {}

        self._build_ui()
        self._load_preset("Australia")

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        # Sidebar
        sb = tk.Frame(root, bg=SIDEBAR, width=230)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self._build_sidebar(sb)

        # Right: canvas + bottom panel
        right = tk.Frame(root, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_canvas_area(right)
        self._build_bottom(right)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, sb):
        tk.Label(sb, text="🎨 Map Coloring", font=("Georgia", 14, "bold"),
                 bg=SIDEBAR, fg=WHITE, pady=16, padx=16).pack(fill="x")
        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16)

        # Mode buttons
        self._sec_label(sb, "EDIT MODE")
        modes = [
            ("➕ Add Node",   "add_node", ACCENT),
            ("〰 Add Edge",   "add_edge", TEAL),
            ("🗑  Delete",    "delete",   RED),
            ("✋ Move Node",  "select",   AMBER),
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
        self._set_mode("add_node", ACCENT)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Algorithm
        self._sec_label(sb, "ALGORITHM")
        self.algo_var = tk.StringVar(value="Welsh-Powell")
        algo_cb = ttk.Combobox(sb, textvariable=self.algo_var,
                               state="readonly",
                               values=["Greedy","Welsh-Powell",
                                       "DSatur","Backtracking"])
        algo_cb.pack(fill="x", padx=16, pady=4, ipady=4)

        self._sb_btn(sb, "▶  Run Coloring", self._run_coloring, GREEN)
        self._sb_btn(sb, "⟳  Reset Colors", self._reset_colors, MID)
        self._sb_btn(sb, "🗑  Clear All",    self._clear_all,   RED)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Presets
        self._sec_label(sb, "PRESETS")
        presets = ["Australia","US Regions","Petersen Graph",
                   "Complete K5","Cycle C7","Random 12"]
        self.preset_var = tk.StringVar(value="Australia")
        preset_cb = ttk.Combobox(sb, textvariable=self.preset_var,
                                 state="readonly", values=presets)
        preset_cb.pack(fill="x", padx=16, pady=4, ipady=4)
        self._sb_btn(sb, "Load Preset",
                     lambda: self._load_preset(self.preset_var.get()), ACCENT)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Palette
        self._sec_label(sb, "COLOR PALETTE")
        self.palette_var = tk.StringVar(value=DEFAULT_PALETTE)
        pal_cb = ttk.Combobox(sb, textvariable=self.palette_var,
                              state="readonly",
                              values=list(PALETTES.keys()))
        pal_cb.pack(fill="x", padx=16, pady=4, ipady=4)
        pal_cb.bind("<<ComboboxSelected>>", self._change_palette)

        tk.Frame(sb, bg="#2d3748", height=1).pack(fill="x", padx=16, pady=8)

        # Stats
        self._sec_label(sb, "STATISTICS")
        stat_defs = [
            ("Nodes",       "stat_nodes"),
            ("Edges",       "stat_edges"),
            ("Colors Used", "stat_colors"),
            ("Algorithm",   "stat_algo"),
            ("Steps",       "stat_steps"),
            ("Time (ms)",   "stat_time"),
        ]
        self._stat_vars = {}
        for label, key in stat_defs:
            f = tk.Frame(sb, bg=SIDEBAR)
            f.pack(fill="x", padx=20, pady=2)
            tk.Label(f, text=label+":", font=FONT_TINY,
                     bg=SIDEBAR, fg="#64748b", anchor="w").pack(fill="x")
            v = tk.StringVar(value="—")
            tk.Label(f, textvariable=v, font=("Helvetica", 10, "bold"),
                     bg=SIDEBAR, fg=WHITE, anchor="w").pack(fill="x")
            self._stat_vars[key] = v

    def _sec_label(self, parent, text):
        tk.Label(parent, text=text, font=FONT_TINY,
                 bg=SIDEBAR, fg="#475569",
                 anchor="w", pady=4).pack(fill="x", padx=20)

    def _sb_btn(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd,
                  font=FONT_BTN, bg=color, fg=WHITE,
                  relief="flat", activebackground=DARK,
                  activeforeground=WHITE, cursor="hand2",
                  pady=7, padx=16).pack(fill="x", padx=16, pady=3)

    def _set_mode(self, mode, color):
        self.mode = mode
        self.edge_start = None
        self.selected   = None
        for m, (b, c) in self._mode_btns.items():
            b.configure(bg=c if m == mode else SIDEBAR,
                        fg=WHITE if m == mode else LIGHT)
        self._redraw()

    # ── Canvas Area ───────────────────────────────────────────────────────────
    def _build_canvas_area(self, parent):
        canvas_frame = tk.Frame(parent, bg=BG)
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        # Toolbar above canvas
        tb = tk.Frame(canvas_frame, bg=SURFACE,
                      highlightthickness=1, highlightbackground=BORDER)
        tb.pack(fill="x", pady=(0, 4))
        self.mode_label = tk.Label(tb,
            text="Mode: Add Node  |  Click canvas to place nodes",
            font=FONT_SM, bg=SURFACE, fg=MID, anchor="w", pady=6, padx=10)
        self.mode_label.pack(side="left")
        self.color_legend = tk.Frame(tb, bg=SURFACE)
        self.color_legend.pack(side="right", padx=10)

        # Main canvas
        self.canvas = tk.Canvas(canvas_frame, bg=SURFACE,
                                highlightthickness=1,
                                highlightbackground=BORDER,
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>",        self._canvas_click)
        self.canvas.bind("<B1-Motion>",       self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Button-3>",        self._canvas_right_click)

    # ── Bottom Status Bar ─────────────────────────────────────────────────────
    def _build_bottom(self, parent):
        bot = tk.Frame(parent, bg=INPUT_BG,
                       highlightthickness=1, highlightbackground=BORDER)
        bot.pack(fill="x", padx=12, pady=(0, 8))
        self.status_var = tk.StringVar(
            value="Ready  |  Left-click: add node  |  Right-click: cancel edge")
        tk.Label(bot, textvariable=self.status_var,
                 font=FONT_SM, bg=INPUT_BG, fg=MID,
                 anchor="w", pady=5, padx=10).pack(fill="x")

    # ── Canvas Interaction ────────────────────────────────────────────────────
    def _canvas_click(self, event):
        x, y = event.x, event.y
        hit = self._hit_node(x, y)

        if self.mode == "add_node":
            if hit is None:
                nid = self.graph.add_node(x, y)
                self._update_stats()
                self._redraw()
                self.status_var.set(f"Added node {nid}")

        elif self.mode == "add_edge":
            if hit is not None:
                if self.edge_start is None:
                    self.edge_start = hit
                    self.selected   = hit
                    self.status_var.set(
                        f"Edge started from node {hit} — click another node")
                    self._redraw()
                else:
                    if hit != self.edge_start:
                        self.graph.add_edge(self.edge_start, hit)
                        self.status_var.set(
                            f"Edge added: {self.edge_start} ↔ {hit}")
                    self.edge_start = None
                    self.selected   = None
                    self._update_stats()
                    self._redraw()

        elif self.mode == "delete":
            if hit is not None:
                self.graph.remove_node(hit)
                self.status_var.set(f"Deleted node {hit}")
                self._update_stats()
                self._redraw()

        elif self.mode == "select":
            if hit is not None:
                self.drag_node = hit
                nd = self.graph.nodes[hit]
                self.drag_ox = nd["x"] - x
                self.drag_oy = nd["y"] - y
                self.selected = hit
                self._redraw()

    def _canvas_drag(self, event):
        if self.mode == "select" and self.drag_node is not None:
            nd = self.graph.nodes[self.drag_node]
            nd["x"] = event.x + self.drag_ox
            nd["y"] = event.y + self.drag_oy
            self._redraw()

    def _canvas_release(self, event):
        self.drag_node = None

    def _canvas_right_click(self, event):
        # Check if right-clicking on an edge to delete it
        hit_edge = self._hit_edge(event.x, event.y)
        if hit_edge:
            a, b = hit_edge
            self.graph.remove_edge(a, b)
            self.status_var.set(f"Edge removed: {a} ↔ {b}")
            self._update_stats()
            self._redraw()
            return
        self.edge_start = None
        self.selected   = None
        self.status_var.set("Cancelled")
        self._redraw()

    def _hit_node(self, x, y):
        for nid, nd in self.graph.nodes.items():
            if math.hypot(nd["x"]-x, nd["y"]-y) <= NODE_RADIUS + 4:
                return nid
        return None

    def _hit_edge(self, x, y, tol=8):
        for e in self.graph.edges:
            a, b = list(e)
            if a not in self.graph.nodes or b not in self.graph.nodes:
                continue
            ax, ay = self.graph.nodes[a]["x"], self.graph.nodes[a]["y"]
            bx, by = self.graph.nodes[b]["x"], self.graph.nodes[b]["y"]
            # Distance from point to segment
            dx, dy = bx-ax, by-ay
            if dx == dy == 0:
                continue
            t = max(0, min(1, ((x-ax)*dx + (y-ay)*dy) / (dx*dx+dy*dy)))
            px, py = ax+t*dx, ay+t*dy
            if math.hypot(x-px, y-py) <= tol:
                return (a, b)
        return None

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _redraw(self):
        self.canvas.delete("all")
        W = self.canvas.winfo_width()
        H = self.canvas.winfo_height()

        # Grid
        for gx in range(0, W, 40):
            self.canvas.create_line(gx, 0, gx, H, fill="#f1f5f9", width=1)
        for gy in range(0, H, 40):
            self.canvas.create_line(0, gy, W, gy, fill="#f1f5f9", width=1)

        # Edges
        for e in self.graph.edges:
            a, b = list(e)
            if a not in self.graph.nodes or b not in self.graph.nodes:
                continue
            ax, ay = self.graph.nodes[a]["x"], self.graph.nodes[a]["y"]
            bx, by = self.graph.nodes[b]["x"], self.graph.nodes[b]["y"]
            self.canvas.create_line(ax, ay, bx, by,
                                    fill="#94a3b8", width=2)

        # Edge being drawn preview
        if self.edge_start is not None and self.edge_start in self.graph.nodes:
            nd = self.graph.nodes[self.edge_start]
            self.canvas.create_line(nd["x"], nd["y"],
                                    nd["x"]+1, nd["y"]+1,
                                    fill=TEAL, width=2, dash=(6,3))

        # Nodes
        for nid, nd in self.graph.nodes.items():
            cx, cy = nd["x"], nd["y"]
            cidx   = nd["color_idx"]
            fill   = self.palette[cidx % len(self.palette)] if cidx >= 0 else "#e2e8f0"
            outline = ACCENT if nid == self.selected else (
                      TEAL  if nid == self.edge_start else "#94a3b8")
            ow = 3 if nid in (self.selected, self.edge_start) else 1.5

            # Shadow
            self.canvas.create_oval(cx-NODE_RADIUS+2, cy-NODE_RADIUS+2,
                                    cx+NODE_RADIUS+2, cy+NODE_RADIUS+2,
                                    fill="#00000015", outline="")
            # Circle
            self.canvas.create_oval(cx-NODE_RADIUS, cy-NODE_RADIUS,
                                    cx+NODE_RADIUS, cy+NODE_RADIUS,
                                    fill=fill, outline=outline, width=ow)
            # Label
            lbl = nd["label"]
            text_color = self._contrast_text(fill) if cidx >= 0 else DARK
            self.canvas.create_text(cx, cy, text=lbl,
                                    font=("Helvetica", 9, "bold"),
                                    fill=text_color)

        self._update_mode_label()
        self._draw_legend()

    def _contrast_text(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
        lum = 0.299*r + 0.587*g + 0.114*b
        return "#000000" if lum > 140 else "#ffffff"

    def _update_mode_label(self):
        hints = {
            "add_node": "Mode: Add Node  |  Left-click empty space to place a node",
            "add_edge": "Mode: Add Edge  |  Click two nodes to connect  |  Right-click: cancel",
            "delete":   "Mode: Delete    |  Left-click a node to remove  |  Right-click an edge to remove",
            "select":   "Mode: Move Node |  Drag nodes to reposition",
        }
        self.mode_label.configure(text=hints.get(self.mode, ""))

    def _draw_legend(self):
        for w in self.color_legend.winfo_children():
            w.destroy()
        used_colors = {nd["color_idx"] for nd in self.graph.nodes.values()
                       if nd["color_idx"] >= 0}
        for cidx in sorted(used_colors):
            color = self.palette[cidx % len(self.palette)]
            f = tk.Frame(self.color_legend, bg=color, width=16, height=16,
                         highlightthickness=1, highlightbackground=BORDER)
            f.pack(side="left", padx=2)

    # ── Algorithms ────────────────────────────────────────────────────────────
    def _run_coloring(self):
        if not self.graph.nodes:
            messagebox.showwarning("Empty", "Add some nodes first.")
            return
        self.graph.reset_colors()
        algo = self.algo_var.get()
        t0 = time.perf_counter()
        if algo == "Greedy":
            coloring, steps = Algorithms.greedy(self.graph)
        elif algo == "Welsh-Powell":
            coloring, steps = Algorithms.welsh_powell(self.graph)
        elif algo == "DSatur":
            coloring, steps = Algorithms.dsatur(self.graph)
        else:  # Backtracking
            coloring, steps = Algorithms.backtracking(self.graph)
        elapsed = (time.perf_counter() - t0) * 1000

        for nid, cidx in coloring.items():
            if nid in self.graph.nodes:
                self.graph.nodes[nid]["color_idx"] = cidx

        num_colors = len(set(coloring.values())) if coloring else 0
        self._stat_vars["stat_colors"].set(str(num_colors))
        self._stat_vars["stat_algo"].set(algo)
        self._stat_vars["stat_steps"].set(str(steps))
        self._stat_vars["stat_time"].set(f"{elapsed:.2f}")
        self._update_stats()
        self._redraw()
        self.status_var.set(
            f"{algo} complete — {num_colors} colors used, "
            f"{steps} steps, {elapsed:.1f} ms")

    def _reset_colors(self):
        self.graph.reset_colors()
        self._stat_vars["stat_colors"].set("—")
        self._stat_vars["stat_algo"].set("—")
        self._stat_vars["stat_steps"].set("—")
        self._stat_vars["stat_time"].set("—")
        self._redraw()
        self.status_var.set("Colors reset.")

    def _clear_all(self):
        if messagebox.askyesno("Clear", "Clear all nodes and edges?"):
            self.graph.clear()
            self._reset_colors()
            self._update_stats()
            self.status_var.set("Canvas cleared.")

    def _change_palette(self, event=None):
        self.palette_name = self.palette_var.get()
        self.palette = PALETTES[self.palette_name]
        self._redraw()

    def _update_stats(self):
        self._stat_vars["stat_nodes"].set(str(len(self.graph.nodes)))
        self._stat_vars["stat_edges"].set(str(len(self.graph.edges)))

    # ── Presets ───────────────────────────────────────────────────────────────
    def _load_preset(self, name):
        self.graph.clear()
        self.update_idletasks()
        W = max(self.canvas.winfo_width(), 600)
        H = max(self.canvas.winfo_height(), 500)
        cx, cy = W // 2, H // 2

        if name == "Australia":
            positions = {
                "WA": (cx-240, cy),   "NT":  (cx-100, cy-80),
                "SA": (cx-80,  cy+40),"QLD": (cx+80,  cy-80),
                "NSW":(cx+120, cy+40),"VIC": (cx+100, cy+120),
                "TAS":(cx+110, cy+200),
            }
            adjacencies = [
                ("WA","NT"),("WA","SA"),("NT","SA"),("NT","QLD"),
                ("SA","QLD"),("SA","NSW"),("SA","VIC"),
                ("QLD","NSW"),("NSW","VIC"),
            ]
            ids = {}
            for label, (x, y) in positions.items():
                nid = self.graph.add_node(x, y, label)
                ids[label] = nid
            for a, b in adjacencies:
                self.graph.add_edge(ids[a], ids[b])

        elif name == "US Regions":
            regions = {
                "NW":(cx-260,cy-120),"NE":(cx+160,cy-120),
                "MW":(cx-60, cy-80), "SE":(cx+100,cy+80),
                "SW":(cx-200,cy+60), "S": (cx-30, cy+120),
            }
            adjacencies = [
                ("NW","MW"),("NW","SW"),("MW","NE"),("MW","SW"),
                ("MW","SE"),("MW","S"),("NE","SE"),("SW","S"),
                ("SE","S"),
            ]
            ids = {}
            for label, (x, y) in regions.items():
                nid = self.graph.add_node(x, y, label)
                ids[label] = nid
            for a, b in adjacencies:
                self.graph.add_edge(ids[a], ids[b])

        elif name == "Petersen Graph":
            outer_r, inner_r = 180, 80
            outer, inner = [], []
            for i in range(5):
                angle = math.radians(90 + i*72)
                outer.append(self.graph.add_node(
                    int(cx + outer_r*math.cos(angle)),
                    int(cy - outer_r*math.sin(angle)),
                    str(i)))
            for i in range(5):
                angle = math.radians(90 + i*72)
                inner.append(self.graph.add_node(
                    int(cx + inner_r*math.cos(angle)),
                    int(cy - inner_r*math.sin(angle)),
                    str(i+5)))
            for i in range(5):
                self.graph.add_edge(outer[i], outer[(i+1)%5])
                self.graph.add_edge(outer[i], inner[i])
                self.graph.add_edge(inner[i], inner[(i+2)%5])

        elif name == "Complete K5":
            nodes = []
            for i in range(5):
                angle = math.radians(90 + i*72)
                nid = self.graph.add_node(
                    int(cx + 160*math.cos(angle)),
                    int(cy - 160*math.sin(angle)), str(i))
                nodes.append(nid)
            for i in range(5):
                for j in range(i+1, 5):
                    self.graph.add_edge(nodes[i], nodes[j])

        elif name == "Cycle C7":
            nodes = []
            for i in range(7):
                angle = math.radians(90 + i*(360/7))
                nid = self.graph.add_node(
                    int(cx + 160*math.cos(angle)),
                    int(cy - 160*math.sin(angle)), str(i))
                nodes.append(nid)
            for i in range(7):
                self.graph.add_edge(nodes[i], nodes[(i+1)%7])

        elif name == "Random 12":
            nids = []
            random.seed(42)
            for i in range(12):
                x = random.randint(cx-250, cx+250)
                y = random.randint(cy-180, cy+180)
                nids.append(self.graph.add_node(x, y, str(i)))
            for i in range(12):
                for j in range(i+1, 12):
                    if random.random() < 0.25:
                        self.graph.add_edge(nids[i], nids[j])

        self._update_stats()
        self._reset_colors()
        self.status_var.set(f"Loaded preset: {name}")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MapColoringApp()
    app.mainloop()
