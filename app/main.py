"""
main.py - Aplicación de Escritorio: Registro de Matrícula
E.E.S N°3 - "Malvinas Argentinas"
"""

import sys
import os

# Agregar el directorio actual al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from tkinter import messagebox, filedialog

import database as db
import export_excel as ex
import import_excel as impex
from curso_view import CursoView
from stats_view import StatsView
from search_view import SearchView

# ── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MatriculaApp(ctk.CTk):
    """Ventana principal de la aplicación de matrícula."""

    SCHOOL_NAME = 'E.E.S N°3 — "Malvinas Argentinas"'

    def __init__(self):
        super().__init__()
        db.init_db()
        self._active_curso = None
        self._sidebar_buttons = {}
        self._current_view = None

        self.title(f"Registro de Matrícula  ·  {self.SCHOOL_NAME}")
        self.geometry("1280x780")
        self.minsize(1024, 640)

        self._build_ui()
        self._show_stats()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Barra lateral ──────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#111827", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo / Escudo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="#0F172A",
                                  corner_radius=0, height=120)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame, text="🏫",
            font=ctk.CTkFont(size=40)
        ).pack(pady=(18, 2))
        ctk.CTkLabel(
            logo_frame, text="E.E.S N°3",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color="#90CDF4"
        ).pack()
        ctk.CTkLabel(
            logo_frame, text="Malvinas Argentinas",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#718096"
        ).pack()

        # Botones de navegación global
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(12, 0))

        self._nav_btn(nav_frame, "📊  Estadísticas", "stats",
                      command=self._show_stats)
        self._nav_btn(nav_frame, "🔍  Búsqueda Global", "search",
                      command=self._show_search)

        # Exportar todos
        ctk.CTkButton(
            nav_frame, text="📤  Exportar Todo", height=36,
            fg_color="#276749", hover_color="#1C4532", corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12),
            command=self._export_all
        ).pack(fill="x", padx=10, pady=(4, 0))

        # Importar Excel
        ctk.CTkButton(
            nav_frame, text="📥  Importar Excel", height=36,
            fg_color="#2B6CB0", hover_color="#2C5282", corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12),
            command=self._import_excel
        ).pack(fill="x", padx=10, pady=(6, 0))

        # Separador cursos
        sep_frame = ctk.CTkFrame(self.sidebar, fg_color="#1E2535",
                                 corner_radius=0, height=32)
        sep_frame.pack(fill="x", pady=(14, 0))
        sep_frame.pack_propagate(False)
        ctk.CTkLabel(
            sep_frame, text="  CURSOS",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color="#4A5568"
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            sep_frame, text="＋", width=30, height=24,
            fg_color="transparent", hover_color="#2D3748",
            text_color="#90CDF4",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._add_curso_dialog
        ).pack(side="right", padx=6, pady=4)

        # Scrollable list de cursos
        self.cursos_scroll = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color="#2D3748",
            scrollbar_button_hover_color="#4A5568"
        )
        self.cursos_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._refresh_cursos_sidebar()

        # ── Main content ────────────────────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(self, fg_color="#151B2D", corner_radius=0)
        self.main_frame.pack(side="left", fill="both", expand=True)

    def _nav_btn(self, parent, text, key, command=None):
        btn = ctk.CTkButton(
            parent, text=text, height=38, anchor="w",
            fg_color="transparent", hover_color="#1E2535",
            corner_radius=6, font=ctk.CTkFont("Segoe UI", 13),
            text_color="#CBD5E0",
            command=lambda: self._nav_click(key, command)
        )
        btn.pack(fill="x", padx=8, pady=2)
        self._sidebar_buttons[key] = btn
        return btn

    def _nav_click(self, key, command=None):
        self._set_active_nav(key)
        if command:
            command()

    def _set_active_nav(self, key):
        for k, btn in self._sidebar_buttons.items():
            if k == key:
                btn.configure(fg_color="#1A3A5C", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#CBD5E0")

    def _refresh_cursos_sidebar(self):
        for w in self.cursos_scroll.winfo_children():
            w.destroy()
        self._sidebar_buttons = {
            k: v for k, v in self._sidebar_buttons.items()
            if k in ('stats', 'search')
        }

        cursos = db.get_all_cursos()
        current_anio = None
        for curso in cursos:
            anio = curso['anio']
            if anio != current_anio:
                current_anio = anio
                # Año header
                year_lbl = ctk.CTkFrame(self.cursos_scroll, fg_color="transparent")
                year_lbl.pack(fill="x", padx=8, pady=(8, 0))
                ctk.CTkLabel(
                    year_lbl,
                    text=f"{anio}° Año",
                    font=ctk.CTkFont("Segoe UI", 10, "bold"),
                    text_color="#718096"
                ).pack(side="left", padx=6)

            key = f"curso_{curso['id']}"
            curso_dict = dict(curso)

            def make_cmd(c=curso_dict, k=key):
                return lambda: self._show_curso(c, k)

            btn = ctk.CTkButton(
                self.cursos_scroll,
                text=f"   División {curso['division']}",
                height=32, anchor="w",
                fg_color="transparent", hover_color="#1E2535",
                corner_radius=6, font=ctk.CTkFont("Segoe UI", 12),
                text_color="#A0AEC0",
                command=make_cmd()
            )
            btn.pack(fill="x", padx=8, pady=1)
            self._sidebar_buttons[key] = btn

    # ── Navigation ────────────────────────────────────────────────────────────

    def _clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()
        self._current_view = None

    def _show_stats(self):
        self._clear_main()
        self._set_active_nav("stats")
        view = StatsView(self.main_frame)
        view.pack(fill="both", expand=True, padx=20, pady=16)
        self._current_view = view

    def _show_search(self):
        self._clear_main()
        self._set_active_nav("search")
        view = SearchView(self.main_frame, on_goto_curso=self._show_curso_by_obj)
        view.pack(fill="both", expand=True, padx=20, pady=16)
        self._current_view = view

    def _show_curso(self, curso_dict, nav_key=None):
        self._clear_main()
        if nav_key:
            self._set_active_nav(nav_key)
        else:
            key = f"curso_{curso_dict['id']}"
            self._set_active_nav(key)

        view = CursoView(self.main_frame, curso_dict)
        view.pack(fill="both", expand=True, padx=20, pady=16)
        self._current_view = view
        self._active_curso = curso_dict

    def _show_curso_by_obj(self, curso_dict):
        self._show_curso(curso_dict)

    # ── Cursos management ─────────────────────────────────────────────────────

    def _add_curso_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Agregar Curso")
        dlg.geometry("360x240")
        dlg.grab_set()
        dlg.lift()
        dlg.focus_force()

        ctk.CTkLabel(dlg, text="Agregar Nuevo Curso",
                     font=ctk.CTkFont("Segoe UI", 16, "bold")).pack(pady=20)

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="x", padx=30)

        ctk.CTkLabel(form, text="Año (1-6):").pack(anchor="w")
        anio_var = ctk.StringVar(value="1")
        ctk.CTkEntry(form, textvariable=anio_var, height=32).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="División (A, B, C...):").pack(anchor="w")
        div_var = ctk.StringVar(value="A")
        ctk.CTkEntry(form, textvariable=div_var, height=32).pack(fill="x")

        def save():
            try:
                anio = int(anio_var.get())
                div = div_var.get().strip().upper()
                if not (1 <= anio <= 6) or not div:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Año debe ser 1-6 y División no puede estar vacío.")
                return
            ok = db.add_curso(anio, div)
            if ok:
                self._refresh_cursos_sidebar()
                dlg.destroy()
            else:
                messagebox.showwarning("Advertencia", "Ese curso ya existe.")

        ctk.CTkButton(dlg, text="Agregar", command=save,
                      fg_color="#2E6DA4", height=36).pack(pady=18)

    def _export_all(self):
        filepath = filedialog.asksaveasfilename(
            title="Exportar toda la matrícula",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="Matricula_Completa.xlsx"
        )
        if filepath:
            try:
                saved = ex.export_all_cursos(filepath)
                messagebox.showinfo("Exportado", f"Archivo guardado:\n{saved}")
            except Exception as e:
                messagebox.showerror("Error al exportar", str(e))

    def _import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo Excel de Matrícula",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if not filepath:
            return

        # Previsualizar cursos detectados
        try:
            preview = impex.read_excel_file(filepath)
        except Exception as e:
            messagebox.showerror("Error al leer Excel", f"No se pudo leer el archivo:\n{e}")
            return

        if not preview["cursos"]:
            ign_str = ", ".join(preview["hojas_ignoradas"]) if preview["hojas_ignoradas"] else "Ninguna"
            messagebox.showwarning(
                "Sin cursos válidos",
                f"No se encontraron pestañas de cursos válidas (ej. 1°A, 2°B, etc.).\n\nHojas ignoradas: {ign_str}"
            )
            return

        hojas_cursos = [f"• {c['anio']}° {c['division']}: {len(c['alumnos'])} alumnos" for c in preview["cursos"]]
        hojas_ign = ", ".join(preview["hojas_ignoradas"]) if preview["hojas_ignoradas"] else "Ninguna"

        resumen_texto = (
            f"Se detectaron {preview['total_cursos']} cursos y {preview['total_alumnos']} alumnos.\n\n"
            f"Cursos a importar:\n" + "\n".join(hojas_cursos[:12]) +
            (f"\n... y {len(hojas_cursos) - 12} cursos más" if len(hojas_cursos) > 12 else "") +
            f"\n\nPestañas ignoradas (no son cursos):\n{hojas_ign}\n\n"
            f"¿Desea proceder con la importación?\n"
            f"(Los datos de estos cursos en el sistema serán actualizados)."
        )

        if not messagebox.askyesno("Confirmar Importación", resumen_texto):
            return

        # Ejecutar importación
        try:
            result = impex.import_excel_to_database(filepath, replace_existing=True)
            if result["success"]:
                messagebox.showinfo(
                    "Importación Exitosa",
                    f"✅ Se importaron {result['total_alumnos']} alumnos en {result['total_cursos']} cursos correctamente."
                )
                self._refresh_cursos_sidebar()
                if self._active_curso:
                    self._show_curso(self._active_curso)
                else:
                    self._show_stats()
            else:
                messagebox.showerror("Error en importación", result.get("message", "Error desconocido"))
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = MatriculaApp()
    app.mainloop()
