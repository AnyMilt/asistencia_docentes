from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from error_handlers import setup_logging, register_error_handlers

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)
    
    # Configurar logging
    setup_logging(app)
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.usuario import Usuario
        return Usuario.query.get(int(user_id))

    # Registrar manejadores de errores
    register_error_handlers(app)

    # Importar y registrar Blueprints
    from blueprints.docentes import docentes_bp
    from blueprints.asistencia import asistencia_bp
    from blueprints.licencias import licencias_bp
    from blueprints.reportes import reportes_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.auth import auth_bp

    app.register_blueprint(docentes_bp, url_prefix='/docentes')
    app.register_blueprint(asistencia_bp, url_prefix='/asistencia')
    app.register_blueprint(licencias_bp, url_prefix='/licencias')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    @app.route('/')
    def inicio():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/ping')
    def ping():
        return 'pong', 200

    return app
