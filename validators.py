from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, date
import re

class DocenteSchema(Schema):
    nombre = fields.Str(
        required=True, 
        validate=[
            validate.Length(min=2, max=100),
            validate.Regexp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', error='El nombre solo puede contener letras y espacios')
        ]
    )
    jornada = fields.Str(
        required=True,
        validate=validate.OneOf(['matutina', 'vespertina'], error='Jornada debe ser matutina o vespertina')
    )
    tipo = fields.Str(
        required=True,
        validate=validate.OneOf(['DOCENTE', 'ADMINISTRATIVO', 'CONSERJE', 'DECE'], 
                              error='Tipo debe ser DOCENTE, ADMINISTRATIVO, CONSERJE o DECE')
    )

class LicenciaSchema(Schema):
    docente_id = fields.Int(required=True, validate=validate.Range(min=1))
    fecha_inicio = fields.Date(required=True)
    fecha_fin = fields.Date(required=True)
    motivo = fields.Str(validate=validate.Length(max=200))
    estado = fields.Str(validate=validate.OneOf(['pendiente', 'aprobada', 'rechazada']))
    
    def validate_fecha_fin(self, value, **kwargs):
        if 'fecha_inicio' in kwargs and value < kwargs['fecha_inicio']:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')

class AsistenciaSchema(Schema):
    docente_id = fields.Int(required=True, validate=validate.Range(min=1))
    fecha = fields.Date(required=True)
    hora_entrada = fields.Time()
    hora_salida = fields.Time()
    estado = fields.Str(validate=validate.OneOf(['presente', 'ausente', 'pendiente']))

class UsuarioSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-zA-Z0-9_]+$', error='Username solo puede contener letras, números y guiones bajos')
        ]
    )
    password = fields.Str(required=True, validate=validate.Length(min=6))
    rol = fields.Str(validate=validate.OneOf(['admin', 'talento_humano']))

def validate_date_range(fecha_inicio, fecha_fin):
    """Valida que el rango de fechas sea válido"""
    if fecha_fin < fecha_inicio:
        raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')
    
    # No permitir fechas futuras para licencias
    hoy = date.today()
    if fecha_inicio > hoy:
        raise ValidationError('No se pueden crear licencias con fechas futuras')

def sanitize_input(text):
    """Sanitiza entrada de texto para prevenir XSS"""
    if not text:
        return text
    
    # Remover caracteres peligrosos
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', 'script', 'javascript']
    text = str(text)
    
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def validate_qr_data(qr_data):
    """Valida el formato de datos QR"""
    if not qr_data:
        raise ValidationError('Datos QR vacíos')
    
    # Verificar formato básico
    if not isinstance(qr_data, str):
        raise ValidationError('Datos QR deben ser texto')
    
    # Verificar longitud máxima
    if len(qr_data) > 1000:
        raise ValidationError('Datos QR demasiado largos')
    
    return True
