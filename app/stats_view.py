"""
stats_view.py - Panel de estadísticas y resumen de matrícula
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import database as db


class StatsView(ctk.CTkFrame):
    """Panel de estadísticas de matrícula."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="#1A3A5C", corner_radius=10, height=56)
        hdr.pack(fill="x", pady=(0, 16))
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="  📊  Estadísticas de Matrícula",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            hdr, text="🔄 Actualizar", width=120, height=34,
            fg_color="#2E6DA4", hover_color="#1a3a5c", corner_radius=8,
            command=self.refresh
        ).pack(side="right", padx=16)

        # Cards row
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(0, 20))

        # Table por curso
        table_lbl = ctk.CTkFrame(self, fg_color="#2D3748", corner_radius=8, height=36)
        table_lbl.pack(fill="x", pady=(0, 6))
        table_lbl.pack_propagate(False)
        ctk.CTkLabel(
            table_lbl, text="  Detalle por Curso y División",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color="#90CDF4"
        ).pack(side="left", padx=12, pady=8)

        table_outer = ctk.CTkFrame(self, fg_color="#1E2535", corner_radius=10)
        table_outer.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Stats.Treeview",
                        background="#1E2535", foreground="#E2E8F0",
                        rowheight=26, fieldbackground="#1E2535",
                        font=("Segoe UI", 10))
        style.configure("Stats.Treeview.Heading",
                        background="#2D3748", foreground="#90CDF4",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Stats.Treeview", background=[("selected", "#2E6DA4")])

        self.tree = ttk.Treeview(
            table_outer,
            columns=("curso", "division", "cantidad", "pct"),
            show="headings",
            style="Stats.Treeview"
        )
        self.tree.heading("curso", text="Año", anchor="center")
        self.tree.heading("division", text="División", anchor="center")
        self.tree.heading("cantidad", text="Alumnos", anchor="center")
        self.tree.heading("pct", text="% del total", anchor="center")
        self.tree.column("curso", width=100, anchor="center")
        self.tree.column("division", width=100, anchor="center")
        self.tree.column("cantidad", width=100, anchor="center")
        self.tree.column("pct", width=120, anchor="center")

        vsb = ttk.Scrollbar(table_outer, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", pady=4)
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

    def _stat_card(self, parent, icon, label, value, color):
        card = ctk.CTkFrame(parent, fg_color="#1E2535", corner_radius=12, height=100)
        card.pack(side="left", fill="x", expand=True, padx=6)
        card.pack_propagate(False)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(14, 2))

        ctk.CTkLabel(top, text=icon,
                     font=ctk.CTkFont(size=26)).pack(side="left")

        val_lbl = ctk.CTkLabel(
            card, text=str(value),
            font=ctk.CTkFont("Segoe UI", 32, "bold"),
            text_color=color
        )
        val_lbl.pack(anchor="w", padx=18)

        ctk.CTkLabel(
            card, text=label,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color="#A0AEC0"
        ).pack(anchor="w", padx=18)

    def _bar(self, parent, label, value, max_value, color, idx):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=3)

        ctk.CTkLabel(row, text=label, width=80,
                     font=ctk.CTkFont("Segoe UI", 11),
                     anchor="w").pack(side="left")

        bar_bg = ctk.CTkFrame(row, fg_color="#2D3748", height=18, corner_radius=4)
        bar_bg.pack(side="left", fill="x", expand=True, padx=6)
        bar_bg.pack_propagate(False)

        pct = value / max_value if max_value else 0
        if pct > 0:
            bar_fill = ctk.CTkFrame(bar_bg, fg_color=color, height=18, corner_radius=4)
            bar_fill.place(relx=0, rely=0, relwidth=pct, relheight=1)

        ctk.CTkLabel(row, text=str(value), width=40,
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=color).pack(side="right")

    def refresh(self):
        stats = db.get_stats()

        # Clear cards
        for w in self.cards_frame.winfo_children():
            w.destroy()

        total = stats['total_alumnos']
        n_cursos = stats['total_cursos']

        # Sexo breakdown
        sexo_dict = {r['sexo']: r['cantidad'] for r in stats['por_sexo']}
        masc = sexo_dict.get('M', 0)
        fem = sexo_dict.get('F', 0)

        self._stat_card(self.cards_frame, "🎓", "Total Alumnos", total, "#68D391")
        self._stat_card(self.cards_frame, "📚", "Cursos Activos", n_cursos, "#63B3ED")
        self._stat_card(self.cards_frame, "👦", "Varones", masc, "#76E4F7")
        self._stat_card(self.cards_frame, "👧", "Mujeres", fem, "#F687B3")

        # Table
        for item in self.tree.get_children():
            self.tree.delete(item)

        COLORS = ["#68D391", "#63B3ED", "#F6AD55", "#FC8181",
                  "#9F7AEA", "#76E4F7", "#F687B3"]
        for i, row in enumerate(stats['por_curso']):
            pct = f"{row['cantidad'] / total * 100:.1f}%" if total else "0%"
            tag = f"c{i}"
            self.tree.insert(
                "", "end",
                values=(f"{row['anio']}° Año", row['division'], row['cantidad'], pct),
                tags=(tag,)
            )
            bg = "#252D3D" if i % 2 == 0 else "#1E2535"
            self.tree.tag_configure(tag, background=bg)
