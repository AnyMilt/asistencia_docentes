#!/usr/bin/env python3
"""
Script para probar el sistema de logout
"""

import requests
from requests.sessions import Session

def test_logout():
    """Prueba el sistema de login y logout"""
    base_url = "http://localhost:5000"
    
    # Crear sesión
    session = Session()
    
    print("Probando sistema de autenticación...")
    print("=" * 50)
    
    # 1. Acceder a la página principal (debería redirigir a login)
    print("1. Accediendo a página principal...")
    response = session.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    # 2. Acceder a la página de login
    print("\n2. Accediendo a página de login...")
    response = session.get(f"{base_url}/auth/login")
    print(f"   Status: {response.status_code}")
    
    # 3. Hacer login
    print("\n3. Haciendo login...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    response = session.post(f"{base_url}/auth/login", data=login_data)
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    # 4. Acceder al dashboard (debería funcionar)
    print("\n4. Accediendo al dashboard...")
    response = session.get(f"{base_url}/dashboard/")
    print(f"   Status: {response.status_code}")
    
    # 5. Hacer logout
    print("\n5. Haciendo logout...")
    response = session.get(f"{base_url}/auth/logout")
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    # 6. Intentar acceder al dashboard después del logout (debería redirigir a login)
    print("\n6. Intentando acceder al dashboard después del logout...")
    response = session.get(f"{base_url}/dashboard/")
    print(f"   Status: {response.status_code}")
    print(f"   Redirected to: {response.url}")
    
    print("\n" + "=" * 50)
    print("Prueba completada!")

if __name__ == '__main__':
    test_logout()

