"""
Auth Blueprint - Authentifizierung
Login, Logout, Registrierung
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse

from models import db, User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Ungültige E-Mail oder Passwort.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Ihr Account ist deaktiviert. Bitte kontaktieren Sie den Administrator.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        flash(f'Willkommen zurück, {user.name}!', 'success')
        
        # Redirect to next page or home
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registrierung (optional - kann deaktiviert werden)"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validierung
        if not name or not email or not password:
            flash('Bitte füllen Sie alle Felder aus.', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != password_confirm:
            flash('Passwörter stimmen nicht überein.', 'danger')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('E-Mail-Adresse bereits registriert.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create user
        user = User(name=name, email=email, role='Mitarbeiter')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@bp.route('/profile')
@login_required
def profile():
    """Benutzerprofil"""
    return render_template('auth/profile.html')


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Profil bearbeiten"""
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        
        # Passwort ändern (optional)
        new_password = request.form.get('new_password')
        if new_password:
            if len(new_password) < 6:
                flash('Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
                return redirect(url_for('auth.edit_profile'))
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profil aktualisiert.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')
