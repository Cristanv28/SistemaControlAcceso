from flask import Blueprint, jsonify
from database import get_cursor

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/stats")
def stats():
    conn, cur = get_cursor()

    try:
        cur.execute("""
            SELECT 
                SUM(resultado = 'permitido') as accesos,
                SUM(resultado = 'denegado') as denegados
            FROM registro_acceso
            WHERE timestamp >= CURDATE()
            AND timestamp < CURDATE() + INTERVAL 1 DAY
        """)

        row = cur.fetchone()

        return jsonify({
            "accesos_hoy": row["accesos"] or 0,
            "denegados_hoy": row["denegados"] or 0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()