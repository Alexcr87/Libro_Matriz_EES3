"""
database.py - Gestión de la base de datos SQLite para el sistema de matrícula
E.E.S N°3 - "Malvinas Argentinas"
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matricula.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos creando las tablas si no existen."""
    conn = get_connection()
    c = conn.cursor()

    # Tabla de cursos
    c.execute("""
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anio INTEGER NOT NULL,
            division TEXT NOT NULL,
            ciclo_lectivo INTEGER NOT NULL DEFAULT 2024,
            UNIQUE(anio, division, ciclo_lectivo)
        )
    """)

    # Tabla de alumnos
    c.execute("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curso_id INTEGER NOT NULL,
            nro_orden INTEGER,
            fecha_inscripcion TEXT,
            nro_matricula TEXT,
            apellido_nombre TEXT NOT NULL,
            fecha_nac TEXT,
            edad INTEGER,
            sexo TEXT,
            nacionalidad TEXT,
            tipo_doc TEXT,
            nro_doc TEXT,
            nombre_tutor TEXT,
            nacionalidad_tutor TEXT,
            profesion_tutor TEXT,
            domicilio TEXT,
            telefono TEXT,
            egreso TEXT,
            pase TEXT,
            salida_despues_30_4 TEXT,
            ingresa TEXT,
            ingr_despues_30_4 TEXT,
            observaciones TEXT,
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )
    """)

    # Insertar cursos por defecto si no existen
    cursos_default = [
        (1, 'A'), (1, 'B'), (1, 'C'),
        (2, 'A'), (2, 'B'), (2, 'C'),
        (3, 'A'), (3, 'B'), (3, 'C'),
        (4, 'A'), (4, 'B'), (4, 'C'),
        (5, 'A'), (5, 'B'), (5, 'C'),
        (6, 'A'), (6, 'B'), (6, 'C'),
    ]
    ciclo = datetime.now().year
    for anio, div in cursos_default:
        c.execute("""
            INSERT OR IGNORE INTO cursos (anio, division, ciclo_lectivo)
            VALUES (?, ?, ?)
        """, (anio, div, ciclo))

    conn.commit()
    conn.close()


# ─── CURSOS ───────────────────────────────────────────────────────────────────

def get_all_cursos():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cursos ORDER BY anio, division").fetchall()
    conn.close()
    return rows


def get_curso_by_anio_div(anio, division):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM cursos WHERE anio=? AND division=?", (anio, division)
    ).fetchone()
    conn.close()
    return row


def add_curso(anio, division, ciclo_lectivo=None):
    ciclo = ciclo_lectivo or datetime.now().year
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO cursos (anio, division, ciclo_lectivo) VALUES (?, ?, ?)",
            (anio, division, ciclo)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_curso(curso_id):
    conn = get_connection()
    conn.execute("DELETE FROM alumnos WHERE curso_id=?", (curso_id,))
    conn.execute("DELETE FROM cursos WHERE id=?", (curso_id,))
    conn.commit()
    conn.close()


# ─── ALUMNOS ──────────────────────────────────────────────────────────────────

def get_alumnos_by_curso(curso_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alumnos WHERE curso_id=? ORDER BY nro_orden, apellido_nombre",
        (curso_id,)
    ).fetchall()
    conn.close()
    return rows


def search_alumnos(query):
    conn = get_connection()
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT a.*, c.anio, c.division FROM alumnos a
        JOIN cursos c ON a.curso_id = c.id
        WHERE a.apellido_nombre LIKE ?
           OR a.nro_doc LIKE ?
           OR a.nro_matricula LIKE ?
        ORDER BY c.anio, c.division, a.apellido_nombre
    """, (q, q, q)).fetchall()
    conn.close()
    return rows


def add_alumno(data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO alumnos (
            curso_id, nro_orden, fecha_inscripcion, nro_matricula,
            apellido_nombre, fecha_nac, edad, sexo, nacionalidad,
            tipo_doc, nro_doc, nombre_tutor, nacionalidad_tutor,
            profesion_tutor, domicilio, telefono, egreso, pase,
            salida_despues_30_4, ingresa, ingr_despues_30_4, observaciones
        ) VALUES (
            :curso_id, :nro_orden, :fecha_inscripcion, :nro_matricula,
            :apellido_nombre, :fecha_nac, :edad, :sexo, :nacionalidad,
            :tipo_doc, :nro_doc, :nombre_tutor, :nacionalidad_tutor,
            :profesion_tutor, :domicilio, :telefono, :egreso, :pase,
            :salida_despues_30_4, :ingresa, :ingr_despues_30_4, :observaciones
        )
    """, data)
    alumno_id = c.lastrowid
    conn.commit()
    conn.close()
    return alumno_id


def update_alumno(alumno_id, data: dict):
    data['id'] = alumno_id
    conn = get_connection()
    conn.execute("""
        UPDATE alumnos SET
            curso_id=:curso_id, nro_orden=:nro_orden,
            fecha_inscripcion=:fecha_inscripcion, nro_matricula=:nro_matricula,
            apellido_nombre=:apellido_nombre, fecha_nac=:fecha_nac,
            edad=:edad, sexo=:sexo, nacionalidad=:nacionalidad,
            tipo_doc=:tipo_doc, nro_doc=:nro_doc, nombre_tutor=:nombre_tutor,
            nacionalidad_tutor=:nacionalidad_tutor, profesion_tutor=:profesion_tutor,
            domicilio=:domicilio, telefono=:telefono, egreso=:egreso, pase=:pase,
            salida_despues_30_4=:salida_despues_30_4, ingresa=:ingresa,
            ingr_despues_30_4=:ingr_despues_30_4, observaciones=:observaciones
        WHERE id=:id
    """, data)
    conn.commit()
    conn.close()


def delete_alumno(alumno_id):
    conn = get_connection()
    conn.execute("DELETE FROM alumnos WHERE id=?", (alumno_id,))
    conn.commit()
    conn.close()


def get_alumno_by_id(alumno_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM alumnos WHERE id=?", (alumno_id,)).fetchone()
    conn.close()
    return row


# ─── ESTADÍSTICAS ─────────────────────────────────────────────────────────────

def get_stats():
    conn = get_connection()
    stats = {}

    stats['total_alumnos'] = conn.execute("SELECT COUNT(*) FROM alumnos").fetchone()[0]
    stats['total_cursos'] = conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]

    stats['por_anio'] = conn.execute("""
        SELECT c.anio, COUNT(a.id) as cantidad
        FROM cursos c
        LEFT JOIN alumnos a ON a.curso_id = c.id
        GROUP BY c.anio
        ORDER BY c.anio
    """).fetchall()

    stats['por_curso'] = conn.execute("""
        SELECT c.anio, c.division, COUNT(a.id) as cantidad
        FROM cursos c
        LEFT JOIN alumnos a ON a.curso_id = c.id
        GROUP BY c.id
        ORDER BY c.anio, c.division
    """).fetchall()

    stats['por_sexo'] = conn.execute("""
        SELECT sexo, COUNT(*) as cantidad FROM alumnos
        WHERE sexo IS NOT NULL AND sexo != ''
        GROUP BY sexo
    """).fetchall()

    conn.close()
    return stats
