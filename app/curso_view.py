"""
curso_view.py - Vista principal de la tabla de alumnos por curso
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import database as db
import export_excel as ex
from alumno_form import AlumnoFormDialog


COL_KEYS = [
    ("nro_orden", "N°", 40),
    ("apellido_nombre", "Apellido y Nombre", 220),
    ("fecha_nac", "Fecha Nac.", 90),
    ("edad", "Edad", 40),
    ("sexo", "Sexo", 45),
    ("nro_doc", "N° Documento", 100),
    ("domicilio", "Domicilio", 180),
    ("telefono", "Teléfono", 100),
    ("nombre_tutor", "Tutor / Encargado", 180),
    ("observaciones", "Observaciones", 180),
]


class CursoView(ctk.CTkFrame):
    """Panel que muestra la lista de alumnos de un curso específico."""

    def __init__(self, parent, curso, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.curso = dict(curso)
        self.curso_id = curso['id']
        self._build_ui()
        self._load_data()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="#1A3A5C", corner_radius=10, height=56)
        hdr.pack(fill="x", padx=0, pady=(0, 10))
        hdr.pack_propagate(False)

        title_txt = f"  {self.curso['anio']}° Año  —  División {self.curso['division']}"
        ctk.CTkLabel(
            hdr, text=title_txt,
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(side="left", padx=16, pady=12)

        self.count_label = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color="#90CDF4"
        )
        self.count_label.pack(side="left", padx=8)

        # ── Toolbar ────────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=0, pady=(0, 8))

        ctk.CTkButton(
            toolbar, text="➕  Nuevo Alumno", width=160, height=36,
            fg_color="#2E6DA4", hover_color="#1A3A5C", corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._new_alumno
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            toolbar, text="✏️  Editar", width=110, height=36,
            fg_color="#2D3748", hover_color="#4A5568", corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._edit_alumno
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            toolbar, text="🗑️  Eliminar", width=110, height=36,
            fg_color="#742A2A", hover_color="#9B2C2C", corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._delete_alumno
        ).pack(side="left", padx=(0, 8))

        # Separador
        ctk.CTkLabel(toolbar, text="│", text_color="#4A5568",
                     font=ctk.CTkFont(size=22)).pack(side="left", padx=8)

        ctk.CTkButton(
            toolbar, text="📥  Exportar este curso", width=180, height=36,
            fg_color="#276749", hover_color="#1C4532", corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._export_curso
        ).pack(side="left", padx=(0, 8))

        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_frame.pack(side="right")
        ctk.CTkLabel(search_frame, text="🔍",
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(
            search_frame, textvariable=self.search_var,
            placeholder_text="Buscar en este curso...",
            width=220, height=36, corner_radius=8
        ).pack(side="left")

        # ── Table ──────────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color="#1E2535", corner_radius=10)
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background="#1E2535",
                        foreground="#E2E8F0",
                        rowheight=28,
                        fieldbackground="#1E2535",
                        font=("Segoe UI", 10))
        style.configure("Custom.Treeview.Heading",
                        background="#2D3748",
                        foreground="#90CDF4",
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        style.map("Custom.Treeview",
                  background=[("selected", "#2E6DA4")],
                  foreground=[("selected", "white")])
        style.map("Custom.Treeview.Heading",
                  background=[("active", "#2E6DA4")])

        columns = [k for k, *_ in COL_KEYS]
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Custom.Treeview", selectmode="browse"
        )
        for key, label, width in COL_KEYS:
            self.tree.heading(key, text=label, anchor="w")
            self.tree.column(key, width=width, minwidth=30, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

        # Doble clic para editar
        self.tree.bind("<Double-1>", lambda e: self._edit_alumno())

        # Guardar referencia a alumnos raw
        self._alumnos = []
        self._filtered = []

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_data(self):
        self._alumnos = [dict(a) for a in db.get_alumnos_by_curso(self.curso_id)]
        self._apply_filter()

    def _apply_filter(self):
        q = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        if q:
            self._filtered = [
                a for a in self._alumnos
                if q in (a.get('apellido_nombre') or '').lower()
                or q in (a.get('nro_doc') or '').lower()
                or q in (a.get('nro_matricula') or '').lower()
            ]
        else:
            self._filtered = list(self._alumnos)
        self._render_table()

    def _render_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, alumno in enumerate(self._filtered):
            row = tuple(str(alumno.get(k) or '') for k, *_ in COL_KEYS)
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(alumno['id']), values=row, tags=(tag,))

        self.tree.tag_configure("odd", background="#252D3D")
        self.tree.tag_configure("even", background="#1E2535")
        count = len(self._filtered)
        total = len(self._alumnos)
        if hasattr(self, 'count_label'):
            txt = f"({count} alumno{'s' if count != 1 else ''})" if not self.search_var.get() \
                else f"({count} de {total})"
            self.count_label.configure(text=txt)

    def _on_search(self, *_):
        self._apply_filter()

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _selected_data(self):
        aid = self._selected_id()
        if aid is None:
            return None
        row = db.get_alumno_by_id(aid)
        return dict(row) if row else None

    # ── Actions ───────────────────────────────────────────────────────────────

    def _new_alumno(self):
        AlumnoFormDialog(
            self, self.curso_id,
            on_save=self._load_data
        )

    def _edit_alumno(self):
        data = self._selected_data()
        if not data:
            messagebox.showwarning("Sin selección", "Seleccioná un alumno para editar.")
            return
        AlumnoFormDialog(
            self, self.curso_id,
            alumno_data=data,
            on_save=self._load_data
        )

    def _delete_alumno(self):
        data = self._selected_data()
        if not data:
            messagebox.showwarning("Sin selección", "Seleccioná un alumno para eliminar.")
            return
        nombre = data.get('apellido_nombre', 'este alumno')
        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminás a '{nombre}'?\n\nEsta acción no se puede deshacer.",
            icon="warning"
        ):
            db.delete_alumno(data['id'])
            self._load_data()

    def _export_curso(self):
        filepath = filedialog.asksaveasfilename(
            title="Exportar curso a Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"Matricula_{self.curso['anio']}{self.curso['division']}.xlsx"
        )
        if filepath:
            try:
                saved = ex.export_single_curso(self.curso_id, filepath)
                messagebox.showinfo("Exportado", f"Archivo guardado:\n{saved}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
