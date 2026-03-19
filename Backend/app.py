from flask import Flask
from flask_cors import CORS

from routes.dashboard import dashboard_bp
from routes.estudiantes import estudiantes_bp
from routes.tarjetas import tarjetas_bp
from routes.historial import history_bp
from routes.acceso import acceso_bp
from routes.access_control import access_bp
from routes.emergency import emergency_bp   # ← ESTA LINEA CORRECTA
from routes.docentes import docentes_bp
from routes.empleados import empleados_bp
from routes.nodo import nodo_bp


app = Flask(__name__)

CORS(app)
app.register_blueprint(docentes_bp)
app.register_blueprint(empleados_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(estudiantes_bp)
app.register_blueprint(tarjetas_bp)
app.register_blueprint(history_bp)
app.register_blueprint(acceso_bp)
app.register_blueprint(access_bp)
app.register_blueprint(emergency_bp) 
app.register_blueprint(nodo_bp)   # ← REGISTRO

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)