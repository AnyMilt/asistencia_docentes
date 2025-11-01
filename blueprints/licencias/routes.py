from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta, date
from models import Docente, Licencia
from app_simple import db

licencias_bp = Blueprint('licencias', __name__, template_folder='templates/licencias')

# 🔧 Utilidades
def filtrar_licencias(query, docente_id=None, desde=None, hasta=None):
    if docente_id:
        query = query.filter(Licencia.docente_id == int(docente_id))
    if desde:
        query = query.filter(Licencia.fecha_inicio >= datetime.strptime(desde, '%Y-%m-%d').date())
    if hasta:
        query = query.filter(Licencia.fecha_fin <= datetime.strptime(hasta, '%Y-%m-%d').date())
    return query

def licencia_solapada(docente_id, fecha_inicio, fecha_fin, licencia_id=None):
    query = Licencia.query.filter(
        Licencia.docente_id == docente_id,
        Licencia.fecha_inicio <= fecha_fin,
        Licencia.fecha_fin >= fecha_inicio
    )
    if licencia_id:
        query = query.filter(Licencia.id != licencia_id)
    return query.first()

# 🟦 Vista principal
@licencias_bp.route('/', methods=['GET', 'POST'])
def index():
    hoy = date.today()
    vencimiento_limite = hoy + timedelta(days=2)

    docentes = Docente.query.order_by(Docente.nombre).all()

    docente_id = request.form.get('docente_id')
    desde = request.form.get('desde')
    hasta = request.form.get('hasta')
   
    docente_nombre = None
    if docente_id:
        docente = Docente.query.get(docente_id)
        docente_nombre = docente.nombre if docente else None

    query = Licencia.query.join(Docente).filter(Licencia.estado == 'aprobada')
    query = filtrar_licencias(query, docente_id, desde, hasta)

    if not desde and not hasta:
        query = query.filter(Licencia.fecha_inicio <= hoy, Licencia.fecha_fin >= hoy)

    licencias = query.order_by(Licencia.fecha_inicio).all()

    

    return render_template(
        'licencias/activas.html',
        mensaje="Control de licencias",
        licencias=licencias,
        vencimiento_limite=vencimiento_limite,
        hoy=hoy.strftime('%d/%m/%Y'),
        docente_id=docente_id,
        docente_nombre=docente_nombre,
        docentes=docentes
    )

# 🟨 Licencias pendientes
@licencias_bp.route('/pendientes', methods=['GET', 'POST'])
def licencias_pendientes():
    docentes = Docente.query.order_by(Docente.nombre).all()
    docente_id = request.form.get('docente_id')
    desde = request.form.get('desde')
    hasta = request.form.get('hasta')

    query = Licencia.query.join(Docente).filter(Licencia.estado == 'pendiente')
    query = filtrar_licencias(query, docente_id, desde, hasta)

    licencias = query.order_by(Licencia.fecha_inicio).all()

    return render_template('licencias/pendientes.html', licencias=licencias, docentes=docentes)

# 🟩 Registro de nueva licencia
@licencias_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_licencia():
    docentes = Docente.query.order_by(Docente.nombre).all()  # ✅ definido al inicio

    if request.method == 'POST':
        try:
            docente_id = int(request.form['docente_id'])
            fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date()
            motivo = request.form.get('motivo', '').strip()
            estado = request.form.get('estado', 'pendiente')
            aprobado_por = request.form.get('aprobado_por', '').strip()

            if fecha_inicio > fecha_fin:
                flash("La fecha de inicio no puede ser posterior a la fecha de fin.", "danger")
                return render_template('licencias/nueva.html', docentes=docentes)

            conflicto = licencia_solapada(docente_id, fecha_inicio, fecha_fin)
            if conflicto:
                flash(f"Conflicto con licencia del {conflicto.fecha_inicio.strftime('%d/%m/%Y')} al {conflicto.fecha_fin.strftime('%d/%m/%Y')}.", "danger")
                return render_template('licencias/nueva.html', docentes=docentes)

            nueva = Licencia(
                docente_id=docente_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo,
                estado=estado,
                aprobado_por=aprobado_por
            )
            db.session.add(nueva)
            db.session.commit()
            flash("Licencia registrada correctamente.", "success")
            return redirect(url_for('licencias.index'))

        except Exception as e:
            flash(f"Error al registrar la licencia: {str(e)}", "danger")
            return render_template('licencias/nueva.html', docentes=docentes)

    return render_template('licencias/nueva.html', docentes=docentes)

# 🟦 Licencias activas (filtro alternativo)
@licencias_bp.route('/activas', methods=['GET', 'POST'])
def licencias_activas():
    docente_id = request.form.get('docente_id')
    desde = request.form.get('desde')
    hasta = request.form.get('hasta')
    
    docente_nombre = None
    if docente_id:
        docente = Docente.query.get(docente_id)
        docente_nombre = docente.nombre if docente else None

    query = Licencia.query.filter(Licencia.estado == 'aprobada')
    query = filtrar_licencias(query, docente_id, desde, hasta)

    licencias_filtradas = query.order_by(Licencia.fecha_inicio).all()

    hoy = date.today()
    vencimiento_limite = hoy + timedelta(days=3)

    return render_template(
        'licencias/activas.html',
        licencias=licencias_filtradas,
        docente_id=docente_id,
        docente_nombre=docente_nombre,
        hoy=hoy,
        vencimiento_limite=vencimiento_limite
    )

# 📝 Edición de licencia
@licencias_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_licencia(id):
    licencia = Licencia.query.get_or_404(id)
    docentes = Docente.query.order_by(Docente.nombre).all()

    if request.method == 'POST':
        docente_id = int(request.form['docente_id'])
        fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date()
        motivo = request.form['motivo']
        estado = request.form['estado']
        aprobado_por = request.form['aprobado_por']

        conflicto = licencia_solapada(docente_id, fecha_inicio, fecha_fin, licencia_id=id)
        if conflicto:
            flash(f"Conflicto con licencia del {conflicto.fecha_inicio.strftime('%d/%m/%Y')} al {conflicto.fecha_fin.strftime('%d/%m/%Y')}", "danger")
            return redirect(url_for('licencias.editar_licencia', id=id))

        licencia.docente_id = docente_id
        licencia.fecha_inicio = fecha_inicio
        licencia.fecha_fin = fecha_fin
        licencia.motivo = motivo
        licencia.estado = estado
        licencia.aprobado_por = aprobado_por

        db.session.commit()
        flash("Licencia actualizada correctamente.", "success")
        return redirect(url_for('licencias.index'))

    return render_template('licencias/editar.html', licencia=licencia, docentes=docentes)

# 🗑️ Eliminación de licencia
@licencias_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_licencia(id):
    licencia = Licencia.query.get_or_404(id)
    db.session.delete(licencia)
    db.session.commit()
    flash('Licencia eliminada', 'warning')
    return redirect(url_for('licencias.licencias_activas'))