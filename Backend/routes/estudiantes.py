from flask import Blueprint, request, jsonify
from database import get_cursor

estudiantes_bp = Blueprint("estudiantes", __name__)

@estudiantes_bp.route("/estudiantes", methods=["GET"])
def obtener_estudiantes():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT 
            u.numero_control,
            u.nombre,
            u.apellido_p,
            u.apellido_m,
            c.nombre_carrera,
            a.semestre,
            u.activo
        FROM alumno a
        JOIN usuario u ON a.id_usuario = u.id_usuario
        JOIN carrera c ON a.id_carrera = c.id_carrera
    """)

    rows = cur.fetchall()

    estudiantes = []

    for r in rows:

        nombre = f"{r['nombre']} {r['apellido_p']} {r['apellido_m']}"

        estudiantes.append({
            "control": r["numero_control"],
            "nombre": nombre,
            "carrera": r["nombre_carrera"],
            "semestre": r["semestre"],
            "estado": "Activo" if r["activo"] else "Inactivo"
        })

    conn.close()

    return jsonify(estudiantes)

@estudiantes_bp.route("/estudiantes", methods=["POST"])
def crear_estudiante():

    try:

        data = request.json

        nombre = data.get("nombre")
        apellido_p = data.get("apellido_p")
        apellido_m = data.get("apellido_m")
        control = data.get("control")
        carrera = data.get("carrera")
        semestre = data.get("semestre")

        conn, cur = get_cursor()

        # verificar si ya existe
        cur.execute("""
            SELECT id_usuario
            FROM usuario
            WHERE numero_control=%s
        """,(control,))

        if cur.fetchone():
            conn.close()
            return jsonify({"error":"El estudiante ya existe"}),400


        # crear usuario
        cur.execute("""
            INSERT INTO usuario
            (numero_control,nombre,apellido_p,apellido_m,tipo,activo)
            VALUES (%s,%s,%s,%s,'alumno',1)
        """,(control,nombre,apellido_p,apellido_m))

        id_usuario = cur.lastrowid


        # buscar carrera
        cur.execute("""
            SELECT id_carrera
            FROM carrera
            WHERE nombre_carrera=%s
        """,(carrera,))

        carrera_row = cur.fetchone()

        if not carrera_row:
            conn.close()
            return jsonify({"error":"Carrera no encontrada"}),404

        id_carrera = carrera_row["id_carrera"]


        # crear alumno
        cur.execute("""
            INSERT INTO alumno
            (id_usuario,id_carrera,semestre)
            VALUES (%s,%s,%s)
        """,(id_usuario,id_carrera,semestre))


        conn.commit()
        conn.close()

        return jsonify({
            "mensaje":"Estudiante registrado correctamente",
            "id_usuario":id_usuario
        })


    except Exception as e:

        return jsonify({"error":str(e)}),500

@estudiantes_bp.route("/estudiantes/<control>", methods=["PUT"])
def editar_estudiante(control):

    data = request.json

    semestre = data.get("semestre")
    estado = int(data.get("estado"))

    conn, cur = get_cursor()

    # actualizar estudiante
    cur.execute("""
        UPDATE usuario u
        JOIN alumno a ON a.id_usuario = u.id_usuario
        SET 
            a.semestre=%s,
            u.activo=%s
        WHERE u.numero_control=%s
    """,(semestre,estado,control))

    # sincronizar tarjeta
    cur.execute("""
        UPDATE tarjeta_nfc t
        JOIN usuario u ON t.id_usuario = u.id_usuario
        SET t.activa=%s
        WHERE u.numero_control=%s
    """,(estado,control))

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error":"Estudiante no encontrado"}),404

    conn.close()

    return jsonify({"mensaje":"Estudiante actualizado correctamente"})

@estudiantes_bp.route("/estudiantes/<control>", methods=["DELETE"])
def eliminar_estudiante(control):

    conn, cur = get_cursor()

    cur.execute("""
        SELECT id_usuario
        FROM usuario
        WHERE numero_control=%s
    """,(control,))

    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return jsonify({"error":"Estudiante no encontrado"}),404

    id_usuario = usuario["id_usuario"]


    # eliminar registros de acceso
    cur.execute("""
        DELETE r FROM registro_acceso r
        JOIN tarjeta_nfc t ON r.id_tarjeta=t.id_tarjeta
        WHERE t.id_usuario=%s
    """,(id_usuario,))


    cur.execute("""
        DELETE FROM tarjeta_nfc
        WHERE id_usuario=%s
    """,(id_usuario,))


    cur.execute("""
        DELETE FROM alumno
        WHERE id_usuario=%s
    """,(id_usuario,))

    cur.execute("""
        DELETE FROM usuario
        WHERE id_usuario=%s
    """,(id_usuario,))


    conn.commit()
    conn.close()

    return jsonify({"mensaje":"Estudiante eliminado correctamente"})