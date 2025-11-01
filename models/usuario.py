from app_simple import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, talento_humano
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    ultimo_acceso = db.Column(db.DateTime)

    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'admin'

    def is_talento_humano(self):
        """Verifica si el usuario es de talento humano"""
        return self.rol == 'talento_humano'

    def __repr__(self):
        return f'<Usuario {self.username}>'