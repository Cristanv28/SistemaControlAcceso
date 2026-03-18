from flask import Blueprint, jsonify, request
from database import get_cursor
from datetime import datetime

emergency_bp = Blueprint("emergency", __name__)


# ──────────────────────────────────────────
#  GET /emergency/codigos
# ──────────────────────────────────────────
@emergency_bp.route("/emergency/codigos")
def obtener_codigos():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT id_codigo, codigo, color, descripcion
        FROM codigo_emergencia
        ORDER BY id_codigo
    """)

    data = cur.fetchall()
    conn.close()

    return jsonify(data)


# ──────────────────────────────────────────
#  GET /emergency  →  estado actual
# ──────────────────────────────────────────
@emergency_bp.route("/emergency", methods=["GET"])
def estado():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT e.id_emergencia, e.tipo, e.inicio, e.motivo, e.estado,
               c.color
        FROM emergencia e
        LEFT JOIN codigo_emergencia c ON e.id_codigo = c.id_codigo
        WHERE e.estado = 'activa'
        ORDER BY e.inicio DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()

    if row:
        return jsonify({
            "activo": True,
            "codigo": row["motivo"],
            "tipo":   row["tipo"],
            "color":  row["color"],
            "inicio": row["inicio"].strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify({"activo": False, "codigo": None})


# ──────────────────────────────────────────
#  POST /emergency  →  activar emergencia
# ──────────────────────────────────────────
@emergency_bp.route("/emergency", methods=["POST"])
def activar_emergencia():

    try:

        data      = request.json
        id_codigo = data.get("id_codigo")
        tipo      = data.get("tipo")

        conn, cur = get_cursor()

        cur.execute("""
            SELECT codigo, descripcion
            FROM codigo_emergencia
            WHERE id_codigo = %s
        """, (id_codigo,))

        codigo = cur.fetchone()

        if not codigo:
            conn.close()
            return jsonify({"error": "Código de emergencia no encontrado"}), 404

        motivo = f"{codigo['codigo']} - {codigo['descripcion']}"
        ahora  = datetime.now()

        cur.execute("""
            INSERT INTO emergencia (tipo, inicio, motivo, estado, id_codigo)
            VALUES (%s, %s, %s, 'activa', %s)
        """, (tipo, ahora, motivo, id_codigo))

        conn.commit()
        conn.close()

        return jsonify({"mensaje": "Emergencia activada", "motivo": motivo})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────
#  DELETE /emergency  →  desactivar
# ──────────────────────────────────────────
@emergency_bp.route("/emergency", methods=["DELETE"])
def desactivar():

    conn, cur = get_cursor()

    cur.execute("""
        UPDATE emergencia
        SET fin = %s, estado = 'finalizada'
        WHERE estado = 'activa'
    """, (datetime.now(),))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Emergencia desactivada"})
