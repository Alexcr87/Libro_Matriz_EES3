"""
alumno_form.py - Formulario modal para agregar/editar alumnos
"""

import customtkinter as ctk
from datetime import datetime
import database as db


SEXO_OPTS = ["", "M", "F", "Otro"]
TIPO_DOC_OPTS = ["", "DNI", "LC", "LE", "Pasaporte", "Otro"]
NAC_OPTS = ["", "Argentina", "Boliviana", "Brasileña", "Chilena", "Colombiana",
            "Ecuatoriana", "Paraguaya", "Peruana", "Uruguaya", "Venezolana", "Otra"]


class AlumnoFormDialog(ctk.CTkToplevel):
    """Diálogo modal para crear o editar un alumno."""

    def __init__(self, parent, curso_id, alumno_data=None, on_save=None):
        super().__init__(parent)
        self.curso_id = curso_id
        self.alumno_data = alumno_data  # None = nuevo, dict = editar
        self.on_save = on_save
        self.result = None

        title = "Editar Alumno" if alumno_data else "Nuevo Alumno"
        self.title(title)
        self.geometry("820x680")
        self.resizable(True, True)
        self.grab_set()  # Modal
        self.lift()
        self.focus_force()

        self._build_ui()
        if alumno_data:
            self._populate(alumno_data)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#1A3A5C", corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        icon = "✏️" if self.alumno_data else "➕"
        ctk.CTkLabel(
            header,
            text=f"  {icon}  {'Editar Alumno' if self.alumno_data else 'Nuevo Alumno'}",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=12)

        # Scrollable form
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.fields = {}
        self._section("📋 Datos de Inscripción")
        row1 = self._row(self.scroll)
        self.fields['nro_orden'] = self._field(row1, "N° de Orden", width=100)
        self.fields['nro_matricula'] = self._field(row1, "N° Matrícula", width=160)
        self.fields['fecha_inscripcion'] = self._field(row1, "Fecha Inscripción", width=130, placeholder="dd/mm/aaaa")

        self._section("👤 Datos del Alumno")
        row2 = self._row(self.scroll)
        self.fields['apellido_nombre'] = self._field(row2, "Apellido y Nombre *", width=320)
        self.fields['fecha_nac'] = self._field(row2, "Fecha Nac.", width=120, placeholder="dd/mm/aaaa")
        self.fields['edad'] = self._field(row2, "Edad", width=60)

        row3 = self._row(self.scroll)
        self.fields['sexo'] = self._combo(row3, "Sexo", SEXO_OPTS, width=100)
        self.fields['nacionalidad'] = self._combo(row3, "Nacionalidad", NAC_OPTS, width=160)
        self.fields['tipo_doc'] = self._combo(row3, "Tipo Doc.", TIPO_DOC_OPTS, width=120)
        self.fields['nro_doc'] = self._field(row3, "N° Documento", width=160)

        row4 = self._row(self.scroll)
        self.fields['domicilio'] = self._field(row4, "Domicilio", width=360)
        self.fields['telefono'] = self._field(row4, "Teléfono", width=160)

        self._section("👪 Datos del Tutor / Encargado")
        row5 = self._row(self.scroll)
        self.fields['nombre_tutor'] = self._field(row5, "Nombre Tutor/Encargado", width=320)
        self.fields['nacionalidad_tutor'] = self._combo(row5, "Nacionalidad Tutor", NAC_OPTS, width=160)

        row6 = self._row(self.scroll)
        self.fields['profesion_tutor'] = self._field(row6, "Profesión Tutor", width=260)

        self._section("🔄 Movimientos")
        row7 = self._row(self.scroll)
        self.fields['egreso'] = self._field(row7, "Egresó", width=130, placeholder="dd/mm/aaaa")
        self.fields['pase'] = self._field(row7, "Pase", width=130)
        self.fields['salida_despues_30_4'] = self._field(row7, "Salida > 30/4", width=130, placeholder="dd/mm/aaaa")

        row8 = self._row(self.scroll)
        self.fields['ingresa'] = self._field(row8, "Ingresa", width=130)
        self.fields['ingr_despues_30_4'] = self._field(row8, "Ingreso > 30/4", width=130, placeholder="dd/mm/aaaa")

        self._section("📝 Observaciones")
        obs_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        obs_frame.pack(fill="x", pady=(4, 8))
        self.fields['observaciones'] = ctk.CTkTextbox(obs_frame, height=70, corner_radius=8)
        self.fields['observaciones'].pack(fill="x", padx=4)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=130,
            fg_color="#4A5568", hover_color="#2D3748",
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="💾  Guardar", width=160,
            fg_color="#2E6DA4", hover_color="#1A3A5C",
            command=self._save
        ).pack(side="right")

    def _section(self, title):
        frame = ctk.CTkFrame(self.scroll, fg_color="#1A3A5C", corner_radius=6, height=28)
        frame.pack(fill="x", pady=(12, 4))
        frame.pack_propagate(False)
        ctk.CTkLabel(
            frame, text=f"  {title}",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="white"
        ).pack(side="left", padx=10, pady=4)

    def _row(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=4)
        return f

    def _field(self, parent, label, width=200, placeholder=""):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(side="left", padx=(0, 12), anchor="w")
        ctk.CTkLabel(wrapper, text=label,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color="#A0AEC0").pack(anchor="w")
        entry = ctk.CTkEntry(wrapper, width=width, height=32,
                             placeholder_text=placeholder,
                             corner_radius=6)
        entry.pack()
        return entry

    def _combo(self, parent, label, options, width=140):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(side="left", padx=(0, 12), anchor="w")
        ctk.CTkLabel(wrapper, text=label,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color="#A0AEC0").pack(anchor="w")
        combo = ctk.CTkOptionMenu(wrapper, values=options, width=width, height=32,
                                  corner_radius=6,
                                  fg_color="#2D3748", button_color="#2E6DA4",
                                  button_hover_color="#1A3A5C")
        combo.pack()
        return combo

    # ── Data ──────────────────────────────────────────────────────────────────

    def _populate(self, data):
        """Rellena el formulario con datos existentes."""
        def set_entry(key, val):
            widget = self.fields.get(key)
            if widget is None:
                return
            val = str(val) if val is not None else ""
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
                widget.insert(0, val)
            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.set(val)
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
                widget.insert("1.0", val)

        for key in self.fields:
            set_entry(key, data.get(key, ""))

    def _collect(self):
        """Recolecta los datos del formulario."""
        data = {}
        for key, widget in self.fields.items():
            if isinstance(widget, ctk.CTkEntry):
                data[key] = widget.get().strip() or None
            elif isinstance(widget, ctk.CTkOptionMenu):
                val = widget.get().strip()
                data[key] = val if val else None
            elif isinstance(widget, ctk.CTkTextbox):
                val = widget.get("1.0", "end").strip()
                data[key] = val if val else None

        # Convertir tipos
        try:
            data['nro_orden'] = int(data['nro_orden']) if data.get('nro_orden') else None
            data['edad'] = int(data['edad']) if data.get('edad') else None
        except (ValueError, TypeError):
            pass

        data['curso_id'] = self.curso_id
        return data

    def _save(self):
        data = self._collect()
        if not data.get('apellido_nombre'):
            self._show_error("El campo 'Apellido y Nombre' es obligatorio.")
            return

        try:
            if self.alumno_data and self.alumno_data.get('id'):
                db.update_alumno(self.alumno_data['id'], data)
            else:
                db.add_alumno(data)

            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            self._show_error(f"Error al guardar:\n{e}")

    def _show_error(self, msg):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Error")
        dlg.geometry("360x160")
        dlg.grab_set()
        dlg.lift()
        ctk.CTkLabel(dlg, text="⚠️ " + msg,
                     font=ctk.CTkFont("Segoe UI", 12),
                     wraplength=320).pack(expand=True, pady=20)
        ctk.CTkButton(dlg, text="Aceptar", command=dlg.destroy,
                      fg_color="#2E6DA4").pack(pady=(0, 16))
