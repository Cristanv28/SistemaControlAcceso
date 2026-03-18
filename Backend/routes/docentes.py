from flask import Blueprint, jsonify, request
from database import get_cursor

docentes_bp = Blueprint("docentes", __name__)

#  DOCENTES

@docentes_bp.route("/docentes", methods=["GET"])
def obtener_docentes():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT
            u.numero_control,
            CONCAT(u.nombre,' ',u.apellido_p,' ',u.apellido_m) AS nombre,
            COALESCE(a.nombre_area, '—') AS nombre_area,
            u.activo
        FROM usuario u
        LEFT JOIN area a ON u.id_area = a.id_area
        WHERE u.tipo = 'docente'
    """)

    rows = cur.fetchall()
    conn.close()

    return jsonify([{
        "id":           r["numero_control"],
        "nombre":       r["nombre"],
        "departamento": r["nombre_area"],
        "estado":       "Activo" if r["activo"] else "Inactivo"
    } for r in rows])


@docentes_bp.route("/docentes/<control>", methods=["PUT"])
def editar_docente(control):

    data   = request.json
    estado = int(data.get("estado", 1))
    id_area = data.get("id_area")

    conn, cur = get_cursor()

    if id_area:
        cur.execute("""
            UPDATE usuario SET activo=%s, id_area=%s
            WHERE numero_control=%s AND tipo='docente'
        """, (estado, id_area, control))
    else:
        cur.execute("""
            UPDATE usuario SET activo=%s
            WHERE numero_control=%s AND tipo='docente'
        """, (estado, control))

    cur.execute("""
        UPDATE tarjeta_nfc t
        JOIN usuario u ON t.id_usuario = u.id_usuario
        SET t.activa = %s
        WHERE u.numero_control = %s
    """, (estado, control))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Docente actualizado correctamente"})


@docentes_bp.route("/docentes/<control>", methods=["DELETE"])
def eliminar_docente(control):

    conn, cur = get_cursor()

    cur.execute("SELECT id_usuario FROM usuario WHERE numero_control=%s AND tipo='docente'", (control,))
    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return jsonify({"error": "Docente no encontrado"}), 404

    id_usuario = usuario["id_usuario"]

    cur.execute("""
        DELETE r FROM registro_acceso r
        JOIN tarjeta_nfc t ON r.id_tarjeta = t.id_tarjeta
        WHERE t.id_usuario = %s
    """, (id_usuario,))

    cur.execute("DELETE FROM tarjeta_nfc WHERE id_usuario = %s", (id_usuario,))
    cur.execute("DELETE FROM usuario     WHERE id_usuario = %s", (id_usuario,))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Docente eliminado correctamente"})


# ══════════════════════════════════════════
#  ADMINISTRATIVOS
# ══════════════════════════════════════════

@docentes_bp.route("/administrativos", methods=["GET"])
def obtener_admin():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT
            u.numero_control,
            CONCAT(u.nombre,' ',u.apellido_p,' ',u.apellido_m) AS nombre,
            COALESCE(a.nombre_area, '—') AS nombre_area,
            u.activo
        FROM usuario u
        LEFT JOIN area a ON u.id_area = a.id_area
        WHERE u.tipo = 'administrativo'
    """)

    rows = cur.fetchall()
    conn.close()

    return jsonify([{
        "id":     r["numero_control"],
        "nombre": r["nombre"],
        "area":   r["nombre_area"],
        "estado": "Activo" if r["activo"] else "Inactivo"
    } for r in rows])


@docentes_bp.route("/administrativos/<control>", methods=["PUT"])
def editar_admin(control):

    data    = request.json
    estado  = int(data.get("estado", 1))
    id_area = data.get("id_area")

    conn, cur = get_cursor()

    if id_area:
        cur.execute("""
            UPDATE usuario SET activo=%s, id_area=%s
            WHERE numero_control=%s AND tipo='administrativo'
        """, (estado, id_area, control))
    else:
        cur.execute("""
            UPDATE usuario SET activo=%s
            WHERE numero_control=%s AND tipo='administrativo'
        """, (estado, control))

    cur.execute("""
        UPDATE tarjeta_nfc t
        JOIN usuario u ON t.id_usuario = u.id_usuario
        SET t.activa = %s
        WHERE u.numero_control = %s
    """, (estado, control))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Administrativo actualizado correctamente"})


@docentes_bp.route("/administrativos/<control>", methods=["DELETE"])
def eliminar_admin(control):

    conn, cur = get_cursor()

    cur.execute("SELECT id_usuario FROM usuario WHERE numero_control=%s AND tipo='administrativo'", (control,))
    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return jsonify({"error": "Administrativo no encontrado"}), 404

    id_usuario = usuario["id_usuario"]

    cur.execute("""
        DELETE r FROM registro_acceso r
        JOIN tarjeta_nfc t ON r.id_tarjeta = t.id_tarjeta
        WHERE t.id_usuario = %s
    """, (id_usuario,))

    cur.execute("DELETE FROM tarjeta_nfc WHERE id_usuario = %s", (id_usuario,))
    cur.execute("DELETE FROM usuario     WHERE id_usuario = %s", (id_usuario,))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Administrativo eliminado correctamente"})


# ══════════════════════════════════════════
#  REGISTRAR DOCENTE  POST /docentes
# ══════════════════════════════════════════

@docentes_bp.route("/docentes", methods=["POST"])
def crear_docente():
    try:
        data       = request.json
        nombre     = data.get("nombre")
        apellido_p = data.get("apellido_p")
        apellido_m = data.get("apellido_m") or ""
        control    = data.get("control")
        area_texto = data.get("area", "").strip()

        if not all([nombre, apellido_p, control]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        conn, cur = get_cursor()

        cur.execute("SELECT id_usuario FROM usuario WHERE numero_control=%s", (control,))
        if cur.fetchone():
            conn.close()
            return jsonify({"error": "Ya existe un usuario con ese número de control"}), 400

        id_area = None
        if area_texto:
            cur.execute("SELECT id_area FROM area WHERE nombre_area=%s", (area_texto,))
            row = cur.fetchone()
            if row:
                id_area = row["id_area"]
            else:
                cur.execute("INSERT INTO area (nombre_area, descripcion) VALUES (%s, '')", (area_texto,))
                id_area = cur.lastrowid

        cur.execute("""
            INSERT INTO usuario
            (numero_control, nombre, apellido_p, apellido_m, tipo, activo, id_area)
            VALUES (%s, %s, %s, %s, 'docente', 1, %s)
        """, (control, nombre, apellido_p, apellido_m, id_area))

        conn.commit()
        conn.close()
        return jsonify({"mensaje": "Docente registrado correctamente"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════
#  REGISTRAR ADMINISTRATIVO  POST /administrativos
# ══════════════════════════════════════════
@docentes_bp.route("/administrativos", methods=["POST"])
def crear_admin():
    try:
        data       = request.json
        nombre     = data.get("nombre")
        apellido_p = data.get("apellido_p")
        apellido_m = data.get("apellido_m") or ""
        control    = data.get("control")
        area_texto = data.get("area", "").strip()

        if not all([nombre, apellido_p, control]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        conn, cur = get_cursor()

        cur.execute("SELECT id_usuario FROM usuario WHERE numero_control=%s", (control,))
        if cur.fetchone():
            conn.close()
            return jsonify({"error": "Ya existe un usuario con ese número de control"}), 400

        id_area = None
        if area_texto:
            cur.execute("SELECT id_area FROM area WHERE nombre_area=%s", (area_texto,))
            row = cur.fetchone()
            if row:
                id_area = row["id_area"]
            else:
                cur.execute("INSERT INTO area (nombre_area, descripcion) VALUES (%s, '')", (area_texto,))
                id_area = cur.lastrowid

        cur.execute("""
            INSERT INTO usuario
            (numero_control, nombre, apellido_p, apellido_m, tipo, activo, id_area)
            VALUES (%s, %s, %s, %s, 'administrativo', 1, %s)
        """, (control, nombre, apellido_p, apellido_m, id_area))

        conn.commit()
        conn.close()
        return jsonify({"mensaje": "Administrativo registrado correctamente"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════
#  GET /areas  — para llenar los selects
# ══════════════════════════════════════════

@docentes_bp.route("/areas", methods=["GET"])
def obtener_areas():
    conn, cur = get_cursor()
    cur.execute("SELECT id_area, nombre_area FROM area ORDER BY nombre_area")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)
