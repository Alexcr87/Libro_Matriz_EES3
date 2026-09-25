# 📋 Registro de Matrícula — E.E.S N°3 "Malvinas Argentinas"

Aplicación de escritorio para gestionar el registro de matrícula escolar.

## ▶️ Cómo iniciar

**Opción 1 — Doble clic:**
Ejecutar `Iniciar_Matricula.bat`

**Opción 2 — Terminal:**
```
cd app
python main.py
```

## 📦 Requisitos

- Python 3.9+
- Instalar dependencias (una sola vez):
```
python -m pip install customtkinter openpyxl pillow
```

## ✨ Funcionalidades

| Feature | Descripción |
|---|---|
| 📚 Cursos por año/división | 18 cursos: 1° a 6°, divisiones A/B/C |
| ➕ Alta de alumnos | Formulario completo con todos los campos del registro oficial |
| ✏️ Editar alumnos | Doble clic o botón "Editar" |
| 🗑️ Eliminar | Con confirmación |
| 🔍 Búsqueda global | Por nombre, apellido, DNI o N° de matrícula |
| 📊 Estadísticas | Total alumnos, por sexo, por curso |
| 📥 Exportar a Excel | Por curso individual o toda la matrícula |
| 📥 Importar desde Excel | Carga masiva omitiendo pestañas que no son cursos |
| ➕ Agregar cursos | Podés agregar más divisiones |

## 📁 Archivos generados

- `app/matricula.db` — Base de datos SQLite (no borrar)
- Exportaciones Excel — donde elijas guardarlas

## 📐 Campos por alumno

- N° de Orden, N° de Matrícula, Fecha de Inscripción
- Apellido y Nombre, Fecha de Nacimiento, Edad, Sexo
- Nacionalidad, Tipo y N° de Documento
- Domicilio, Teléfono
- Nombre del Tutor/Encargado, Nacionalidad, Profesión
- Egresos, Pases, Ingresos
- Observaciones
