import logging
import traceback
from functools import wraps
from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user
from datetime import datetime
import os

# Configurar logging
def setup_logging(app):
    """Configura el sistema de logging"""
    if not app.debug:
        # Crear directorio de logs si no existe
        log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar archivo de log
        log_file = os.path.join(log_dir, 'app.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Configurar logger específico para la aplicación
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicación iniciada')

def log_error(error, request_data=None):
    """Registra errores en el log"""
    logger = logging.getLogger(__name__)
    
    error_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'error': str(error),
        'type': type(error).__name__,
        'traceback': traceback.format_exc(),
        'user': current_user.username if current_user.is_authenticated else 'anonymous',
        'url': request.url if request else None,
        'method': request.method if request else None,
        'ip': request.remote_addr if request else None
    }
    
    logger.error(f"Error occurred: {error_info}")
    return error_info

def handle_errors(f):
    """Decorador para manejo de errores en rutas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_info = log_error(e, request)
            
            # Si es una petición AJAX, devolver JSON
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'error': True,
                    'message': 'Ha ocurrido un error interno',
                    'code': 500
                }), 500
            
            # Para peticiones normales, mostrar página de error
            flash('Ha ocurrido un error inesperado. Por favor intenta nuevamente.', 'danger')
            return redirect(url_for('dashboard.index'))
    
    return decorated_function

def handle_database_errors(f):
    """Decorador específico para errores de base de datos"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_info = log_error(e, request)
            
            # Errores específicos de base de datos
            if 'UNIQUE constraint failed' in str(e):
                flash('El registro ya existe en la base de datos', 'warning')
            elif 'FOREIGN KEY constraint failed' in str(e):
                flash('No se puede realizar la operación debido a dependencias', 'warning')
            elif 'NOT NULL constraint failed' in str(e):
                flash('Faltan campos obligatorios', 'warning')
            else:
                flash('Error de base de datos. Contacta al administrador.', 'danger')
            
            return redirect(request.referrer or url_for('dashboard.index'))
    
    return decorated_function

def validate_required_fields(required_fields):
    """Decorador para validar campos obligatorios"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_fields = []
            
            for field in required_fields:
                if not request.form.get(field) and not request.args.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                flash(f'Faltan campos obligatorios: {", ".join(missing_fields)}', 'warning')
                return redirect(request.referrer or url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def talento_humano_required(f):
    """Decorador para requerir permisos de talento humano o admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth.login'))
        
        if not (current_user.is_admin() or current_user.is_talento_humano()):
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Manejo de errores globales
def register_error_handlers(app):
    """Registra manejadores de errores globales"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        log_error(error, request)
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

def log_user_action(action, details=None):
    """Registra acciones del usuario"""
    logger = logging.getLogger('user_actions')
    
    action_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'user': current_user.username if current_user.is_authenticated else 'anonymous',
        'action': action,
        'details': details,
        'ip': request.remote_addr if request else None,
        'url': request.url if request else None
    }
    
    logger.info(f"User action: {action_info}")
