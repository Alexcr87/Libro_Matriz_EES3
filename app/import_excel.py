"""
import_excel.py - Módulo para importar registros de matrícula desde archivos Excel.
E.E.S N°3 - "Malvinas Argentinas"
"""

import re
import unicodedata
from datetime import datetime, date
import openpyxl
import database as db


def normalize_text(text):
    """Normaliza texto para comparaciones sin acentos ni mayúsculas."""
    if not text:
        return ""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", text)


def clean_val(v):
    """Limpia y convierte valores de celdas a string limpio o None."""
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%d/%m/%Y")
    s = str(v).strip()
    if s.lower() == "none":
        return ""
    return s


def clean_doc(v):
    """Extrae tipo_doc y nro_doc a partir del valor de la celda de documento."""
    if v is None:
        return "", ""
    s = str(v).strip()
    if not s or s.lower() == "none":
        return "", ""
    
    # Manejar formatos como "DNI 51.167.338" o "LC 12345" o solo números "51167338"
    m = re.match(r"^(DNI|LC|LE|PAS|CI|DU)?\s*[\.:]?\s*([0-9\.\s\-]+)$", s, re.IGNORECASE)
    if m:
        tipo = m.group(1).upper() if m.group(1) else "DNI"
        num = re.sub(r"[\.\s\-]", "", m.group(2))
        return tipo, num
    return "DNI", s


def clean_int(v):
    """Convierte valor a entero seguro o None."""
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(v)
        s = str(v).strip()
        if s.isdigit():
            return int(s)
    except Exception:
        pass
    return None


def parse_header_map(ws):
    """
    Detecta automáticamente la fila de encabezados (entre filas 4 y 8)
    y mapea dinámicamente cada columna a su campo correspondiente.
    """
    header_row = None
    for r in range(4, 9):
        row_vals = [normalize_text(ws.cell(r, c).value) for c in range(1, 28)]
        if any("apellido" in v for v in row_vals) or any("alumno" in v for v in row_vals):
            header_row = r
            break
    
    if not header_row:
        # Fallback a fila 6
        header_row = 6

    col_map = {}
    found_tutor = False

    for c in range(1, 28):
        v = normalize_text(ws.cell(header_row, c).value)
        if not v:
            continue

        if "ord" in v and "nro_orden" not in col_map:
            col_map["nro_orden"] = c
        elif "inscr" in v and "fecha_inscripcion" not in col_map:
            col_map["fecha_inscripcion"] = c
        elif ("matric" in v or "folio" in v or "lm" in v) and "nro_matricula" not in col_map:
            col_map["nro_matricula"] = c
        elif ("apellido" in v or "alumno" in v) and "apellido_nombre" not in col_map:
            col_map["apellido_nombre"] = c
        elif ("nac" in v and "fecha" in v) or "f. nac" in v or "f.nac" in v or v == "fecha nac.":
            col_map["fecha_nac"] = c
        elif "edad" in v and "edad" not in col_map:
            col_map["edad"] = c
        elif "sexo" in v and "sexo" not in col_map:
            col_map["sexo"] = c
        elif ("doc" in v or "dni" in v) and "doc" not in col_map:
            col_map["doc"] = c
        elif ("padre" in v or "tutor" in v or "encargado" in v) and "nombre_tutor" not in col_map:
            col_map["nombre_tutor"] = c
            found_tutor = True
        elif "nacionalidad" in v or "nac" in v:
            if found_tutor and "nacionalidad_tutor" not in col_map:
                col_map["nacionalidad_tutor"] = c
            elif "nacionalidad" not in col_map:
                col_map["nacionalidad"] = c
        elif ("profes" in v or "ocupac" in v) and "profesion_tutor" not in col_map:
            col_map["profesion_tutor"] = c
        elif ("domicil" in v or "direcc" in v) and "domicilio" not in col_map:
            col_map["domicilio"] = c
        elif ("tel" in v or "cel" in v) and "telefono" not in col_map:
            col_map["telefono"] = c
        elif "egres" in v and "egreso" not in col_map:
            col_map["egreso"] = c
        elif "pase" in v and "pase" not in col_map:
            col_map["pase"] = c
        elif "salida" in v and "salida_despues_30_4" not in col_map:
            col_map["salida_despues_30_4"] = c
        elif "ingresa" in v or ("ingr" in v and "30" not in v and "ingresa" not in col_map):
            col_map["ingresa"] = c
        elif ("ingr" in v and "30" in v) or "ingr. desp" in v or "ingr desp" in v:
            col_map["ingr_despues_30_4"] = c
        elif ("obs" in v or "observ" in v) and "observaciones" not in col_map:
            col_map["observaciones"] = c

    return header_row, col_map


def parse_curso_from_sheet_name(name):
    """
    Intenta extraer año y división del nombre de la pestaña (ej. '1°A', '1 A', '4° C', '3B').
    Retorna (anio, division) o None si no es una pestaña de curso.
    """
    # Evitar nombres explícitamente no correspondientes a cursos
    norm = normalize_text(name)
    if "blanco" in norm or "datos" in norm or "basicos" in norm or "resumen" in norm:
        return None

    match = re.search(r"([1-6])\s*[\°\^o]?\s*([A-Za-z])", name)
    if match:
        anio = int(match.group(1))
        div = match.group(2).upper()
        return anio, div
    return None


def read_excel_file(filepath):
    """
    Lee un archivo Excel y extrae únicamente las pestañas correspondientes a cursos.
    Retorna un diccionario estructurado con los datos listos para importar.
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    cursos_data = []
    hojas_ignoradas = []
    total_alumnos = 0

    for sheet_name in wb.sheetnames:
        curso_info = parse_curso_from_sheet_name(sheet_name)
        if not curso_info:
            hojas_ignoradas.append(sheet_name)
            continue

        anio, division = curso_info
        ws = wb[sheet_name]
        header_row, col_map = parse_header_map(ws)

        alumnos = []
        for r in range(header_row + 1, ws.max_row + 1):
            name_col = col_map.get("apellido_nombre")
            ord_col = col_map.get("nro_orden")

            name_val = clean_val(ws.cell(r, name_col).value) if name_col else ""
            ord_raw = ws.cell(r, ord_col).value if ord_col else None
            ord_val = clean_int(ord_raw)

            # Si no hay nombre ni orden válido, saltar fila
            if not name_val and ord_val is None:
                continue

            # Saltar filas de encabezado repetidas o subtítulos (ej. "30/6/2026")
            norm_name = normalize_text(name_val)
            if norm_name in ["apellido y nombre", "nombre", "apellido", "alumnos"]:
                continue
            if not name_val and ord_val is not None:
                # Si solo hay nro de orden pero no hay nombre, verificar si hay otros datos
                doc_col = col_map.get("doc")
                if not doc_col or not ws.cell(r, doc_col).value:
                    continue

            # Extraer campos
            tipo_doc, nro_doc = "", ""
            if "doc" in col_map:
                tipo_doc, nro_doc = clean_doc(ws.cell(r, col_map["doc"]).value)

            def get_c(key):
                if key in col_map:
                    return clean_val(ws.cell(r, col_map[key]).value)
                return ""

            alumno = {
                "nro_orden": ord_val,
                "fecha_inscripcion": get_c("fecha_inscripcion"),
                "nro_matricula": get_c("nro_matricula"),
                "apellido_nombre": name_val,
                "fecha_nac": get_c("fecha_nac"),
                "edad": clean_int(ws.cell(r, col_map["edad"]).value) if "edad" in col_map else None,
                "sexo": get_c("sexo"),
                "nacionalidad": get_c("nacionalidad"),
                "tipo_doc": tipo_doc,
                "nro_doc": nro_doc,
                "nombre_tutor": get_c("nombre_tutor"),
                "nacionalidad_tutor": get_c("nacionalidad_tutor"),
                "profesion_tutor": get_c("profesion_tutor"),
                "domicilio": get_c("domicilio"),
                "telefono": get_c("telefono"),
                "egreso": get_c("egreso"),
                "pase": get_c("pase"),
                "salida_despues_30_4": get_c("salida_despues_30_4"),
                "ingresa": get_c("ingresa"),
                "ingr_despues_30_4": get_c("ingr_despues_30_4"),
                "observaciones": get_c("observaciones"),
            }
            alumnos.append(alumno)

        total_alumnos += len(alumnos)
        cursos_data.append({
            "anio": anio,
            "division": division,
            "sheet_name": sheet_name,
            "alumnos": alumnos
        })

    return {
        "cursos": cursos_data,
        "total_alumnos": total_alumnos,
        "total_cursos": len(cursos_data),
        "hojas_ignoradas": hojas_ignoradas
    }


def import_excel_to_database(filepath, replace_existing=True):
    """
    Importa todos los cursos y alumnos del archivo Excel directamente a SQLite.
    
    Args:
        filepath: Ruta del archivo .xlsx
        replace_existing: Si True, reemplaza los alumnos de los cursos importados.
                         Si False, los añade a continuación.
    """
    data = read_excel_file(filepath)
    if not data["cursos"]:
        return {
            "success": False,
            "message": "No se encontraron pestañas de cursos válidas en el archivo.",
            "data": data
        }

    conn = db.get_connection()
    c = conn.cursor()

    alumnos_insertados = 0
    cursos_creados = 0

    try:
        for curso_info in data["cursos"]:
            anio = curso_info["anio"]
            div = curso_info["division"]
            alumnos = curso_info["alumnos"]

            # Obtener o crear el curso
            c.execute("SELECT id FROM cursos WHERE anio=? AND division=?", (anio, div))
            row = c.fetchone()
            if row:
                curso_id = row["id"]
            else:
                c.execute(
                    "INSERT INTO cursos (anio, division, ciclo_lectivo) VALUES (?, ?, ?)",
                    (anio, div, datetime.now().year)
                )
                curso_id = c.lastrowid
                cursos_creados += 1

            # Si se elige reemplazar, limpiar alumnos previos de ese curso
            if replace_existing:
                c.execute("DELETE FROM alumnos WHERE curso_id=?", (curso_id,))

            # Insertar alumnos
            for a in alumnos:
                c.execute("""
                    INSERT INTO alumnos (
                        curso_id, nro_orden, fecha_inscripcion, nro_matricula,
                        apellido_nombre, fecha_nac, edad, sexo, nacionalidad,
                        tipo_doc, nro_doc, nombre_tutor, nacionalidad_tutor,
                        profesion_tutor, domicilio, telefono, egreso, pase,
                        salida_despues_30_4, ingresa, ingr_despues_30_4, observaciones
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?
                    )
                """, (
                    curso_id, a["nro_orden"], a["fecha_inscripcion"], a["nro_matricula"],
                    a["apellido_nombre"], a["fecha_nac"], a["edad"], a["sexo"], a["nacionalidad"],
                    a["tipo_doc"], a["nro_doc"], a["nombre_tutor"], a["nacionalidad_tutor"],
                    a["profesion_tutor"], a["domicilio"], a["telefono"], a["egreso"], a["pase"],
                    a["salida_despues_30_4"], a["ingresa"], a["ingr_despues_30_4"], a["observaciones"]
                ))
                alumnos_insertados += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Error al guardar en la base de datos: {str(e)}",
            "data": data
        }
    finally:
        conn.close()

    return {
        "success": True,
        "total_alumnos": alumnos_insertados,
        "total_cursos": len(data["cursos"]),
        "cursos_creados": cursos_creados,
        "hojas_ignoradas": data["hojas_ignoradas"],
        "cursos_info": [f"{c['anio']}° {c['division']} ({len(c['alumnos'])} alumnos)" for c in data["cursos"]]
    }
