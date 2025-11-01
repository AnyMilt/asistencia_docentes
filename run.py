from app_simple import create_app, db

app = create_app()

# Crear base de datos si no existe
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)