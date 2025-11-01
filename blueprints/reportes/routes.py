from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from models.asistencia import Asistencia
from models.docente import Docente
from utils import evaluar_asistencia, calcular_tiempo_acumulado, slugify
from datetime import datetime, timedelta, date
from app_simple import db
from models.licencia import Licencia
from sqlalchemy import extract
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

reportes_bp = Blueprint('reportes', __name__, template_folder='templates/reportes')

@reportes_bp.route('/')
def index():
    return render_template('base.html', mensaje="Reportes semanales y mensuales")



@reportes_bp.route('/incumplimientos')
def reporte_incumplimientos():
    jornada = request.args.get('jornada')
    desde_str = request.args.get('desde')
    hasta_str = request.args.get('hasta')
    docentes_ids = request.args.getlist('docente')

    hoy = datetime.now().date()
    try:
        desde = datetime.strptime(desde_str, '%Y-%m-%d').date() if desde_str else hoy
        hasta = datetime.strptime(hasta_str, '%Y-%m-%d').date() if hasta_str else hoy
    except ValueError:
        return "Formato de fecha inválido", 400

    query = Asistencia.query.join(Docente).filter(Asistencia.fecha.between(desde, hasta))
    if jornada:
        query = query.filter(Docente.jornada == jornada)
    if docentes_ids:
        query = query.filter(Docente.id.in_(docentes_ids))

    registros = query.order_by(Asistencia.fecha, Asistencia.hora_entrada).all()

    resumen_docentes = defaultdict(lambda: {
        'nombre': '',
        'jornada': '',
        'entrada_tarde': 0,
        'salida_temprano': 0,
        'incumplimientos': 0,
        'tiempo_total': timedelta()
    })

    for a in registros:
        entrada_tarde, salida_temprano = evaluar_asistencia(a.docente, a.hora_entrada, a.hora_salida)
        tiempo_acumulado = calcular_tiempo_acumulado(a.hora_entrada, a.hora_salida)

        if entrada_tarde or salida_temprano:
            d = resumen_docentes[a.docente.id]
            d['nombre'] = a.docente.nombre
            d['jornada'] = a.docente.jornada
            d['entrada_tarde'] += int(entrada_tarde)
            d['salida_temprano'] += int(salida_temprano)
            d['incumplimientos'] += 1
            d['tiempo_total'] += tiempo_acumulado or timedelta()

    resumen_lista = list(resumen_docentes.values())
    todos_los_docentes = Docente.query.order_by(Docente.nombre).all()

    return render_template(
                'reportes/reporte_incumplimientos.html',
                resumen=resumen_lista,
                todos_los_docentes=todos_los_docentes,
                fecha=hoy
                    )

# 🟦 2. Asistencia diaria
@reportes_bp.route('/asistencia-diaria')
def reporte_asistencia_diaria():
    fecha = request.args.get('fecha', '').strip()
    docente = request.args.get('docente', '').strip()

    query = Asistencia.query.join(Docente)

    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            flash("La fecha ingresada no tiene un formato válido.", "danger")
            return redirect(url_for('reportes.reporte_asistencia_diaria'))
    else:
        fecha_obj = date.today()
        fecha = fecha_obj.strftime('%Y-%m-%d')

    query = query.filter(Asistencia.fecha == fecha_obj)

    if docente:
        query = query.filter(Docente.nombre.ilike(f'%{docente}%'))

    resultados = query.all()

    # Procesar los resultados y formatear fechas
    for r in resultados:
        try:
            fecha_iso = r.fecha.strftime('%Y-%m-%d') if hasattr(r, 'fecha') and r.fecha else ''
        except Exception:
            fecha_iso = ''
        r.fila_id = f"{slugify(r.docente.nombre)}-{fecha_iso}"
    return render_template('reportes/asistencia_diaria.html',
        resultados=resultados,
        fecha=fecha,
        docente=docente
    )

# 🟨 3. Faltas injustificadas

@reportes_bp.route('/faltas')
def reporte_faltas():
    fecha = request.args.get('fecha')
    fecha_obj = None
    faltantes = []

    if fecha:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

        # Docentes con asistencia registrada ese día
        presentes_ids = db.session.query(Asistencia.docente_id).filter_by(fecha=fecha_obj).distinct()

        # Docentes con licencia activa ese día
        con_licencia_ids = db.session.query(Licencia.docente_id).filter(
            Licencia.estado == 'aprobada',
            Licencia.fecha_inicio <= fecha_obj,
            Licencia.fecha_fin >= fecha_obj
        ).distinct()

        # Docentes activos sin asistencia ni licencia
        faltantes = Docente.query.filter(
            Docente.activo == True,
            ~Docente.id.in_(presentes_ids),
            ~Docente.id.in_(con_licencia_ids)
        ).all()

    return render_template('reportes/faltas.html', faltantes=faltantes, fecha=fecha_obj)


# 🟩 4. Resumen mensual

@reportes_bp.route('/resumen-mensual')
def reporte_resumen_mensual():
    # Parámetros recibidos
    mes_str = request.args.get('mes', '').strip()  # formato esperado: YYYY-MM
    docente_filtro = request.args.get('docente', '').strip()

    # Validación de mes
    try:
        if mes_str:
            año, mes_num = map(int, mes_str.split('-'))
            inicio_mes = date(año, mes_num, 1)
        else:
            hoy = date.today()
            año, mes_num = hoy.year, hoy.month
            inicio_mes = date(año, mes_num, 1)
            mes_str = inicio_mes.strftime('%Y-%m')
    except ValueError:
        flash("Formato de mes inválido. Usa YYYY-MM.", "danger")
        return redirect(url_for('reportes.reporte_resumen_mensual'))

    # Consulta base
    query = Asistencia.query.join(Docente).filter(
        extract('year', Asistencia.fecha) == año,
        extract('month', Asistencia.fecha) == mes_num
    )

    if docente_filtro:
        query = query.filter(Docente.nombre.ilike(f'%{docente_filtro}%'))

    registros = query.all()

    # Construcción del resumen
    resumen = {}
    hora_referencia = datetime.strptime('08:00', '%H:%M').time()

    for r in registros:
        nombre = r.docente.nombre
        if nombre not in resumen:
            resumen[nombre] = {
                'asistencias': 0,
                'ausentes': 0,
                'pendientes': 0,
                'atrasos': 0
            }

        if r.estado == 'presente':
            resumen[nombre]['asistencias'] += 1
            if r.hora_entrada and r.hora_entrada > hora_referencia:
                resumen[nombre]['atrasos'] += 1
        elif r.estado == 'ausente':
            resumen[nombre]['ausentes'] += 1
        elif r.estado == 'pendiente':
            resumen[nombre]['pendientes'] += 1

    return render_template('reportes/resumen_mensual.html',
        resumen=resumen,
        mes=mes_str,
        docente=docente_filtro
    )

@reportes_bp.route('/incumplimientos/pdf')
def exportar_pdf():
    jornada = request.args.get('jornada')
    desde_str = request.args.get('desde')
    hasta_str = request.args.get('hasta')
    docentes_ids = request.args.getlist('docente')

    hoy = datetime.now().date()
    try:
        desde = datetime.strptime(desde_str, '%Y-%m-%d').date() if desde_str else hoy
        hasta = datetime.strptime(hasta_str, '%Y-%m-%d').date() if hasta_str else hoy
    except ValueError:
        return "Fechas inválidas", 400

    query = Asistencia.query.join(Docente).filter(Asistencia.fecha.between(desde, hasta))
    if jornada:
        query = query.filter(Docente.jornada == jornada)
    if docentes_ids:
        query = query.filter(Docente.id.in_(docentes_ids))

    registros = query.order_by(Asistencia.fecha, Asistencia.hora_entrada).all()

    resumen_docentes = defaultdict(lambda: {
        'nombre': '',
        'jornada': '',
        'entrada_tarde': 0,
        'salida_temprano': 0,
        'incumplimientos': 0,
        'tiempo_total': timedelta()
    })

    for a in registros:
        entrada_tarde, salida_temprano = evaluar_asistencia(a.docente, a.hora_entrada, a.hora_salida)
        tiempo_acumulado = calcular_tiempo_acumulado(a.hora_entrada, a.hora_salida)

        if entrada_tarde or salida_temprano:
            d = resumen_docentes[a.docente.id]
            d['nombre'] = a.docente.nombre
            d['jornada'] = a.docente.jornada
            d['entrada_tarde'] += int(entrada_tarde)
            d['salida_temprano'] += int(salida_temprano)
            d['incumplimientos'] += 1
            d['tiempo_total'] += tiempo_acumulado or timedelta()

    resumen_lista = list(resumen_docentes.values())

    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Encabezado institucional
    elements.append(Paragraph("Unidad Educativa “ALBERTINA RIVAS MEDINA”", styles['Title']))
    elements.append(Paragraph("Resumen de incumplimientos por docente", styles['Heading2']))
    elements.append(Paragraph(f"Periodo: {desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}", styles['Normal']))
    if jornada:
        elements.append(Paragraph(f"Jornada: {jornada.capitalize()}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Tabla
    data = [
        ["Docente", "Jornada", "Entradas tarde", "Salidas temprano", "Incumplimientos", "Tiempo total"]
    ]
    for r in resumen_lista:
        tiempo = f"{r['tiempo_total'].seconds // 3600}h {(r['tiempo_total'].seconds // 60) % 60}m"
        data.append([
            r['nombre'],
            r['jornada'].capitalize(),
            r['entrada_tarde'],
            r['salida_temprano'],
            r['incumplimientos'],
            tiempo
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightyellow])
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=False, download_name="incumplimientos.pdf", mimetype='application/pdf')



def calcular_jornada_esperada(jornada: str) -> timedelta:
    """
    Devuelve la duración esperada de la jornada laboral según el tipo.
    """
    if jornada == "matutina":
        return timedelta(hours=8)   # ejemplo: 8 horas
    elif jornada == "vespertina":
        return timedelta(hours=8)   # ejemplo: 8 horas
    elif jornada == "doble":
        return timedelta(hours=16)  # ejemplo: 16 horas
    else:
        # valor por defecto si no está definido
        return timedelta(hours=8)


@reportes_bp.route('/consolidado')
def reporte_consolidado():
    desde_str = request.args.get('desde')
    hasta_str = request.args.get('hasta')

    desde = datetime.strptime(desde_str, '%Y-%m-%d').date() if desde_str else date.today().replace(day=1)
    hasta = datetime.strptime(hasta_str, '%Y-%m-%d').date() if hasta_str else date.today()

    docentes = Docente.query.order_by(Docente.nombre).all()
    consolidado = []

    for d in docentes:
        # Asistencias en el rango
        asistencias = Asistencia.query.filter(
            Asistencia.docente_id == d.id,
            Asistencia.fecha.between(desde, hasta)
        ).all()
        fechas_con_asistencia = {a.fecha for a in asistencias}

        # Licencias aprobadas que se solapan con el rango
        licencias = Licencia.query.filter(
            Licencia.docente_id == d.id,
            Licencia.estado == 'aprobada',
            Licencia.fecha_inicio <= hasta,
            Licencia.fecha_fin >= desde
        ).all()

        # Expandir días de licencia
        fechas_con_licencia = set()
        for l in licencias:
            dia = max(l.fecha_inicio, desde)
            fin = min(l.fecha_fin, hasta)
            while dia <= fin:
                fechas_con_licencia.add(dia)
                dia += timedelta(days=1)

        # Calcular faltas (solo días laborales sin asistencia ni licencia)
        faltas = 0
        dia = desde
        while dia <= hasta:
            if dia.weekday() < 5:  # lunes-viernes
                if dia not in fechas_con_asistencia and dia not in fechas_con_licencia:
                    faltas += 1
            dia += timedelta(days=1)

        # Calcular horas incumplidas
        horas_incumplidas = timedelta()
        for a in asistencias:
            entrada_tarde, salida_temprano = evaluar_asistencia(d, a.hora_entrada, a.hora_salida)
            if entrada_tarde or salida_temprano:
                esperado = calcular_jornada_esperada(d.jornada)
                trabajado = calcular_tiempo_acumulado(a.hora_entrada, a.hora_salida) or timedelta()
                horas_incumplidas += max(timedelta(), esperado - trabajado)

        consolidado.append({
            "docente": d.nombre,
            "jornada": d.jornada,
            "faltas": faltas,
            "licencias": len(licencias),
            "horas_incumplidas": f"{horas_incumplidas.seconds//3600}h {(horas_incumplidas.seconds//60)%60}m"
        })

    return render_template("reportes/consolidado.html",
                           consolidado=consolidado,
                           desde=desde,
                           hasta=hasta)