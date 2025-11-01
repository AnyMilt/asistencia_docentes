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
        return f'<Asistencia Docente={self.docente_id} Fecha={self.fecha} Jornada={self.jornada}>'

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
            'longitud': self.longitud
        }

    @property
    def tiempo_trabajado(self):
        if self.hora_entrada and self.hora_salida:
            entrada = datetime.combine(self.fecha, self.hora_entrada)
            salida = datetime.combine(self.fecha, self.hora_salida)
            if salida < entrada:
                salida += timedelta(days=1)
            return (salida - entrada).total_seconds() / 3600
        return 0

    @property
    def es_tardanza(self):
        if not self.hora_entrada or not self.docente:
            return False
        if self.docente.jornada == 'matutina':
            return self.hora_entrada > time(7, 0, 0)
        elif self.docente.jornada == 'vespertina':
            return self.hora_entrada > time(13, 0, 0)
        return False