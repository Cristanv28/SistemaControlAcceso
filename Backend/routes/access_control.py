from flask import Blueprint, request, jsonify
from database import get_cursor

access_bp = Blueprint("access", __name__)

# Fallback en memoria por si la tabla no existe aún
_modo_memoria = {"modo": "normal"}


def _asegurar_tabla():
    """Crea la tabla configuracion si no existe."""
    conn, cur = get_cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave  VARCHAR(50)  PRIMARY KEY,
            valor  VARCHAR(100) NOT NULL
        )
    """)
    cur.execute("""
        INSERT IGNORE INTO configuracion (clave, valor)
        VALUES ('modo_acceso', 'normal')
    """)
    conn.commit()
    conn.close()


def _get_modo_db():
    try:
        _asegurar_tabla()
        conn, cur = get_cursor()
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'modo_acceso'")
        row = cur.fetchone()
        conn.close()
        return row["valor"] if row else "normal"
    except Exception as e:
        print("Error leyendo modo:", e)
        return _modo_memoria["modo"]


def _set_modo_db(modo):
    try:
        _asegurar_tabla()
        conn, cur = get_cursor()
        cur.execute("""
            INSERT INTO configuracion (clave, valor)
            VALUES ('modo_acceso', %s)
            ON DUPLICATE KEY UPDATE valor = %s
        """, (modo, modo))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error guardando modo:", e)
    # Siempre actualizar memoria como respaldo
    _modo_memoria["modo"] = modo


@access_bp.route("/access-mode", methods=["GET"])
def get_mode():
    modo = _get_modo_db()
    return jsonify({"modo": modo})


@access_bp.route("/access-mode", methods=["POST"])
def set_mode():
    data = request.json
    modo = data.get("modo", "normal")
    _set_modo_db(modo)
    return jsonify({"mensaje": "Modo actualizado", "modo": modo})
