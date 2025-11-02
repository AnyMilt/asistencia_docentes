from flask import Blueprint, render_template, send_file,request, flash, redirect, url_for, jsonify
from models.docente import Docente
from datetime import datetime, time, timedelta
import qrcode
import os
from app_simple import db
from models.asistencia import Asistencia
from io import BytesIO
from utils import get_local_ip, slugify
import json
from urllib.parse import urlparse, parse_qs


asistencia_bp = Blueprint('asistencia', __name__, template_folder='templates/asistencia')


def jornada_actual():
    hora = datetime.now().hour
    return 'matutina' if hora < 13 else 'vespertina'

def jornada_por_hora(hora):
    if time(7, 0) <= hora < time(13, 0):
        return 'matutina'
    elif time(13, 0) <= hora < time(18, 0):
        return 'vespertina'
    else:
        return 'fuera de jornada'

def obtener_jornada_valida(docente, hora):
    """
    Determina la jornada válida para el registro según la hora y la configuración del docente.
    Soporta jornada completa y días especiales.
    Returns:
        tuple: (es_valido, jornada, mensaje)
    """
    jornada_hora = jornada_por_hora(hora)
    fecha_actual = datetime.now().date()
    
    # Si la jornada del docente es 'completa', siempre retorna esa
    if docente.jornada == 'completa':
        return True, 'completa', "Jornada válida"
        
    # TODO: Aquí se podría agregar lógica para verificar si la fecha actual
    # es un día especial de jornada completa (por ejemplo, consultando una tabla)
    # if es_dia_jornada_completa(fecha_actual):
    #     return True, 'completa', "Jornada completa (día especial)"
    
    # Si es doble jornada, la jornada se determina por la hora
    if docente.jornada == 'doble':
        if jornada_hora == 'fuera de jornada':
            return False, None, "Hora fuera del horario de trabajo"
        return True, jornada_hora, "Jornada válida"
    
    # Para jornada única, debe coincidir con la jornada del docente
    if docente.jornada != jornada_hora:
        return False, None, f"El docente solo está asignado a jornada {docente.jornada}"
    
    return True, jornada_hora, "Jornada válida"

def validar_horario_registro(hora, jornada, tipo_registro='entrada'):
    """
    Valida si el horario es válido para una jornada y tipo de registro específicos.
    Permite registros tardíos y jornadas especiales de 8 horas.
    Args:
        hora: datetime.time - Hora a validar
        jornada: str - Jornada del docente ('matutina', 'vespertina', 'completa')
        tipo_registro: str - Tipo de registro ('entrada' o 'salida')
    Returns:
        tuple: (es_valido, mensaje, es_tardio)
    """
    HORARIOS = {
        'matutina': {
            'entrada': (time(7, 0), time(8, 30)),     # 7:00 a 8:30
            'salida': (time(12, 30), time(13, 30))    # 12:30 a 13:30
        },
        'vespertina': {
            'entrada': (time(13, 0), time(14, 30)),   # 13:00 a 14:30
            'salida': (time(17, 30), time(18, 30))    # 17:30 a 18:30
        },
        'completa': {
            'entrada': (time(7, 0), time(8, 30)),     # 7:00 a 8:30
            'salida': (time(15, 0), time(16, 0))      # 15:00 a 16:00 (8 horas después)
        }
    }
    
    LIMITES_TARDANZA = {
        'matutina': {
            'entrada': time(12, 0),     # Límite máximo entrada matutina
            'salida': time(14, 0)       # Límite máximo salida matutina
        },
        'vespertina': {
            'entrada': time(17, 0),     # Límite máximo entrada vespertina
            'salida': time(19, 0)       # Límite máximo salida vespertina
        },
        'completa': {
            'entrada': time(12, 0),     # Límite máximo entrada jornada completa
            'salida': time(17, 0)       # Límite máximo salida jornada completa
        }
    }
    
    if jornada not in HORARIOS:
        return False, "Jornada no válida", False
        
    horarios = HORARIOS[jornada]
    
    if tipo_registro not in horarios:
        return False, f"Tipo de registro '{tipo_registro}' no válido", False
        
    hora_min, hora_max = horarios[tipo_registro]
    
    # Si está dentro del horario normal
    if hora_min <= hora <= hora_max:
        return True, "Horario válido", False
        
    # Si es un registro tardío pero dentro del límite permitido
    limite_tardanza = LIMITES_TARDANZA[jornada][tipo_registro]
    if hora <= limite_tardanza:
        return True, f"⚠️ Registro tardío ({hora_min.strftime('%H:%M')} - {hora_max.strftime('%H:%M')})", True
        
    # Para jornada completa, permitir también horarios de jornada vespertina
    if jornada == 'completa' and tipo_registro == 'entrada':
        horario_vesp = HORARIOS['vespertina']['entrada']
        if horario_vesp[0] <= hora <= horario_vesp[1]:
            return True, "Horario válido (turno vespertino)", False
            
    return False, f"❌ {tipo_registro.title()} fuera de horario permitido ({hora_min.strftime('%H:%M')} - {hora_max.strftime('%H:%M')})", False
    
    

@asistencia_bp.route('/')
def index():
    return render_template('base.html', mensaje="Registro de asistencia")

@asistencia_bp.route('/generar_qr/<int:id>')
def generar_qr(id):
    docente = Docente.query.get_or_404(id)
    base_url = f"http://{get_local_ip()}:5000/asistencia/registrar"
    qr_data = f"{base_url}?docente={docente.id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

    

@asistencia_bp.route('/escanear', methods=['POST'])
def escanear_qr():
    codigo = request.form['codigo']  # Ej: "docente:12"
    if not codigo.startswith("docente:"):
        flash("❌ Código inválido.")
        return redirect(url_for('asistencia.index'))

    try:
        docente_id = int(codigo.split(":")[1])
        docente = Docente.query.get(docente_id)
        if not docente:
            flash("❌ Docente no encontrado.")
            return redirect(url_for('asistencia.index'))

        ahora = datetime.now()
        fecha = ahora.date()
        hora = ahora.time()

        # Validar jornada y horario
        es_valido_jornada, jornada_detectada, mensaje_jornada = obtener_jornada_valida(docente, hora)
        if not es_valido_jornada:
            flash(f"❌ Error: {mensaje_jornada}", "danger")
            return redirect(url_for('asistencia.index'))
            
        es_valido_horario, mensaje_horario = validar_horario_registro(hora, jornada_detectada)
        if not es_valido_horario:
            flash(f"❌ Error: {mensaje_horario}", "danger")
            return redirect(url_for('asistencia.index'))

        nueva_asistencia = Asistencia(
            docente_id=docente.id,
            fecha=fecha,
            hora_entrada=hora,
            jornada=jornada_detectada
        )
        db.session.add(nueva_asistencia)
        db.session.commit()
        flash(f"✅ Asistencia registrada para {docente.nombre} - Jornada: {jornada_detectada}.", "success")

    except Exception as e:
        flash(f"❌ Error al procesar el código: {str(e)}", "danger")

    return redirect(url_for('asistencia.index'))

@asistencia_bp.route('/sincronizar', methods=['GET'])
def sincronizar_asistencia():
    docente_id = request.args.get('docente')
    fecha_str = request.args.get('fecha')  # Ej: "2025-10-23"
    hora_str = request.args.get('hora')    # Ej: "12:05:00"

    if not docente_id or not fecha_str or not hora_str:
        return "❌ Parámetros incompletos", 400

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora = datetime.strptime(hora_str, "%H:%M:%S").time()
    except ValueError:
        return "❌ Formato de fecha/hora inválido", 400

    docente = Docente.query.get(int(docente_id))
    if not docente:
        return "❌ Docente no encontrado", 404

    # Validar jornada y horario
    es_valido_jornada, jornada_detectada, mensaje_jornada = obtener_jornada_valida(docente, hora)
    if not es_valido_jornada:
        return f"❌ Error: {mensaje_jornada}", 400
        
    es_valido_horario, mensaje_horario = validar_horario_registro(hora, jornada_detectada)
    if not es_valido_horario:
        return f"❌ Error: {mensaje_horario}", 400

    nueva_asistencia = Asistencia(
        docente_id=docente.id, 
        fecha=fecha,
        hora_entrada=hora,
        jornada=jornada_detectada
    )
    db.session.add(nueva_asistencia)
    db.session.commit()

    return f"✅ Asistencia sincronizada para {docente.nombre} a las {hora.strftime('%H:%M:%S')} - Jornada: {jornada_detectada}", 200

def mostrar_mensaje(tipo, nombre, hora, fecha, jornada):
    colores = {
        "entrada": "#e0f7fa",
        "salida": "#e8f5e9",
        "completo": "#fff3e0"
    }
    emojis = {
        "entrada": "✅",
        "salida": "✅",
        "completo": "⚠️"
    }
    fondo = colores[tipo]
    emoji = emojis[tipo]
    hora_html = f"<p>🕒 {hora.strftime('%H:%M:%S')}</p>" if hora else ""
    jornada_html = f"<p>🕓 Jornada detectada: <strong>{jornada}</strong></p>"

    

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background-color: {fondo};
                color: #333;
                text-align: center;
                padding: 2em;
            }}
            .card {{
                background: white;
                border-radius: 12px;
                padding: 1.5em;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                max-width: 400px;
                margin: auto;
            }}
            h1 {{
                font-size: 1.8em;
                margin-bottom: 0.5em;
            }}
            p {{
                font-size: 1.2em;
                margin: 0.5em 0;
            }}
            .emoji {{
                font-size: 2em;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="emoji">{emoji}</div>
            <h1>{tipo.capitalize()} registrada</h1>
            <p><strong>{nombre}</strong></p>
            {hora_html}
            <p>📅 {fecha.strftime('%d/%m/%Y')}</p>
            {jornada_html}
        </div>
    </body>
    </html>
    """

# @asistencia_bp.route('/registrar', methods=['GET', 'POST'])
# def registrar_asistencia():
#     # Manejar parámetros tanto de GET como de POST
#     if request.method == 'GET':
#         docente_id = request.args.get('docente')
#         fecha_str = request.args.get('fecha')
#         hora_str = request.args.get('hora')
#         # En GET asumimos que es entrada por defecto
#         tipo = 'entrada'
#         # La jornada se detectará automáticamente
#         jornada = None
#     else:  # POST
#         docente_id = request.form.get('docente_id')
#         fecha_str = request.form.get('fecha')
#         hora_str = request.form.get('hora')
#         jornada = request.form.get('jornada')
#         tipo = request.form.get('tipo')  # 'entrada' o 'salida'

#     if not all([docente_id, fecha_str, hora_str]):
#         flash('❌ Todos los campos son requeridos', 'danger')
#         return redirect(url_for('asistencia.index'))

#     try:
#         print(f"DEBUG - Parametros recibidos: docente={docente_id}, fecha={fecha_str}, hora={hora_str}")
        
#         # Validar y obtener docente
#         try:
#             docente_id = int(docente_id)
#             docente = Docente.query.get(docente_id)
#             print(f"DEBUG - Docente encontrado: {docente.nombre if docente else 'No encontrado'}")
#         except (ValueError, TypeError) as e:
#             print(f"DEBUG - Error al convertir docente_id: {str(e)}")
#             mensaje_error = '❌ ID de docente inválido'
#             return (mensaje_error, 400) if request.method == 'GET' else (flash(mensaje_error, 'danger'), redirect(url_for('asistencia.index')))

#         if not docente:
#             mensaje_error = '❌ Docente no encontrado'
#             return (mensaje_error, 404) if request.method == 'GET' else (flash(mensaje_error, 'danger'), redirect(url_for('asistencia.index')))

#         # Validar y parsear fecha/hora
#         try:
#             fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
#             print(f"DEBUG - Fecha parseada: {fecha}")
            
#             if request.method == 'GET':
#                 try:
#                     hora = datetime.strptime(hora_str, '%H:%M:%S').time()
#                 except ValueError as e1:
#                     print(f"DEBUG - Error formato HH:MM:SS: {str(e1)}")
#                     try:
#                         # Intentar con formato alternativo si falla
#                         hora = datetime.strptime(hora_str, '%H:%M').time()
#                     except ValueError as e2:
#                         print(f"DEBUG - Error formato HH:MM: {str(e2)}")
#                         raise
#             else:
#                 hora = datetime.strptime(hora_str, '%H:%M').time()
#             print(f"DEBUG - Hora parseada: {hora}")
#         except ValueError as e:
#             mensaje_error = f'❌ Formato de fecha/hora inválido: {str(e)}'
#             return (mensaje_error, 400) if request.method == 'GET' else (flash(mensaje_error, 'danger'), redirect(url_for('asistencia.index')))

#         # Validar jornada
#         es_valido_jornada, jornada_detectada, mensaje_jornada = obtener_jornada_valida(docente, hora)
#         print(f"DEBUG - Validación jornada: válido={es_valido_jornada}, jornada={jornada_detectada}, mensaje={mensaje_jornada}")
        
#         if not es_valido_jornada:
#             mensaje_error = f"❌ {mensaje_jornada}"
#             return (mensaje_error, 400) if request.method == 'GET' else (flash(mensaje_error, "danger"), redirect(url_for('asistencia.index')))

#         # En POST validar que la jornada coincida con la detectada
#         if request.method == 'POST' and jornada and jornada != jornada_detectada:
#             mensaje_error = "❌ La jornada seleccionada no coincide con el horario del docente"
#             flash(mensaje_error, "danger")
#             return redirect(url_for('asistencia.index'))

#         # Verificar si ya existe una asistencia para determinar si es entrada o salida
#         asistencia = Asistencia.query.filter_by(
#             docente_id=docente_id,
#             fecha=fecha,
#             jornada=jornada_detectada
#         ).first()

#         # Determinar si es entrada o salida
#         tipo_registro = 'entrada'
#         if asistencia and asistencia.hora_entrada and not asistencia.hora_salida:
#             tipo_registro = 'salida'
        
#         print(f"DEBUG - Tipo de registro determinado: {tipo_registro}")

#         # Validar horario según el tipo de registro
#         es_valido_horario, mensaje_horario, es_tardio = validar_horario_registro(hora, jornada_detectada, tipo_registro)

#         print(f"DEBUG - Validación horario: válido={es_valido_horario}, mensaje={mensaje_horario}, tardío={es_tardio}")
        
#         if not es_valido_horario:
#             mensaje_error = mensaje_horario  # El mensaje ya incluye el emoji
#             return (mensaje_error, 400) if request.method == 'GET' else (flash(mensaje_error, "danger"), redirect(url_for('asistencia.index')))

#         # Verificar el estado actual y actualizar según corresponda
#         if tipo_registro == 'entrada':
#             if asistencia and asistencia.hora_entrada:
#                 mensaje_error = f'❌ Ya existe un registro de entrada para {docente.nombre} en esta fecha y jornada ({jornada_detectada})'
#                 return (mensaje_error, 400) if request.method == 'GET' else (flash(mensaje_error, 'danger'), redirect(url_for('asistencia.index')))

#             # Crear nuevo registro o actualizar existente
#             if not asistencia:
#                 asistencia = Asistencia(
#                     docente_id=docente_id,
#                     fecha=fecha,
#                     jornada=jornada_detectada
#                 )
            
#             asistencia.hora_entrada = hora
#             db.session.add(asistencia)
#             db.session.commit()

#             mensaje_exito = f"✅ Entrada registrada para {docente.nombre} - Jornada: {jornada_detectada} - Hora: {hora.strftime('%H:%M:%S')}"
#             if request.method == 'GET':
#                 return mensaje_exito, 200
                
#             flash(mensaje_exito, "success")
#             return mostrar_mensaje("entrada", docente.nombre, hora, fecha, jornada_detectada)

#         elif tipo_registro == 'salida':
#             if not asistencia or not asistencia.hora_entrada:
#                 mensaje_error = f'❌ No existe un registro de entrada para {docente.nombre} en esta fecha y jornada ({jornada_detectada})'
#                 return (mensaje_error, 400) if request.method == 'GET' else (flash(mensaje_error, 'danger'), redirect(url_for('asistencia.index')))

#             # Registrar la salida
#             asistencia.hora_salida = hora
#             db.session.commit()

#             # Preparar mensaje según si es tardío o no
#             estado = "⚠️ Salida tardía" if es_tardio else "✅ Salida registrada"
#             mensaje_exito = f"{estado} para {docente.nombre} - Jornada: {jornada_detectada} - Hora: {hora.strftime('%H:%M:%S')}"
            
#             if request.method == 'GET':
#                 return mensaje_exito, 200
                
#             flash(mensaje_exito, "success")
#             return mostrar_mensaje("salida", docente.nombre, hora, fecha, jornada_detectada)

#     except Exception as e:
#         mensaje_error = f'❌ Error: {str(e)}'
#         return (mensaje_error, 500) if request.method == 'GET' else (flash(mensaje_error, 'danger'), redirect(url_for('asistencia.index')))

###aqui va la nueva función registrar_asistencia con los cambios solicitados###
def calcular_incidencias(jornada: str, hora_entrada: time, hora_salida: time):
    """
    Calcula minutos de atraso y salida temprana según la jornada.
    - Matutina: 07:00 a 13:00
    - Vespertina: 13:00 a 19:00
    - Completa: salida = entrada + 6 horas
    """
    hoy = datetime.today().date()
    atraso = 0
    salida_temprana = 0

    if jornada == "matutina":
        inicio, fin = time(7, 0), time(13, 0)
    elif jornada == "vespertina":
        inicio, fin = time(12, 0), time(18, 0)
    elif jornada == "completa":
        if not hora_entrada:
            return 0, 0
        entrada_dt = datetime.combine(hoy, hora_entrada)
        salida_esperada = entrada_dt + timedelta(hours=6)
        if hora_salida:
            salida_dt = datetime.combine(hoy, hora_salida)
            if salida_dt < salida_esperada:
                salida_temprana = int((salida_esperada - salida_dt).total_seconds() // 60)
        return 0, salida_temprana
    else:
        return 0, 0

    # Para matutina/vespertina
    if hora_entrada:
        entrada_dt = datetime.combine(hoy, hora_entrada)
        inicio_dt = datetime.combine(hoy, inicio)
        if entrada_dt > inicio_dt:
            atraso = int((entrada_dt - inicio_dt).total_seconds() // 60)

    if hora_salida:
        salida_dt = datetime.combine(hoy, hora_salida)
        fin_dt = datetime.combine(hoy, fin)
        if salida_dt < fin_dt:
            salida_temprana = int((fin_dt - salida_dt).total_seconds() // 60)

    return atraso, salida_temprana

@asistencia_bp.route('/registrar', methods=['POST'])
def registrar_asistencia_post():
    try:
        data = request.get_json()

        if not data:
            return "❌ No se recibió JSON válido", 400

        docente_id = data.get('idDocente')
        device_id = data.get('idDispositivo')
        latitud = data.get('lat')
        longitud = data.get('lng')
        tipo = data.get('tipo', 'Entrada')
        fecha_hora_str = data.get('fecha')

        if not all([docente_id, fecha_hora_str]):
            return "❌ Faltan parámetros obligatorios (idDocente, fecha)", 400

        docente = Docente.query.get(int(docente_id))
        if not docente:
            return "❌ Docente no encontrado", 404

        # Parsear fecha y hora
        fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M:%S")
        fecha = fecha_hora.date()
        hora = fecha_hora.time()

        # Detectar jornada
        if time(6, 0) <= hora <= time(12, 59):
            jornada_detectada = "matutina"
        elif time(13, 0) <= hora <= time(19, 59):
            jornada_detectada = "vespertina"
        else:
            jornada_detectada = "completa"

        asistencia = Asistencia.query.filter_by(
            docente_id=docente.id,
            fecha=fecha,
            jornada=jornada_detectada
        ).first()

        if tipo.lower() == "entrada" or not asistencia:
            # Registrar entrada
            if not asistencia:
                asistencia = Asistencia(
                    docente_id=docente.id,
                    fecha=fecha,
                    jornada=jornada_detectada
                )
                db.session.add(asistencia)

            asistencia.hora_entrada = hora
            asistencia.device_id = device_id
            asistencia.latitud = float(latitud) if latitud else None
            asistencia.longitud = float(longitud) if longitud else None
            asistencia.fecha_creacion = datetime.now()
            asistencia.fecha_actualizacion = datetime.now()

            db.session.commit()
            return jsonify({
                "status": "ok",
                "mensaje": f"✅ Entrada registrada para {docente.nombre}",
                "jornada": jornada_detectada
            }), 200

        elif tipo.lower() == "salida":
            # Actualizar salida
            asistencia.hora_salida = hora
            asistencia.device_id = device_id or asistencia.device_id
            asistencia.latitud = float(latitud) if latitud else asistencia.latitud
            asistencia.longitud = float(longitud) if longitud else asistencia.longitud
            asistencia.fecha_actualizacion = datetime.now()

            atraso, salida_temprana = calcular_incidencias(
                jornada_detectada,
                asistencia.hora_entrada,
                asistencia.hora_salida
            )

            db.session.commit()
            return jsonify({
                "status": "ok",
                "mensaje": f"✅ Salida registrada para {docente.nombre}",
                "jornada": jornada_detectada,
                "atraso": atraso,
                "salida_temprana": salida_temprana
            }), 200

        else:
            return "⚠️ Tipo de registro desconocido (Entrada/Salida)", 400

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500



##final de la nueva función registrar_asistencia##



@asistencia_bp.route('/asistencia/reportes')
def reportes():
    return render_template('asistencia/asistencia_reportes.html')


@asistencia_bp.route('/importar_json', methods=['POST'], endpoint='importar_json')
def importar_json():
    archivo = request.files.get('archivo_json')
    if not archivo or not archivo.filename.endswith('.json'):
        flash('❌ Archivo inválido. Debe ser un archivo .json.', 'danger')
        return redirect(url_for('asistencia.index'))

    try:
        contenido = json.load(archivo)
        if not isinstance(contenido, list):
            flash('❌ Formato inválido. El archivo debe contener una lista de registros.', 'danger')
            return redirect(url_for('asistencia.index'))

        registros_importados = 0
        errores = []

        for item in contenido:
            if not isinstance(item, dict) or 'UrlEscaneo' not in item:
                continue

            try:
                # Extraer y validar parámetros desde la URL
                partes = urlparse(item['UrlEscaneo'])
                qs = parse_qs(partes.query)
                
                try:
                    docente_id = int(qs.get('docente', [0])[0])
                except ValueError:
                    errores.append(f"ID de docente inválido en URL: {item['UrlEscaneo']}")
                    continue

                fecha_str = qs.get('fecha', [''])[0]
                hora_str = qs.get('hora', [''])[0]

                if not all([docente_id, fecha_str, hora_str]):
                    errores.append(f"Faltan parámetros requeridos en URL: {item['UrlEscaneo']}")
                    continue

                docente = Docente.query.get(docente_id)
                if not docente:
                    errores.append(f"Docente no encontrado con ID {docente_id}")
                    continue

                try:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    hora = datetime.strptime(hora_str, '%H:%M:%S').time()
                except ValueError as e:
                    errores.append(f"Formato de fecha/hora inválido: {str(e)}")
                    continue

                # Validar jornada y horario
                es_valido_jornada, jornada_detectada, mensaje_jornada = obtener_jornada_valida(docente, hora)
                if not es_valido_jornada:
                    errores.append(f"Error en jornada para {docente.nombre}: {mensaje_jornada}")
                    continue

                es_valido_horario, mensaje_horario = validar_horario_registro(hora, jornada_detectada)
                if not es_valido_horario:
                    errores.append(f"Error en horario para {docente.nombre}: {mensaje_horario}")
                    continue

                # Buscar o crear registro para la jornada específica
                registro = Asistencia.query.filter_by(
                    docente_id=docente.id, 
                    fecha=fecha,
                    jornada=jornada_detectada
                ).first()

                if not registro:
                    registro = Asistencia(
                        docente_id=docente.id, 
                        fecha=fecha,
                        jornada=jornada_detectada
                    )
                    registro.hora_entrada = hora
                elif not registro.hora_entrada:
                    registro.hora_entrada = hora
                elif not registro.hora_salida:
                    registro.hora_salida = hora
                else:
                    errores.append(f"Ya existe registro completo para {docente.nombre} en {fecha_str}")
                    continue

                db.session.add(registro)
                registros_importados += 1

            except Exception as e:
                errores.append(f"Error procesando registro: {str(e)}")
                continue

        db.session.commit()
        
        # Mostrar resumen de la importación
        if registros_importados > 0:
            flash(f'✅ {registros_importados} registros importados correctamente.', 'success')
        
        if errores:
            flash(f'⚠️ Se encontraron {len(errores)} errores durante la importación:', 'warning')
            for error in errores[:5]:  # Mostrar solo los primeros 5 errores
                flash(f'• {error}', 'warning')
            if len(errores) > 5:
                flash(f'• ... y {len(errores) - 5} errores más.', 'warning')

    except json.JSONDecodeError:
        flash('❌ Error al decodificar el archivo JSON. Verifique el formato.', 'danger')
    except Exception as e:
        flash(f'❌ Error al procesar el archivo: {str(e)}', 'danger')

    return redirect(url_for('asistencia.index'))