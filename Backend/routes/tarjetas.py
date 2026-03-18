from flask import Blueprint, jsonify, request
from database import get_cursor

tarjetas_bp = Blueprint("tarjetas", __name__)

_modo_registro = {"activo": False, "id_usuario": None}


@tarjetas_bp.route("/tarjetas")
def tarjetas():
    conn, cur = get_cursor()

    cur.execute("""
    SELECT
        u.numero_control,
        u.nombre,
        u.apellido_p,
        u.apellido_m,
        u.tipo,
        c.nombre_carrera,
        a.semestre,
        t.uid_rfid,
        t.activa,
        t.fecha_registro
    FROM usuario u
    LEFT JOIN tarjeta_nfc t ON t.id_usuario = u.id_usuario
    LEFT JOIN alumno a ON a.id_usuario = u.id_usuario
    LEFT JOIN carrera c ON a.id_carrera = c.id_carrera
    WHERE u.activo = 1
    """)

    rows = cur.fetchall()
    data = []

    for r in rows:
        nombre = f"{r['nombre']} {r['apellido_p']} {r['apellido_m']}"
        data.append({
            "control": r["numero_control"],
            "nombre": nombre,
            "tipo": r["tipo"],
            "carrera": r["nombre_carrera"] if r["nombre_carrera"] else "-",
            "semestre": r["semestre"] if r["semestre"] else "-",
            "estado": "Activa" if r["activa"] else ("Inactiva" if r["uid_rfid"] else "Sin tarjeta"),
            "fecha": str(r["fecha_registro"]) if r["fecha_registro"] else "-"
        })

    conn.close()
    return jsonify(data)

@tarjetas_bp.route("/tarjetas/modo-registro", methods=["GET"])
def get_modo_registro():
    return jsonify(_modo_registro)

@tarjetas_bp.route("/tarjetas/modo-registro", methods=["POST"])
def set_modo_registro():
    data = request.json or {}
    activo = data.get("activo", True)

    if not activo:
        _modo_registro["activo"] = False
        _modo_registro["id_usuario"] = None
        return jsonify({"mensaje": "Modo registro desactivado"})

    id_usuario = data.get("id_usuario")
    if not id_usuario:
        return jsonify({"error": "id_usuario requerido"}), 400

    # Verificar que el usuario existe
    conn, cur = get_cursor()
    cur.execute("SELECT id_usuario, nombre FROM usuario WHERE id_usuario = %s AND activo = 1",
                (id_usuario,))
    usuario = cur.fetchone()
    conn.close()

    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    _modo_registro["activo"] = True
    _modo_registro["id_usuario"] = id_usuario

    return jsonify({
        "mensaje": f"Modo registro activo para {usuario['nombre']}",
        "id_usuario": id_usuario
    })


@tarjetas_bp.route("/tarjetas/registrar-uid", methods=["POST"])
def registrar_uid():
    if not _modo_registro["activo"] or not _modo_registro["id_usuario"]:
        return jsonify({"modo_registro": False}), 200

    data = request.json or {}
    uid = data.get("uid_rfid", "").upper()

    if not uid:
        return jsonify({"error": "uid_rfid requerido"}), 400

    conn, cur = get_cursor()

    try:
        # Verificar si el UID ya está en uso por otro usuario
        cur.execute("SELECT id_tarjeta, id_usuario FROM tarjeta_nfc WHERE uid_rfid = %s", (uid,))
        existente = cur.fetchone()

        if existente and existente["id_usuario"] != _modo_registro["id_usuario"]:
            conn.close()
            return jsonify({
                "modo_registro": True,
                "registrado": False,
                "error": "UID ya asignado a otro usuario"
            }), 409

        id_usuario = _modo_registro["id_usuario"]

        if existente and existente["id_usuario"] == id_usuario:
            # Actualizar tarjeta existente
            cur.execute("""
                UPDATE tarjeta_nfc SET uid_rfid = %s, activa = 1, fecha_registro = NOW()
                WHERE id_usuario = %s
            """, (uid, id_usuario))
        else:
            # Desactivar tarjeta anterior si existe
            cur.execute("UPDATE tarjeta_nfc SET activa = 0 WHERE id_usuario = %s", (id_usuario,))
            # Insertar nueva
            cur.execute("""
                INSERT INTO tarjeta_nfc (id_usuario, uid_rfid, activa, fecha_registro)
                VALUES (%s, %s, 1, NOW())
            """, (id_usuario, uid))

        conn.commit()

        # Obtener nombre del usuario para respuesta
        cur.execute("SELECT nombre FROM usuario WHERE id_usuario = %s", (id_usuario,))
        usuario = cur.fetchone()
        conn.close()

        # Desactivar modo registro automáticamente tras éxito
        _modo_registro["activo"] = False
        _modo_registro["id_usuario"] = None

        return jsonify({
            "modo_registro": True,
            "registrado": True,
            "uid": uid,
            "nombre": usuario["nombre"] if usuario else "—"
        })

    except Exception as e:
        print("Error registrando UID:", e)
        conn.close()
        return jsonify({"error": str(e)}), 500

@tarjetas_bp.route("/tarjetas/usuarios-sin-tarjeta")
def usuarios_sin_tarjeta():
    conn, cur = get_cursor()

    cur.execute("""
        SELECT u.id_usuario,
               CONCAT(u.nombre, ' ', u.apellido_p, ' ', u.apellido_m) AS nombre_completo,
               u.numero_control,
               u.tipo
        FROM usuario u
        LEFT JOIN tarjeta_nfc t ON t.id_usuario = u.id_usuario AND t.activa = 1
        WHERE u.activo = 1 AND t.id_tarjeta IS NULL
        ORDER BY u.nombre
    """)

    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)