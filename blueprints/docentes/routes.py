from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app_simple import db
from models.docente import Docente

docentes_bp = Blueprint('docentes', __name__, template_folder='templates/docentes')

# Vista principal con filtros
@docentes_bp.route('/')
@login_required
def index():
    jornada = request.args.get('jornada')
    estado = request.args.get('estado')
    tipo = request.args.get('tipo')


    query = Docente.query

    if jornada:
        query = query.filter_by(jornada=jornada)
    
    if tipo:
        query = query.filter_by(tipo=tipo)

    if estado == 'activo':
        query = query.filter_by(activo=True)
    elif estado == 'inactivo':
        query = query.filter_by(activo=False)

    docentes = query.order_by(Docente.nombre).all()
    return render_template('docentes/index_docentes.html', docentes=docentes)

# Búsqueda AJAX para Select2
@docentes_bp.route('/buscar', endpoint='buscar')
def buscar_docentes():
    q = request.args.get('q', '')
    resultados = Docente.query.filter(Docente.nombre.ilike(f'%{q}%')).limit(20).all()
    return jsonify([{'id': d.id, 'text': d.nombre} for d in resultados])

# Registro de nuevo docente
@docentes_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_docente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        jornada = request.form.get('jornada')
        tipo = request.form.get('tipo')

        # Validaciones básicas
        if not nombre or not cedula or not telefono or not correo:
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('docentes.nuevo_docente'))

        if jornada not in ['matutina', 'vespertina', 'doble'] or tipo not in ['DOCENTE', 'ADMINISTRATIVO', 'CONSERJE', 'DECE']:
            flash('Datos inválidos. Verifica la jornada y el tipo de personal.', 'warning')
            return redirect(url_for('docentes.nuevo_docente'))

        # Verificar si ya existe un docente con la misma cédula o correo
        docente_existente = Docente.query.filter(
            (Docente.cedula == cedula) | (Docente.correo == correo)
        ).first()

        if docente_existente:
            if docente_existente.cedula == cedula:
                flash('Ya existe un docente registrado con esta cédula.', 'danger')
            if docente_existente.correo == correo:
                flash('Ya existe un docente registrado con este correo electrónico.', 'danger')
            return render_template('docentes/form_docente.html', 
                                docente=request.form,
                                es_nuevo=True)

        try:
            # Crear nuevo docente
            nuevo = Docente(
                nombre=nombre,
                cedula=cedula,
                telefono=telefono,
                correo=correo,
                jornada=jornada,
                tipo=tipo
            )

            db.session.add(nuevo)
            db.session.commit()
            flash('Docente registrado correctamente.', 'success')
            return redirect(url_for('docentes.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el docente. Por favor, verifica los datos.', 'danger')
            return render_template('docentes/form_docente.html', 
                                docente=request.form,
                                es_nuevo=True)

    return render_template('docentes/form_docente.html', es_nuevo=True)

# Edición de docente
@docentes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_docente(id):
    docente = Docente.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        jornada = request.form.get('jornada')
        tipo = request.form.get('tipo')

        # Validaciones básicas
        if not nombre or not cedula or not telefono or not correo:
            flash('Todos los campos son obligatorios.', 'warning')
            return render_template('docentes/form_docente.html', docente=docente)

        if jornada not in ['matutina', 'vespertina', 'doble'] or tipo not in ['DOCENTE', 'ADMINISTRATIVO', 'CONSERJE', 'DECE']:
            flash('Datos inválidos. Verifica la jornada y el tipo de personal.', 'warning')
            return render_template('docentes/form_docente.html', docente=docente)

        # Verificar si ya existe otro docente con la misma cédula o correo
        docente_existente = Docente.query.filter(
            (Docente.cedula == cedula) | (Docente.correo == correo)
        ).filter(Docente.id != id).first()

        if docente_existente:
            if docente_existente.cedula == cedula:
                flash('Ya existe otro docente registrado con esta cédula.', 'danger')
            if docente_existente.correo == correo:
                flash('Ya existe otro docente registrado con este correo electrónico.', 'danger')
            return render_template('docentes/form_docente.html', docente=docente)

        try:
            # Actualizar datos
            docente.nombre = nombre
            docente.cedula = cedula
            docente.telefono = telefono
            docente.correo = correo
            docente.jornada = jornada
            docente.tipo = tipo

            db.session.commit()
            flash('Docente actualizado correctamente.', 'success')
            return redirect(url_for('docentes.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el docente. Por favor, verifica los datos.', 'danger')
            return render_template('docentes/form_docente.html', docente=docente)

    return render_template('docentes/form_docente.html', docente=docente)
    
# Eliminación de docente
@docentes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_docente(id):
    docente = Docente.query.get_or_404(id)
    db.session.delete(docente)
    db.session.commit()
    flash('Docente eliminado correctamente.', 'success')
    return redirect(url_for('docentes.index'))

# Desactivación de docente
@docentes_bp.route('/desactivar/<int:id>', methods=['POST'])
def desactivar_docente(id):
    docente = Docente.query.get_or_404(id)
    docente.activo = False
    db.session.commit()
    flash('Docente desactivado correctamente.', 'info')
    return redirect(url_for('docentes.index'))

# Reactivación de docente
@docentes_bp.route('/reactivar/<int:id>', methods=['POST'])
def reactivar_docente(id):
    docente = Docente.query.get_or_404(id)
    docente.activo = True
    db.session.commit()
    flash('Docente reactivado correctamente.', 'info')
    return redirect(url_for('docentes.index'))


@docentes_bp.route("/docentes/carga_masiva", methods=["GET", "POST"])
def carga_masiva():
    if request.method == "POST":
        file = request.files["archivo"]
        if not file:
            flash("Debes subir un archivo CSV o Excel", "danger")
            return redirect(url_for("docentes.carga_masiva"))

        import pandas as pd
        # Forzar lectura de columnas como texto
        df = pd.read_excel(file, dtype={"cedula": str, "telefono": str, "correo": str})

        cargados, errores = 0, []
        for i, row in df.iterrows():
            fila = i + 2  # +2 porque pandas empieza en 0 y fila 1 son encabezados

            # --- Normalizar cédula ---
            cedula = str(row.get("cedula", "")).strip()
            if "." in cedula:  # si viene como float (ej: 123456789.0)
                cedula = cedula.split(".")[0]
            cedula = cedula.zfill(10)  # rellenar con ceros a la izquierda

            if not cedula.isdigit() or len(cedula) != 10:
                errores.append(f"Fila {fila}: cédula inválida ({row.get('cedula')})")
                continue

            if Docente.query.filter_by(cedula=cedula).first():
                errores.append(f"Fila {fila}: cédula duplicada ({cedula})")
                continue

            # --- Normalizar teléfono ---
            telefono = str(row.get("telefono", "")).strip()
            if "." in telefono:
                telefono = telefono.split(".")[0]

            if not telefono.isdigit() or not (7 <= len(telefono) <= 10):
                errores.append(f"Fila {fila}: teléfono inválido ({row.get('telefono')})")
                continue

            # --- Correo ---
            correo = str(row.get("correo", "")).strip()
            if "@" not in correo or "." not in correo:
                errores.append(f"Fila {fila}: correo inválido ({correo})")
                continue

            # --- Jornada y tipo ---
            jornada = str(row.get("jornada", "")).lower()
            if jornada not in ["matutina", "vespertina", "doble"]:
                errores.append(f"Fila {fila}: jornada inválida ({jornada})")
                continue

            tipo = str(row.get("tipo", "")).upper()
            if tipo not in ["DOCENTE", "ADMINISTRATIVO", "CONSERJE", "DECE"]:
                errores.append(f"Fila {fila}: tipo inválido ({tipo})")
                continue

            # --- Crear docente ---
            docente = Docente(
                nombre=row.get("nombre", "").strip(),
                cedula=cedula,
                telefono=telefono,
                correo=correo,
                jornada=jornada,
                tipo=tipo,
                activo=True
            )
            db.session.add(docente)
            cargados += 1

        db.session.commit()
        flash(f"✅ {cargados} docentes cargados correctamente", "success")
        if errores:
            flash("⚠️ Errores encontrados:\n" + "\n".join(errores), "warning")

        return redirect(url_for("docentes.index"))

    return render_template("docentes/carga_masiva.html")