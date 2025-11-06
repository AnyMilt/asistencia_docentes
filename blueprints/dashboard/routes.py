from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date, timedelta
from sqlalchemy import func
from app_simple import db
from models import Docente, Licencia, Asistencia


dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates/dashboard')


from flask import Blueprint, render_template
from datetime import date, time, timedelta
from sqlalchemy import func
from app_simple import db
from models import Docente, Licencia, Asistencia



@dashboard_bp.route('/', methods=['GET', 'POST'], endpoint='index')
@login_required
def dashboard_home():
    hoy = date.today()
    vencimiento_limite = hoy + timedelta(days=3)

    # Métricas principales
    total_docentes = Docente.query.count()
    licencias_activas = Licencia.query.filter(
        Licencia.estado == 'aprobada',
        Licencia.fecha_inicio <= hoy,
        Licencia.fecha_fin >= hoy
    ).count()
    asistencia_hoy = Asistencia.query.filter(Asistencia.fecha == hoy).count()
    alertas = Licencia.query.filter(
        Licencia.estado == 'aprobada',
        Licencia.fecha_fin <= vencimiento_limite,
        Licencia.fecha_fin >= hoy
    ).count()

    metric_cards = [
        ('Docentes registrados', total_docentes),
        ('Licencias activas', licencias_activas),
        ('Asistencia hoy', asistencia_hoy),
        ('Alertas', alertas)
    ]

    # Licencias por estado (para gráfico)
    estado_raw = db.session.query(
        Licencia.estado,
        func.count(Licencia.id)
    ).group_by(Licencia.estado).all()

    estado_chart = {
        'labels': [estado.capitalize() for estado, _ in estado_raw] if estado_raw else [],
        'values': [cantidad for _, cantidad in estado_raw] if estado_raw else []
    }

    # Ranking de docentes con más licencias
    ranking = db.session.query(
        Docente.nombre,
        func.count(Licencia.id)
    ).join(Licencia).group_by(Docente.id).order_by(func.count(Licencia.id).desc()).limit(5).all()

    # Ranking de docentes con más tardanzas (hora entrada > 07:30)
    ranking_tardanzas = db.session.query(
        Docente.nombre,
        func.count(Asistencia.id)
    ).join(Asistencia).filter(Asistencia.hora_entrada > time(7, 30))\
    .group_by(Docente.id).order_by(func.count(Asistencia.id).desc()).limit(5).all()

    # Ranking de docentes con más faltas (sin asistencia en los últimos 5 días)
    dias_recientes = [hoy - timedelta(days=i) for i in range(5)]
    ranking_faltas = db.session.query(
        Docente.nombre,
        func.count().label('faltas')
    ).outerjoin(Asistencia, (Asistencia.docente_id == Docente.id) & (Asistencia.fecha.in_(dias_recientes)))\
    .filter(Asistencia.id == None)\
    .group_by(Docente.id).order_by(func.count().desc()).limit(5).all()

    # Docentes por jornada
    jornadas_raw = db.session.query(
        Docente.jornada,
        func.count(Docente.id)
    ).group_by(Docente.jornada).all()

    # Total global
    total_docentes = sum(cantidad for _, cantidad in jornadas_raw)

    # Formato para el template
    docentes_por_jornada = [
        (jornada.capitalize(), cantidad) for jornada, cantidad in jornadas_raw
    ]

    return render_template('dashboard/dashboard.html',
        metric_cards=metric_cards,
        estado_chart=estado_chart,
        ranking=ranking,
        ranking_tardanzas=ranking_tardanzas,
        ranking_faltas=ranking_faltas,
        docentes_por_jornada=docentes_por_jornada,
        total_docentes=total_docentes,
        hoy=hoy
    )

    
