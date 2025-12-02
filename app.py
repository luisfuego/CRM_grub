"""
CRM Application - Hauptdatei
Professionelles CRM-System nach Lehrerangabe
"""
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os

from config import config
from models import db, User, Customer, Product, Order, OrderItem, Contact


def create_app(config_name=None):
    """Application Factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melden Sie sich an, um auf diese Seite zuzugreifen.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from views import main, auth, customers, orders, contacts, reports
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(contacts.bp)
    app.register_blueprint(reports.bp)
    
    # Context processors
    @app.context_processor
    def utility_processor():
        """Globale Template-Variablen"""
        def format_currency(amount):
            """Formatiere Betrag als Währung"""
            if amount is None:
                return '0,00 €'
            return f"{float(amount):,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        def format_date(date):
            """Formatiere Datum"""
            if date is None:
                return '—'
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            return date.strftime('%d.%m.%Y')
        
        def format_datetime(dt):
            """Formatiere Datum und Zeit"""
            if dt is None:
                return '—'
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            return dt.strftime('%d.%m.%Y %H:%M')
        
        def time_ago(dt):
            """Relative Zeitangabe"""
            if dt is None:
                return '—'
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            
            now = datetime.utcnow()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f'vor {minutes} Min.' if minutes > 0 else 'gerade eben'
                else:
                    hours = diff.seconds // 3600
                    return f'vor {hours} Std.'
            elif diff.days == 1:
                return 'gestern'
            elif diff.days < 7:
                return f'vor {diff.days}d'
            elif diff.days < 30:
                weeks = diff.days // 7
                return f'vor {weeks}w'
            else:
                months = diff.days // 30
                return f'vor {months}m'
        
        return dict(
            format_currency=format_currency,
            format_date=format_date,
            format_datetime=format_datetime,
            time_ago=time_ago,
            now=datetime.utcnow()
        )
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Erstelle Tabellen bei erstem Start
    with app.app_context():
        db.create_all()
        
        # Erstelle Admin-User falls nicht vorhanden
        if User.query.count() == 0:
            admin = User(
                name='Admin',
                email='admin@crm.local',
                role='Admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin-User erstellt: admin@crm.local / admin123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
