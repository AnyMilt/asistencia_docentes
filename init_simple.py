#!/usr/bin/env python3
"""
Script simplificado para inicializar la base de datos
"""

import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar solo lo necesario para crear la base de datos
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Crear aplicación mínima
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar solo SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Importar modelos después de inicializar db
from models.usuario import Usuario
from models.docente import Docente
from models.asistencia import Asistencia
from models.licencia import Licencia

def init_database():
    """Inicializa la base de datos y crea tablas"""
    with app.app_context():
        print("Creando tablas de la base de datos...")
        db.create_all()
        print("Tablas creadas exitosamente")

def create_admin_user():
    """Crea un usuario administrador por defecto"""
    with app.app_context():
        # Verificar si ya existe un admin
        admin_exists = Usuario.query.filter_by(username='admin').first()
        
        if admin_exists:
            print("El usuario administrador ya existe")
            return
        
        print("Creando usuario administrador...")
        
        admin = Usuario(
            username='admin',
            rol='admin',
            activo=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("Usuario administrador creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")

if __name__ == '__main__':
    print("Inicializando base de datos...")
    init_database()
    create_admin_user()
    print("Inicialización completada!")
