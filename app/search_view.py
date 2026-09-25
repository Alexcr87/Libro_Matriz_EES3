"""
search_view.py - Vista de búsqueda global de alumnos
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db
from alumno_form import AlumnoFormDialog


class SearchView(ctk.CTkFrame):
    """Panel de búsqueda global de alumnos en todos los cursos."""

    def __init__(self, parent, on_goto_curso=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_goto_curso = on_goto_curso
        self._results = []
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="#1A3A5C", corner_radius=10, height=56)
        hdr.pack(fill="x", pady=(0, 16))
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="  🔍  Búsqueda Global",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(side="left", padx=16, pady=12)

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="#1E2535", corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 12), ipadx=12, ipady=12)

        inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        self.search_var = ctk.StringVar()
        entry = ctk.CTkEntry(
            inner, textvariable=self.search_var,
            placeholder_text="Buscá por nombre, apellido, DNI o N° matrícula...",
            height=42, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13)
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry.bind("<Return>", self._search)

        ctk.CTkButton(
            inner, text="🔍  Buscar", width=130, height=42,
            fg_color="#2E6DA4", hover_color="#1A3A5C",
            corner_radius=8, font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._search
        ).pack(side="left")

        ctk.CTkButton(
            inner, text="✖ Limpiar", width=100, height=42,
            fg_color="#4A5568", hover_color="#2D3748",
            corner_radius=8, font=ctk.CTkFont("Segoe UI", 13),
            command=self._clear
        ).pack(side="left", padx=(6, 0))

        self.result_label = ctk.CTkLabel(
            self, text="Ingresá un término para buscar.",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color="#718096"
        )
        self.result_label.pack(anchor="w", padx=4, pady=(0, 6))

        # Table
        table_outer = ctk.CTkFrame(self, fg_color="#1E2535", corner_radius=10)
        table_outer.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Search.Treeview",
                        background="#1E2535", foreground="#E2E8F0",
                        rowheight=28, fieldbackground="#1E2535",
                        font=("Segoe UI", 10))
        style.configure("Search.Treeview.Heading",
                        background="#2D3748", foreground="#90CDF4",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Search.Treeview", background=[("selected", "#2E6DA4")])

        columns = ["curso", "apellido_nombre", "nro_doc", "fecha_nac",
                   "domicilio", "telefono", "nombre_tutor"]
        headers = ["Curso", "Apellido y Nombre", "N° Documento",
                   "Fecha Nac.", "Domicilio", "Teléfono", "Tutor"]
        widths = [80, 220, 110, 90, 190, 110, 180]

        self.tree = ttk.Treeview(
            table_outer, columns=columns, show="headings",
            style="Search.Treeview", selectmode="browse"
        )
        for col, head, w in zip(columns, headers, widths):
            self.tree.heading(col, text=head, anchor="w")
            self.tree.column(col, width=w, anchor="w", minwidth=40)

        vsb = ttk.Scrollbar(table_outer, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_outer, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree.bind("<Double-1>", self._edit_selected)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=8)
        ctk.CTkButton(
            btn_frame, text="✏️  Editar seleccionado", width=190, height=36,
            fg_color="#2D3748", hover_color="#4A5568", corner_radius=8,
            command=self._edit_selected
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="📌  Ir al curso", width=150, height=36,
            fg_color="#276749", hover_color="#1C4532", corner_radius=8,
            command=self._goto_curso
        ).pack(side="left", padx=(8, 0))

    def _search(self, *_):
        q = self.search_var.get().strip()
        if not q:
            self._clear()
            return
        self._results = [dict(r) for r in db.search_alumnos(q)]
        self._render()

    def _clear(self):
        self.search_var.set("")
        self._results = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.result_label.configure(text="Ingresá un término para buscar.")

    def _render(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, a in enumerate(self._results):
            curso = f"{a.get('anio', '')}° {a.get('division', '')}"
            row = (
                curso,
                a.get('apellido_nombre', ''),
                a.get('nro_doc', ''),
                a.get('fecha_nac', ''),
                a.get('domicilio', ''),
                a.get('telefono', ''),
                a.get('nombre_tutor', '')
            )
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(a['id']), values=row, tags=(tag,))
        self.tree.tag_configure("odd", background="#252D3D")
        self.tree.tag_configure("even", background="#1E2535")
        n = len(self._results)
        self.result_label.configure(
            text=f"Se encontraron {n} resultado{'s' if n != 1 else ''}.",
            text_color="#68D391" if n > 0 else "#FC8181"
        )

    def _selected_data(self):
        sel = self.tree.selection()
        if not sel:
            return None
        aid = int(sel[0])
        row = db.get_alumno_by_id(aid)
        return dict(row) if row else None

    def _edit_selected(self, *_):
        data = self._selected_data()
        if not data:
            messagebox.showwarning("Sin selección", "Seleccioná un alumno.")
            return
        AlumnoFormDialog(
            self, data['curso_id'],
            alumno_data=data,
            on_save=self._search
        )

    def _goto_curso(self):
        data = self._selected_data()
        if not data:
            messagebox.showwarning("Sin selección", "Seleccioná un alumno.")
            return
        if self.on_goto_curso:
            conn = db.get_connection()
            curso = conn.execute(
                "SELECT * FROM cursos WHERE id=?", (data['curso_id'],)
            ).fetchone()
            conn.close()
            if curso:
                self.on_goto_curso(dict(curso))
