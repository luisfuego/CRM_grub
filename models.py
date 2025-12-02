"""
CRM Database Models
Alle Tabellen entsprechend der Lehrerangabe
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Benutzer-Modell für Authentifizierung"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('Schüler', 'Lehrer', 'Admin', 'Chef', 'Mitarbeiter', 
                             name='user_role'), default='Mitarbeiter')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contacts = db.relationship('Contact', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash und speichere Passwort"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Überprüfe Passwort"""
        return check_password_hash(self.password_hash, password)
    
    def is_chef(self):
        """Prüfe ob User Chef ist"""
        return self.role in ['Chef', 'Admin']
    
    def __repr__(self):
        return f'<User {self.email}>'


class Customer(db.Model):
    """Kunden-Modell"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(200))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='Österreich')
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # Kundenbewertung 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy='dynamic', 
                            cascade='all, delete-orphan')
    contacts = db.relationship('Contact', backref='customer', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        """Vollständiger Name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        """Anzeigename für Listen"""
        return f"{self.last_name}, {self.first_name}"
    
    def get_total_revenue(self, start_date=None, end_date=None):
        """Berechne Gesamtumsatz"""
        query = self.orders.filter(Order.status != 'Storniert')
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        return sum(order.total_amount for order in query.all()) or 0
    
    def get_last_contact_date(self):
        """Letztes Kontaktdatum"""
        last_contact = self.contacts.order_by(Contact.contact_time.desc()).first()
        return last_contact.contact_time if last_contact else None
    
    def __repr__(self):
        return f'<Customer {self.full_name}>'


class Product(db.Model):
    """Produkte-Modell"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.name}>'


class Order(db.Model):
    """Bestellungen-Modell"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), 
                           nullable=False, index=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    status = db.Column(db.Enum('Offen', 'Bezahlt', 'Storniert', name='order_status'), 
                      default='Offen', index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic',
                           cascade='all, delete-orphan')
    
    # Composite Index für bessere Performance
    __table_args__ = (
        db.Index('idx_orders_customer_date', 'customer_id', 'order_date'),
    )
    
    def calculate_total(self):
        """Berechne Gesamtsumme aus Positionen"""
        return sum(item.quantity * item.unit_price for item in self.items.all()) or 0
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """Bestellpositionen-Modell"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), 
                        nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(5, 2), default=0)  # Rabatt in %
    
    @property
    def line_total(self):
        """Zeilensumme"""
        from decimal import Decimal
        subtotal = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        if self.discount:
            subtotal *= (Decimal('1') - Decimal(str(self.discount)) / Decimal('100'))
        return subtotal
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'


class Contact(db.Model):
    """Kontakte/Interaktionen-Modell"""
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    channel = db.Column(db.Enum('Telefon', 'E-Mail', 'Meeting', 'Chat', name='contact_channel'),
                       nullable=False, index=True)
    subject = db.Column(db.String(255))
    notes = db.Column(db.Text)
    contact_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    duration_minutes = db.Column(db.Integer)  # Dauer in Minuten
    rating = db.Column(db.Integer)  # Bewertung durch Kunde (1-5) - nur für Chef sichtbar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite Index für bessere Performance
    __table_args__ = (
        db.Index('idx_contacts_customer_time', 'customer_id', 'contact_time'),
    )
    
    def __repr__(self):
        return f'<Contact {self.channel} - {self.subject}>'


# Hilfsfunktion für Datenbankinitialisierung
def init_db(app):
    """Initialisiere Datenbank"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
