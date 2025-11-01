import socket
import re
import unicodedata

from datetime import datetime, time, timedelta


def slugify(text: str) -> str:
    """Genera un slug ASCII seguro para usar como id de fila.

    Convierte a minúsculas, normaliza diacríticos y reemplaza
    caracteres no alfanuméricos por guiones.
    """
    if not text:
        return ""
    text = str(text)
    # Normalizar y eliminar diacríticos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    # Reemplazar cualquier grupo de caracteres no alfanuméricos por '-'
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def evaluar_asistencia(docente, entrada, salida):
    if docente.jornada == 'matutina':
        entrada_tarde = entrada > time(7, 0) if entrada else True
        salida_temprano = salida < time(13, 0) if salida else True
    elif docente.jornada == 'vespertina':
        entrada_tarde = entrada > time(13, 0) if entrada else True
        salida_temprano = salida < time(18, 0) if salida else True
    else:
        entrada_tarde = salida_temprano = False
    return entrada_tarde, salida_temprano

def calcular_tiempo_acumulado(entrada, salida):
    if entrada and salida:
        dt_entrada = datetime.combine(datetime.today(), entrada)
        dt_salida = datetime.combine(datetime.today(), salida)
        return dt_salida - dt_entrada
    return timedelta()  # Retorna cero si falta entrada o salida

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip