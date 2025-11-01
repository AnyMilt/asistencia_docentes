#!/usr/bin/env python3
"""
Script para crear solo las tablas de la base de datos
"""

import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar configuración
from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Crear aplicación mínima
app = Flask(__name__)
app.config.from_object(Config)

# Crear instancia de SQLAlchemy
db = SQLAlchemy()

# Definir modelos aquí mismo para evitar problemas de importación
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    ultimo_acceso = db.Column(db.DateTime)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

class Docente(db.Model):
    __tablename__ = 'docentes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    cedula = db.Column(db.String(10), unique=True, nullable=False, index=True)
    telefono = db.Column(db.String(15), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False, index=True)
    jornada = db.Column(db.String(20), nullable=False, index=True)
    qr_code_path = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True, index=True)
    tipo = db.Column(db.String(20), nullable=False, index=True)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora_entrada = db.Column(db.Time, index=True)
    hora_salida = db.Column(db.Time)
    estado = db.Column(db.String(20), default='pendiente', index=True)
    jornada = db.Column(db.String(20), nullable=False, index=True)  # matutina, vespertina
    device_id = db.Column(db.String(100), nullable=True, index=True)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Licencia(db.Model):
    __tablename__ = 'licencias'
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False, index=True)
    fecha_inicio = db.Column(db.Date, nullable=False, index=True)
    fecha_fin = db.Column(db.Date, nullable=False, index=True)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='pendiente', index=True)
    aprobado_por = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Inicializar db con la app
db.init_app(app)

def main():
    with app.app_context():
        print("Creando tablas de la base de datos...")
        db.create_all()
        print("Tablas creadas exitosamente")
        
        # Crear usuario administrador
        admin_exists = Usuario.query.filter_by(username='admin').first()
        if not admin_exists:
            print("Creando usuario administrador...")
            admin = Usuario(username='admin', rol='admin', activo=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado:")
            print("   Usuario: admin")
            print("   Contraseña: admin123")
        else:
            print("El usuario administrador ya existe")
        
        print("Inicialización completada!")

if __name__ == '__main__':
    main()
