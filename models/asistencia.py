from app_simple import db
from datetime import datetime, timedelta, time
from sqlalchemy import Enum

class Asistencia(db.Model):
    __tablename__ = 'asistencias'

    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=False, index=True)

    fecha = db.Column(db.Date, nullable=False, index=True)
    hora_entrada = db.Column(db.Time, index=True)
    hora_salida = db.Column(db.Time)

    estado = db.Column(
        Enum("presente", "ausente", "pendiente", name="estado_asistencia"),
        default="pendiente",
        index=True
    )

    jornada = db.Column(db.String(20), nullable=False, index=True)

    # Nuevos campos
    device_id = db.Column(db.String(100), nullable=True, index=True)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

    # 🆕 Nuevo campo: modo (presencial o virtual)
    modo = db.Column(db.String(20), default="presencial", nullable=False, index=True)

    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    __table_args__ = (
        db.Index('idx_asistencia_docente_fecha', 'docente_id', 'fecha'),
        db.Index('idx_asistencia_fecha_estado', 'fecha', 'estado'),
        db.Index('idx_asistencia_docente_fecha_entrada', 'docente_id', 'fecha', 'hora_entrada'),
        db.Index('idx_asistencia_jornada', 'jornada'),
        db.UniqueConstraint('docente_id', 'fecha', 'jornada', name='uq_docente_fecha_jornada'),
    )

    def __repr__(self):
        return f'<Asistencia Docente={self.docente_id} Fecha={self.fecha} Jornada={self.jornada} Modo={self.modo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'docente_id': self.docente_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'hora_entrada': self.hora_entrada.isoformat() if self.hora_entrada else None,
            'hora_salida': self.hora_salida.isoformat() if self.hora_salida else None,
            'estado': self.estado,
            'jornada': self.jornada,
            'device_id': self.device_id,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'modo': self.modo,  # <- nuevo campo
        }
