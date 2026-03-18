from flask import Blueprint, jsonify, request
from database import get_cursor

empleados_bp = Blueprint("empleados", __name__)


@empleados_bp.route("/empleados", methods=["GET"])
def obtener_empleados():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT
            u.numero_control,
            CONCAT(u.nombre,' ',u.apellido_p,' ',u.apellido_m) AS nombre,
            e.puesto,
            u.activo
        FROM usuario u
        JOIN empleado e ON e.id_usuario = u.id_usuario
    """)

    rows = cur.fetchall()
    conn.close()

    return jsonify([{
        "id":     r["numero_control"],
        "nombre": r["nombre"],
        "puesto": r["puesto"],
        "estado": "Activo" if r["activo"] else "Inactivo"
    } for r in rows])


@empleados_bp.route("/empleados/<control>", methods=["PUT"])
def editar_empleado(control):

    data   = request.json
    estado = int(data.get("estado", 1))
    puesto = data.get("puesto")

    conn, cur = get_cursor()

    cur.execute("""
        UPDATE usuario
        SET activo = %s
        WHERE numero_control = %s
    """, (estado, control))

    if puesto:
        cur.execute("""
            UPDATE empleado e
            JOIN usuario u ON e.id_usuario = u.id_usuario
            SET e.puesto = %s
            WHERE u.numero_control = %s
        """, (puesto, control))

    cur.execute("""
        UPDATE tarjeta_nfc t
        JOIN usuario u ON t.id_usuario = u.id_usuario
        SET t.activa = %s
        WHERE u.numero_control = %s
    """, (estado, control))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Empleado actualizado correctamente"})


@empleados_bp.route("/empleados/<control>", methods=["DELETE"])
def eliminar_empleado(control):

    conn, cur = get_cursor()

    cur.execute("SELECT id_usuario FROM usuario WHERE numero_control = %s", (control,))
    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return jsonify({"error": "Empleado no encontrado"}), 404

    id_usuario = usuario["id_usuario"]

    cur.execute("""
        DELETE r FROM registro_acceso r
        JOIN tarjeta_nfc t ON r.id_tarjeta = t.id_tarjeta
        WHERE t.id_usuario = %s
    """, (id_usuario,))

    cur.execute("DELETE FROM tarjeta_nfc WHERE id_usuario = %s", (id_usuario,))
    cur.execute("DELETE FROM empleado    WHERE id_usuario = %s", (id_usuario,))
    cur.execute("DELETE FROM usuario     WHERE id_usuario = %s", (id_usuario,))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Empleado eliminado correctamente"})


# ══════════════════════════════════════════
#  REGISTRAR EMPLEADO  POST /empleados
# ══════════════════════════════════════════
@empleados_bp.route("/empleados", methods=["POST"])
def crear_empleado():
    try:
        data       = request.json
        nombre     = data.get("nombre")
        apellido_p = data.get("apellido_p")
        apellido_m = data.get("apellido_m") or ""
        control    = data.get("control")
        puesto     = data.get("puesto")

        if not all([nombre, apellido_p, control, puesto]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        conn, cur = get_cursor()

        cur.execute("SELECT id_usuario FROM usuario WHERE numero_control=%s", (control,))
        if cur.fetchone():
            conn.close()
            return jsonify({"error": "Ya existe un usuario con ese número de control"}), 400

        id_area = 1

        cur.execute("""
            INSERT INTO usuario
            (numero_control, nombre, apellido_p, apellido_m, tipo, activo, id_area)
            VALUES (%s, %s, %s, %s, 'empleado', 1, %s)
        """, (control, nombre, apellido_p, apellido_m, id_area))

        id_usuario = cur.lastrowid

        cur.execute("""
            INSERT INTO empleado (id_usuario, id_area, puesto)
            VALUES (%s, %s, %s)
        """, (id_usuario, id_area, puesto))

        conn.commit()
        conn.close()

        return jsonify({"mensaje": "Empleado registrado correctamente"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500