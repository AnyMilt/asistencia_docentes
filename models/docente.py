from app_simple import db

class Docente(db.Model):
    __tablename__ = 'docentes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    cedula = db.Column(db.String(10), unique=True, nullable=False, index=True)   # Nueva columna
    telefono = db.Column(db.String(15), nullable=False)                          # Nueva columna
    correo = db.Column(db.String(120), unique=True, nullable=False, index=True)  # Nueva columna
    jornada = db.Column(db.String(20), nullable=False, index=True)  # matutina o vespertina
    qr_code_path = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True, index=True)
    tipo = db.Column(db.String(20), nullable=False, index=True)  # DOCENTE, ADMINISTRATIVO, CONSERJE, DECE
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Relaciones
    asistencias = db.relationship('Asistencia', backref='docente', lazy=True, cascade='all, delete-orphan')
    licencias = db.relationship('Licencia', back_populates='docente', cascade='all, delete-orphan')

    # Índices compuestos para optimizar consultas frecuentes
    __table_args__ = (
        db.Index('idx_docente_activo_tipo', 'activo', 'tipo'),
        db.Index('idx_docente_jornada_activo', 'jornada', 'activo'),
        db.Index('idx_docente_nombre', 'nombre'),
    )

    def __repr__(self):
        return f'<Docente {self.nombre}>'

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'cedula': self.cedula,
            'telefono': self.telefono,
            'correo': self.correo,
            'jornada': self.jornada,
            'tipo': self.tipo,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }