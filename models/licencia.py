from app_simple import db
from models.docente import Docente

class Licencia(db.Model):
    __tablename__ = 'licencias'

    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False, index=True)
    fecha_inicio = db.Column(db.Date, nullable=False, index=True)
    fecha_fin = db.Column(db.Date, nullable=False, index=True)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='pendiente', index=True)  # pendiente, aprobada, rechazada
    aprobado_por = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
   
    # Relación con docente
    docente = db.relationship('Docente', back_populates='licencias')

    # Índices compuestos para optimizar consultas frecuentes
    __table_args__ = (
        db.Index('idx_licencia_docente_estado', 'docente_id', 'estado'),
        db.Index('idx_licencia_fechas', 'fecha_inicio', 'fecha_fin'),
        db.Index('idx_licencia_estado_fecha', 'estado', 'fecha_inicio'),
        db.CheckConstraint('fecha_fin >= fecha_inicio', name='ck_licencia_fechas_validas'),
    )

    def __repr__(self):
        return f'<Licencia {self.docente_id} - {self.fecha_inicio} a {self.fecha_fin}>'

    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'docente_id': self.docente_id,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'motivo': self.motivo,
            'estado': self.estado,
            'aprobado_por': self.aprobado_por,
            'dias_licencia': self.dias_licencia
        }

    @property
    def dias_licencia(self):
        """Calcula los días de licencia"""
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return 0

    @property
    def esta_activa(self):
        """Verifica si la licencia está activa actualmente"""
        from datetime import date
        hoy = date.today()
        return (self.estado == 'aprobada' and 
                self.fecha_inicio <= hoy <= self.fecha_fin)

    @property
    def esta_por_vencer(self):
        """Verifica si la licencia está por vencer (en los próximos 3 días)"""
        from datetime import date, timedelta
        hoy = date.today()
        limite = hoy + timedelta(days=3)
        return (self.estado == 'aprobada' and 
                self.fecha_fin <= limite and 
                self.fecha_fin >= hoy)