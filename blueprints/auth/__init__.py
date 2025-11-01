from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app import db
from models.usuario import Usuario
from validators import UsuarioSchema

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor completa todos los campos', 'warning')
            return render_template('auth/login.html')
        
        # Buscar usuario
        usuario = Usuario.query.filter_by(username=username, activo=True).first()
        
        if usuario and usuario.check_password(password):
            login_user(usuario, remember=True)
            usuario.ultimo_acceso = datetime.utcnow()
            db.session.commit()
            
            flash(f'¡Bienvenido, {usuario.username}!', 'success')
            
            # Redirigir según el rol
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Registro de nuevos usuarios (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        schema = UsuarioSchema()
        try:
            data = schema.load(request.form)
            
            # Verificar si el usuario ya existe
            if Usuario.query.filter_by(username=data['username']).first():
                flash('El nombre de usuario ya existe', 'danger')
                return render_template('auth/register.html')
            
            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                username=data['username'],
                rol=data.get('rol', 'talento_humano')
            )
            nuevo_usuario.set_password(data['password'])
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash(f'Usuario {nuevo_usuario.username} creado exitosamente', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            flash(f'Error al crear usuario: {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/users')
@login_required
def users():
    """Lista de usuarios (solo admin)"""
    if not current_user.is_admin():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.index'))
    
    usuarios = Usuario.query.order_by(Usuario.username).all()
    return render_template('auth/users.html', usuarios=usuarios)

@auth_bp.route('/profile')
@login_required
def profile():
    """Perfil del usuario actual"""
    return render_template('auth/profile.html', usuario=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Contraseña actual incorrecta', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Las contraseñas nuevas no coinciden', 'danger')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Contraseña cambiada exitosamente', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')
