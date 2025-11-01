# 📚 Sistema de Asistencia Docente

Sistema web desarrollado en Flask para la gestión de asistencia de docentes y personal educativo mediante códigos QR.

## ✨ Características

- 🔐 **Sistema de autenticación** con roles (admin, talento humano)
- 📱 **Registro de asistencia** mediante códigos QR
- 👥 **Gestión de docentes** y personal educativo
- 📋 **Control de licencias** médicas y permisos
- 📊 **Dashboard** con métricas y estadísticas
- 📈 **Reportes** detallados de asistencia
- 🔄 **Actualizaciones periódicas** de la información
- 🛡️ **Seguridad mejorada** con validación de datos

## 🚀 Instalación Rápida

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd asistencia_docentes
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # En Windows:
   venv\Scripts\activate
   
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   # Copiar archivo de configuración
   copy env.example .env
   
   # Editar .env con tus configuraciones
   # IMPORTANTE: Cambia SECRET_KEY por una clave segura
   ```

5. **Inicializar base de datos**
   ```bash
   python init_db.py
   ```

6. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

7. **Acceder al sistema**
   - URL: http://localhost:5000
   - Usuario: `admin`
   - Contraseña: `admin123`

## 🔧 Configuración

### Variables de entorno (.env)

```env
# Configuración básica
SECRET_KEY=tu-clave-super-secreta-aqui
DATABASE_URL=sqlite:///asistencia.db
FLASK_ENV=development
FLASK_DEBUG=True

# Seguridad
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### Para producción

```env
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
DATABASE_URL=postgresql://usuario:password@localhost/asistencia_db
```

## 📖 Uso del Sistema

### 1. Gestión de Usuarios
- **Admin**: Puede crear usuarios, gestionar docentes y acceder a todos los módulos
- **Talento Humano**: Puede gestionar docentes, asistencia y reportes

### 2. Gestión de Docentes
- Registrar nuevos docentes con jornada (matutina/vespertina) y tipo
- Generar códigos QR individuales para cada docente
- Activar/desactivar docentes

### 3. Registro de Asistencia
- Los docentes escanean su código QR para registrar entrada/salida
- Sistema automático de detección de jornada
- Validación de horarios según jornada

### 4. Control de Licencias
- Registrar licencias médicas y permisos
- Estados: pendiente, aprobada, rechazada
- Alertas de licencias por vencer

### 5. Reportes
- Reporte de incumplimientos
- Estadísticas de asistencia diaria/mensual
- Ranking de docentes con más faltas/tardanzas

## 🏗️ Estructura del Proyecto

```
asistencia_docentes/
├── app.py                 # Aplicación principal
├── config.py             # Configuración
├── run.py               # Punto de entrada
├── init_db.py           # Script de inicialización
├── requirements.txt     # Dependencias
├── env.example         # Configuración de ejemplo
├── blueprints/         # Módulos de la aplicación
│   ├── auth/           # Autenticación
│   ├── docentes/       # Gestión de docentes
│   ├── asistencia/     # Registro de asistencia
│   ├── licencias/      # Control de licencias
│   ├── reportes/       # Generación de reportes
│   └── dashboard/      # Panel principal
├── models/             # Modelos de base de datos
├── templates/          # Plantillas HTML
├── static/            # Archivos estáticos
└── logs/              # Archivos de log
```

## 🔒 Seguridad

### Mejoras implementadas:
- ✅ Variables de entorno para configuración sensible
- ✅ Validación de entrada con Marshmallow
- ✅ Autenticación con Flask-Login
- ✅ Contraseñas hasheadas con Werkzeug
- ✅ Manejo robusto de errores
- ✅ Logging de acciones del usuario
- ✅ Protección contra inyección SQL (SQLAlchemy ORM)

### Recomendaciones adicionales:
- Cambiar contraseña por defecto del admin
- Usar HTTPS en producción
- Configurar firewall apropiadamente
- Realizar backups regulares de la base de datos

## 🐛 Solución de Problemas

### Error: "Module not found"
```bash
# Asegúrate de que el entorno virtual esté activado
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstala las dependencias
pip install -r requirements.txt
```

### Error: "Database is locked"
```bash
# Detén la aplicación y elimina el archivo de bloqueo
# Luego reinicia la aplicación
```

### Error: "Permission denied"
```bash
# En Linux/Mac, asegúrate de tener permisos de escritura
chmod +x run.py
chmod +x init_db.py
```

## 📞 Soporte

Para reportar problemas o solicitar nuevas funcionalidades:
1. Revisa la documentación
2. Verifica los logs en la carpeta `logs/`
3. Consulta los archivos de configuración

## 🔄 Actualizaciones Futuras

- [ ] Migraciones de base de datos con Flask-Migrate
- [ ] Tests unitarios automatizados
- [ ] API REST para integración externa
- [ ] Notificaciones por email
- [ ] Dashboard móvil responsive
- [ ] Exportación a Excel/CSV

## 📄 Licencia

Este proyecto está desarrollado para uso educativo e institucional.

---

**Desarrollado con ❤️ para la gestión eficiente de asistencia docente**
