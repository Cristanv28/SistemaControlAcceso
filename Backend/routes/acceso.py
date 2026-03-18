from flask import Blueprint, request, jsonify
from database import get_cursor

acceso_bp = Blueprint("acceso", __name__)


def _get_modo_acceso():
    """Lee el modo de acceso actual desde la BD."""
    try:
        conn, cur = get_cursor()
        cur.execute("SELECT valor FROM configuracion WHERE clave = 'modo_acceso'")
        row = cur.fetchone()
        conn.close()
        return row["valor"] if row else "normal"
    except Exception:
        return "normal"


def _hay_emergencia_activa():
    """Devuelve (activa: bool, tipo: str|None)"""
    try:
        conn, cur = get_cursor()
        cur.execute("""
            SELECT tipo FROM emergencia
            WHERE estado = 'activa'
            ORDER BY inicio DESC LIMIT 1
        """)
        row = cur.fetchone()
        conn.close()
        if row:
            return True, row["tipo"]
        return False, None
    except Exception:
        return False, None


@acceso_bp.route("/acceso/verificar", methods=["POST"])
def verificar():

    data = request.json

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    uid         = data.get("uid_rfid")
    tipo_evento = data.get("tipo_evento")   # "entrada" | "salida"
    id_nodo     = data.get("id_nodo")

    if not uid:
        return jsonify({"error": "UID no proporcionado"}), 400

    # ── 1. Verificar modo de emergencia ──────────────────────
    emergencia_activa, tipo_emergencia = _hay_emergencia_activa()

    if emergencia_activa:
        # Siempre bloquear todo durante emergencia activa
        return jsonify({
            "permitido": False,
            "motivo": f"Emergencia activa — acceso bloqueado ({tipo_emergencia})",
            "emergencia": True,
            "buzzer": True        # señal para que el ESP32 active el buzzer
        })

    # ── 2. Verificar modo de acceso (control manual) ─────────
    modo = _get_modo_acceso()

    if modo == "bloqueo_total":
        return jsonify({
            "permitido": False,
            "motivo": "Sistema en bloqueo total",
            "buzzer": False
        })

    if modo == "bloquear_entradas" and tipo_evento == "entrada":
        return jsonify({
            "permitido": False,
            "motivo": "Entradas bloqueadas",
            "buzzer": False
        })

    if modo == "bloquear_salidas" and tipo_evento == "salida":
        return jsonify({
            "permitido": False,
            "motivo": "Salidas bloqueadas",
            "buzzer": False
        })

    # ── 3. Verificar tarjeta ──────────────────────────────────
    conn, cur = get_cursor()

    try:
        cur.execute("""
        SELECT t.id_tarjeta, u.nombre, u.numero_control
        FROM tarjeta_nfc t
        JOIN usuario u ON u.id_usuario = t.id_usuario
        WHERE t.uid_rfid = %s
        AND t.activa = 1
        """, (uid,))

        tarjeta = cur.fetchone()

        if not tarjeta:
            cur.execute("""
            INSERT INTO registro_acceso
            (id_nodo, tipo_evento, resultado, motivo_denegado, timestamp)
            VALUES (%s, %s, 'denegado', 'Tarjeta no registrada', NOW())
            """, (id_nodo, tipo_evento))
            conn.commit()

            return jsonify({
                "permitido": False,
                "motivo": "Tarjeta no registrada",
                "buzzer": False
            })

        id_tarjeta = tarjeta["id_tarjeta"]
        nombre     = tarjeta["nombre"]
        control    = tarjeta["numero_control"]

        cur.execute("""
        INSERT INTO registro_acceso
        (id_tarjeta, id_nodo, tipo_evento, resultado, timestamp)
        VALUES (%s, %s, %s, 'permitido', NOW())
        """, (id_tarjeta, id_nodo, tipo_evento))

        conn.commit()

        return jsonify({
            "permitido": True,
            "nombre": nombre,
            "numero_control": control,
            "buzzer": False
        })

    except Exception as e:
        print("Error en acceso:", e)
        return jsonify({"error": "Error interno"}), 500

    finally:
        cur.close()
        conn.close()