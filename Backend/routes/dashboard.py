from flask import Blueprint, jsonify
from database import get_cursor

dashboard_bp = Blueprint("dashboard", __name__)


# ──────────────────────────────────────────
#  GET /dashboard/stats
#  Conteos generales + accesos del día
# ──────────────────────────────────────────
@dashboard_bp.route("/dashboard/stats")
def stats():

    conn, cur = get_cursor()

    # Totales por tipo de usuario
    cur.execute("SELECT COUNT(*) as total FROM usuario WHERE tipo='alumno'    AND activo=1")
    total_estudiantes = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM usuario WHERE tipo='docente'   AND activo=1")
    total_docentes = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM usuario WHERE tipo='administrativo' AND activo=1")
    total_admin = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM usuario WHERE tipo='empleado'  AND activo=1")
    total_empleados = cur.fetchone()["total"]

    # Accesos de hoy
    cur.execute("""
        SELECT COUNT(*) as total
        FROM registro_acceso
        WHERE DATE(timestamp) = CURDATE()
        AND resultado = 'permitido'
    """)
    accesos_hoy = cur.fetchone()["total"]

    # Accesos denegados hoy
    cur.execute("""
        SELECT COUNT(*) as total
        FROM registro_acceso
        WHERE DATE(timestamp) = CURDATE()
        AND resultado = 'denegado'
    """)
    denegados_hoy = cur.fetchone()["total"]

    conn.close()

    return jsonify({
        "estudiantes": total_estudiantes,
        "docentes":    total_docentes,
        "administrativos": total_admin,
        "empleados":   total_empleados,
        "accesos_hoy": accesos_hoy,
        "denegados_hoy": denegados_hoy
    })


# ──────────────────────────────────────────
#  GET /dashboard/actividad
#  Últimos 10 accesos
# ──────────────────────────────────────────
@dashboard_bp.route("/dashboard/actividad")
def actividad():

    conn, cur = get_cursor()

    cur.execute("""
        SELECT
            u.nombre,
            u.apellido_p,
            r.tipo_evento,
            r.resultado,
            r.timestamp
        FROM registro_acceso r
        JOIN tarjeta_nfc t ON r.id_tarjeta = t.id_tarjeta
        JOIN usuario u     ON t.id_usuario  = u.id_usuario
        ORDER BY r.timestamp DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    data = []

    for r in rows:
        data.append({
            "nombre":    f"{r['nombre']} {r['apellido_p']}",
            "tipo":      r["tipo_evento"],
            "resultado": r["resultado"],
            "hora":      r["timestamp"].strftime("%H:%M:%S"),
            "fecha":     r["timestamp"].strftime("%d/%m/%Y")
        })

    conn.close()

    return jsonify(data)   # ← jsonify corregido
