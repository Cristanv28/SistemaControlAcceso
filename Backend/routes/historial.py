from flask import Blueprint, jsonify, request
from database import get_cursor

history_bp = Blueprint("history", __name__)

@history_bp.route("/history")
def history():

    conn, cur = get_cursor()

    fecha = request.args.get("fecha")
    tipo = request.args.get("tipo")
    carrera = request.args.get("carrera")

    query = """
    SELECT 
        u.nombre,
        u.numero_control,
        c.nombre_carrera,
        r.tipo_evento,
        r.timestamp
    FROM registro_acceso r
    JOIN tarjeta_nfc t ON r.id_tarjeta = t.id_tarjeta
    JOIN usuario u ON t.id_usuario = u.id_usuario
    LEFT JOIN alumno a ON u.id_usuario = a.id_usuario
    LEFT JOIN carrera c ON a.id_carrera = c.id_carrera
    WHERE 1=1
    """

    params = []

    if fecha:
        query += " AND DATE(r.timestamp) = %s"
        params.append(fecha)

    if tipo:
        query += " AND r.tipo_evento = %s"
        params.append(tipo)

    if carrera:
        query += " AND c.nombre_carrera = %s"
        params.append(carrera)

    query += " ORDER BY r.timestamp DESC"

    cur.execute(query, params)

    rows = cur.fetchall()

    data = []

    for r in rows:

       data.append({
    "nombre": f"{r['nombre']} {r.get('apellido_p','')} {r.get('apellido_m','')}",
    "control": r["numero_control"],
    "carrera": r["nombre_carrera"],
    "tipo": r["tipo_evento"],
    "fecha": r["timestamp"].strftime("%Y-%m-%d"),
    "hora": r["timestamp"].strftime("%H:%M:%S")
})

    conn.close()

    return jsonify(data)