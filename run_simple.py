#!/usr/bin/env python3
"""
Versión simplificada de la aplicación sin SocketIO
"""

from app_simple import create_app, db

app = create_app()

# Crear base de datos si no existe
with app.app_context():
    db.create_all()

# Evitar el mensaje "ngrok-skip-browser-warning"
@app.after_request
def skip_ngrok_warning(response):
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

if __name__ == '__main__':
    print("Iniciando aplicación de asistencia docente...")
    print("Accede a: http://localhost:5000")
    print("Usuario: admin")
    print("Contraseña: admin123")
    print("-" * 50)

    # Usar el servidor de desarrollo de Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
