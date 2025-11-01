#!/usr/bin/env python3
"""
Script para inicializar la base de datos y crear usuario administrador
"""

import os
import sys
from datetime import datetime

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.usuario import Usuario
from models.docente import Docente
from models.asistencia import Asistencia
from models.licencia import Licencia

def init_database():
    """Inicializa la base de datos y crea tablas"""
    app = create_app()
    
    with app.app_context():
        print("Creando tablas de la base de datos...")
        db.create_all()
        print("Tablas creadas exitosamente")

def create_admin_user():
    """Crea un usuario administrador por defecto"""
    app = create_app()
    
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
        admin.set_password('admin123')  # Cambiar en producción
        
        db.session.add(admin)
        db.session.commit()
        
        print("Usuario administrador creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   IMPORTANTE: Cambia la contraseña después del primer login")

def create_sample_data():
    """Crea datos de ejemplo para testing"""
    app = create_app()
    
    with app.app_context():
        print("Creando datos de ejemplo...")
        
        # Crear docentes de ejemplo
        docentes_ejemplo = [
            {'nombre': 'María González', 'jornada': 'matutina', 'tipo': 'DOCENTE'},
            {'nombre': 'Carlos Rodríguez', 'jornada': 'vespertina', 'tipo': 'DOCENTE'},
            {'nombre': 'Ana López', 'jornada': 'matutina', 'tipo': 'ADMINISTRATIVO'},
            {'nombre': 'Pedro Martínez', 'jornada': 'vespertina', 'tipo': 'CONSERJE'},
        ]
        
        for datos in docentes_ejemplo:
            docente_existente = Docente.query.filter_by(nombre=datos['nombre']).first()
            if not docente_existente:
                docente = Docente(**datos)
                db.session.add(docente)
        
        db.session.commit()
        print("Datos de ejemplo creados")

def main():
    """Función principal"""
    print("Inicializando sistema de asistencia docente...")
    print("=" * 50)
    
    try:
        # Inicializar base de datos
        init_database()
        
        # Crear usuario administrador
        create_admin_user()
        
        # Crear datos de ejemplo (opcional)
        respuesta = input("\n¿Crear datos de ejemplo? (s/n): ").lower().strip()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            create_sample_data()
        
        print("\n" + "=" * 50)
        print("Inicialización completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Ejecuta: python run.py")
        print("2. Ve a: http://localhost:5000")
        print("3. Inicia sesión con: admin / admin123")
        print("4. Cambia la contraseña del administrador")
        print("5. Crea usuarios adicionales según necesites")
        
    except Exception as e:
        print(f"Error durante la inicialización: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
