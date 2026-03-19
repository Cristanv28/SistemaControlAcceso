from flask import Blueprint, request, jsonify
from database import get_cursor
from datetime import datetime

nodo_bp = Blueprint("nodo", __name__)

@nodo_bp.route("/nodo/heartbeat", methods=["POST"])
def heartbeat():

    data     = request.json or {}
    id_nodo  = data.get("id_nodo")
    ip_local = data.get("ip_local", "")

    # ── Actualizar ultima conexion del nodo ──
    try:
        conn, cur = get_cursor()

        cur.execute("""
            INSERT INTO nodo (id_nodo, ip_local, ultimo_heartbeat)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                ip_local           = VALUES(ip_local),
                ultimo_heartbeat   = VALUES(ultimo_heartbeat)
        """, (id_nodo, ip_local, datetime.now()))

        conn.commit()
        conn.close()

    except Exception as e:
        # Si la tabla nodo no existe aun, no rompemos el heartbeat
        print("Heartbeat DB error (no critico):", e)

    # ── Consultar emergencia activa ──────────
    try:
        conn, cur = get_cursor()

        cur.execute("""
            SELECT tipo FROM emergencia
            WHERE estado = 'activa'
            ORDER BY inicio DESC
            LIMIT 1
        """)

        row = cur.fetchone()
        conn.close()

        if row:
            tipo_emergencia = row["tipo"]   # "lockdown" | "evacuacion"
        else:
            tipo_emergencia = ""

    except Exception as e:
        print("Error consultando emergencia:", e)
        tipo_emergencia = ""

    return jsonify({
        "emergencia": tipo_emergencia,
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
