#!/usr/bin/env python3
"""
Script para probar el sistema completo de login/logout
"""

import requests
from requests.sessions import Session

def test_complete_auth():
    """Prueba completa del sistema de autenticación"""
    base_url = "http://localhost:5000"
    
    # Crear sesión
    session = Session()
    
    print("🧪 Probando sistema completo de autenticación...")
    print("=" * 60)
    
    # 1. Acceder a la página principal (debería redirigir a login)
    print("1️⃣ Accediendo a página principal...")
    response = session.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    # 2. Acceder a la página de login
    print("\n2️⃣ Accediendo a página de login...")
    response = session.get(f"{base_url}/auth/login")
    print(f"   Status: {response.status_code}")
    
    # 3. Hacer login
    print("\n3️⃣ Haciendo login...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    response = session.post(f"{base_url}/auth/login", data=login_data)
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    # 4. Acceder al dashboard (debería funcionar)
    print("\n4️⃣ Accediendo al dashboard...")
    response = session.get(f"{base_url}/dashboard/")
    print(f"   Status: {response.status_code}")
    
    # 5. Verificar que el usuario esté logueado
    print("\n5️⃣ Verificando estado de autenticación...")
    response = session.get(f"{base_url}/dashboard/")
    if response.status_code == 200:
        print("   ✅ Usuario autenticado correctamente")
    else:
        print("   ❌ Error en autenticación")
    
    # 6. Hacer logout
    print("\n6️⃣ Haciendo logout...")
    response = session.get(f"{base_url}/auth/logout")
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    # 7. Intentar acceder al dashboard después del logout (debería redirigir a login)
    print("\n7️⃣ Intentando acceder al dashboard después del logout...")
    response = session.get(f"{base_url}/dashboard/")
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    print("\n" + "=" * 60)
    print("🎉 Prueba completada!")
    print("\n📋 Instrucciones para usar el logout:")
    print("1. Ve a: http://localhost:5000")
    print("2. Haz login con: admin / admin123")
    print("3. En la barra superior derecha, haz clic en tu nombre 'admin'")
    print("4. Selecciona 'Cerrar Sesión' del menú desplegable")
    print("5. Serás redirigido automáticamente al login")

if __name__ == '__main__':
    test_complete_auth()
