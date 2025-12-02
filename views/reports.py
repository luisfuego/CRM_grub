"""
Reports Blueprint - Berichte und Dashboard
"""
from flask import Blueprint, render_template, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, extract, desc
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import csv
import io

from models import db, Order, Customer, Contact, Product

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
@login_required
def index():
    """Dashboard mit KPIs und Charts"""
    
    # Zeiträume definieren
    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - relativedelta(months=1))
    last_month_end = this_month_start - timedelta(seconds=1)
    this_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    last_year_start = this_year_start - relativedelta(years=1)
    last_year_end = this_year_start - timedelta(seconds=1)
    
    # KPIs berechnen
    kpis = {
        # Umsatz
        'revenue_total': db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert'
        ).scalar() or 0,
        'revenue_this_month': db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert',
            Order.order_date >= this_month_start
        ).scalar() or 0,
        'revenue_last_month': db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert',
            Order.order_date >= last_month_start,
            Order.order_date <= last_month_end
        ).scalar() or 0,
        'revenue_this_year': db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert',
            Order.order_date >= this_year_start
        ).scalar() or 0,
        'revenue_last_year': db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert',
            Order.order_date >= last_year_start,
            Order.order_date <= last_year_end
        ).scalar() or 0,
        
        # Bestellungen
        'orders_total': Order.query.count(),
        'orders_this_month': Order.query.filter(Order.order_date >= this_month_start).count(),
        'orders_open': Order.query.filter_by(status='Offen').count(),
        'orders_paid': Order.query.filter_by(status='Bezahlt').count(),
        
        # Kunden
        'customers_total': Customer.query.count(),
        'customers_this_month': Customer.query.filter(Customer.created_at >= this_month_start).count(),
        
        # Kontakte
        'contacts_total': Contact.query.count(),
        'contacts_this_month': Contact.query.filter(Contact.contact_time >= this_month_start).count()
    }
    
    # Monatsumsatz für Chart (letzte 12 Monate)
    monthly_revenue = []
    for i in range(11, -1, -1):
        month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
        month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
        
        revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert',
            Order.order_date >= month_start,
            Order.order_date <= month_end
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })
    
    # Top 10 Kunden nach Umsatz
    top_customers = db.session.query(
        Customer,
        func.sum(Order.total_amount).label('total_revenue')
    ).join(Order).filter(
        Order.status != 'Storniert'
    ).group_by(Customer.id).order_by(desc('total_revenue')).limit(10).all()
    
    # Bestellungen nach Status
    order_status_raw = db.session.query(
        Order.status,
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('total')
    ).group_by(Order.status).all()
    
    # Zu JSON-serialisierbaren Dicts konvertieren
    order_status_stats = [
        {'status': row.status, 'count': row.count, 'total': float(row.total or 0)}
        for row in order_status_raw
    ]
    
    # Kontakte nach Kanal
    contact_channel_raw = db.session.query(
        Contact.channel,
        func.count(Contact.id).label('count')
    ).group_by(Contact.channel).all()
    
    # Zu JSON-serialisierbaren Dicts konvertieren
    contact_channel_stats = [
        {'channel': row.channel, 'count': row.count}
        for row in contact_channel_raw
    ]
    
    # Neueste Aktivitäten
    recent_orders = Order.query.order_by(desc(Order.order_date)).limit(5).all()
    recent_contacts = Contact.query.order_by(desc(Contact.contact_time)).limit(5).all()
    
    # Durchschnittswerte
    avg_order_value = kpis['revenue_total'] / kpis['orders_total'] if kpis['orders_total'] > 0 else 0
    avg_customer_value = kpis['revenue_total'] / kpis['customers_total'] if kpis['customers_total'] > 0 else 0
    
    return render_template('reports/dashboard.html',
                         kpis=kpis,
                         monthly_revenue=monthly_revenue,
                         top_customers=top_customers,
                         order_status_stats=order_status_stats,
                         contact_channel_stats=contact_channel_stats,
                         recent_orders=recent_orders,
                         recent_contacts=recent_contacts,
                         avg_order_value=avg_order_value,
                         avg_customer_value=avg_customer_value)


@bp.route('/customers')
@login_required
def customers():
    """Kundenberichte"""
    
    # Top-Kunden nach verschiedenen Metriken
    top_by_revenue = db.session.query(
        Customer,
        func.sum(Order.total_amount).label('total_revenue'),
        func.count(Order.id).label('order_count')
    ).join(Order).filter(
        Order.status != 'Storniert'
    ).group_by(Customer.id).order_by(desc('total_revenue')).limit(20).all()
    
    top_by_orders = db.session.query(
        Customer,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_revenue')
    ).join(Order).filter(
        Order.status != 'Storniert'
    ).group_by(Customer.id).order_by(desc('order_count')).limit(20).all()
    
    # Kunden ohne Bestellungen
    customers_no_orders = Customer.query.outerjoin(Order).group_by(Customer.id).having(
        func.count(Order.id) == 0
    ).all()
    
    return render_template('reports/customers.html',
                         top_by_revenue=top_by_revenue,
                         top_by_orders=top_by_orders,
                         customers_no_orders=customers_no_orders)


@bp.route('/products')
@login_required
def products():
    """Produktberichte"""
    from models import OrderItem
    
    # Top-Produkte
    top_products = db.session.query(
        Product,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.status != 'Storniert'
    ).group_by(Product.id).order_by(desc('total_revenue')).limit(20).all()
    
    return render_template('reports/products.html', top_products=top_products)


@bp.route('/export/customers_csv')
@login_required
def export_customers_csv():
    """Export aller Kunden als CSV"""
    
    customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        'ID', 'Vorname', 'Nachname', 'E-Mail', 'Telefon', 'Firma',
        'Adresse', 'PLZ', 'Stadt', 'Land', 'Erstellt am'
    ])
    
    # Daten
    for customer in customers:
        writer.writerow([
            customer.id,
            customer.first_name,
            customer.last_name,
            customer.email or '',
            customer.phone or '',
            customer.company or '',
            customer.address or '',
            customer.postal_code or '',
            customer.city or '',
            customer.country or '',
            customer.created_at.strftime('%d.%m.%Y') if customer.created_at else ''
        ])
    
    # Response erstellen
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = 'attachment; filename=kunden_export.csv'
    
    return response


@bp.route('/export/orders_csv')
@login_required
def export_orders_csv():
    """Export aller Bestellungen als CSV"""
    
    orders = Order.query.join(Customer).order_by(desc(Order.order_date)).all()
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        'Bestellnummer', 'Kunde', 'Datum', 'Status', 'Betrag (EUR)'
    ])
    
    # Daten
    for order in orders:
        writer.writerow([
            order.order_number,
            order.customer.full_name,
            order.order_date.strftime('%d.%m.%Y'),
            order.status,
            f"{order.total_amount:.2f}"
        ])
    
    # Response erstellen
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = 'attachment; filename=bestellungen_export.csv'
    
    return response


@bp.route('/export/contacts_csv')
@login_required
def export_contacts_csv():
    """Export aller Kontakte als CSV"""
    
    # Nur Chef sieht Bewertungen
    show_ratings = current_user.is_chef()
    
    contacts = Contact.query.join(Customer).order_by(desc(Contact.contact_time)).all()
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    header = ['Datum', 'Kunde', 'Kanal', 'Betreff', 'Mitarbeiter', 'Dauer (Min)']
    if show_ratings:
        header.append('Bewertung')
    writer.writerow(header)
    
    # Daten
    for contact in contacts:
        row = [
            contact.contact_time.strftime('%d.%m.%Y %H:%M'),
            contact.customer.full_name,
            contact.channel,
            contact.subject or '',
            contact.user.name if contact.user else '',
            contact.duration_minutes or ''
        ]
        if show_ratings:
            row.append(contact.rating or '')
        writer.writerow(row)
    
    # Response erstellen
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = 'attachment; filename=kontakte_export.csv'
    
    return response
