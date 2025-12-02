"""
Customers Blueprint - Kundenverwaltung
Detailansicht mit KPIs, Umsatzfilter, Bestellungen und Kontakten
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from models import db, Customer, Order, Contact

bp = Blueprint('customers', __name__, url_prefix='/customers')


@bp.route('/')
@login_required
def list():
    """Kundenliste"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    search = request.args.get('q', '').strip()
    
    query = Customer.query
    
    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.company.ilike(f'%{search}%'),
                Customer.city.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(desc(Customer.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('customers/list.html', 
                         pagination=pagination, 
                         search=search)


@bp.route('/<int:id>')
@login_required
def detail(id):
    """
    Kunden-Detailansicht mit:
    - KPIs (Umsatz gesamt, Umsatz letztes Jahr, Datumsbereich)
    - Letzte Bestellungen
    - Letzte Kontakte
    - Stammdaten
    """
    customer = Customer.query.get_or_404(id)
    
    # Datumsfilter aus Request
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    
    # KPI: Umsatz gesamt
    revenue_total = customer.get_total_revenue()
    
    # KPI: Umsatz letztes Kalenderjahr
    last_year_start = datetime(datetime.now().year - 1, 1, 1)
    last_year_end = datetime(datetime.now().year - 1, 12, 31, 23, 59, 59)
    revenue_last_year = customer.get_total_revenue(last_year_start, last_year_end)
    
    # KPI: Umsatz im gewählten Datumsbereich
    revenue_period = None
    if date_from and date_to:
        try:
            from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            to_dt = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            revenue_period = customer.get_total_revenue(from_dt, to_dt)
        except ValueError:
            flash('Ungültiges Datumsformat.', 'danger')
    
    # Letzte Bestellungen (nach Datum sortiert)
    orders = customer.orders.order_by(desc(Order.order_date)).limit(10).all()
    
    # Letzte Kontakte (Timeline, neueste zuerst)
    contacts = customer.contacts.order_by(desc(Contact.contact_time)).limit(15).all()
    
    # Letzter Kontakt
    last_contact = contacts[0] if contacts else None
    
    # Statistiken
    order_count = customer.orders.count()
    contact_count = customer.contacts.count()
    
    # Durchschnittlicher Bestellwert
    avg_order_value = 0
    if order_count > 0:
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.customer_id == customer.id,
            Order.status != 'Storniert'
        ).scalar() or 0
        avg_order_value = total_revenue / order_count
    
    return render_template('customers/detail.html',
                         customer=customer,
                         orders=orders,
                         contacts=contacts,
                         last_contact=last_contact,
                         revenue_total=revenue_total,
                         revenue_last_year=revenue_last_year,
                         revenue_period=revenue_period,
                         order_count=order_count,
                         contact_count=contact_count,
                         avg_order_value=avg_order_value,
                         date_from=date_from,
                         date_to=date_to)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Neuen Kunden anlegen"""
    if request.method == 'POST':
        customer = Customer(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            company=request.form.get('company'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            postal_code=request.form.get('postal_code'),
            country=request.form.get('country', 'Österreich'),
            notes=request.form.get('notes')
        )
        
        # Validierung
        if not customer.first_name or not customer.last_name:
            flash('Vor- und Nachname sind erforderlich.', 'danger')
            return redirect(url_for('customers.new'))
        
        db.session.add(customer)
        db.session.commit()
        
        flash(f'Kunde {customer.full_name} wurde erfolgreich angelegt.', 'success')
        return redirect(url_for('customers.detail', id=customer.id))
    
    return render_template('customers/form.html', customer=None)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Kunde bearbeiten"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.first_name = request.form.get('first_name')
        customer.last_name = request.form.get('last_name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.company = request.form.get('company')
        customer.address = request.form.get('address')
        customer.city = request.form.get('city')
        customer.postal_code = request.form.get('postal_code')
        customer.country = request.form.get('country', 'Österreich')
        customer.notes = request.form.get('notes')
        
        # Validierung
        if not customer.first_name or not customer.last_name:
            flash('Vor- und Nachname sind erforderlich.', 'danger')
            return redirect(url_for('customers.edit', id=id))
        
        db.session.commit()
        
        flash(f'Kunde {customer.full_name} wurde aktualisiert.', 'success')
        return redirect(url_for('customers.detail', id=id))
    
    return render_template('customers/form.html', customer=customer)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Kunde löschen"""
    if current_user.role not in ['Admin', 'Chef']:
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('customers.detail', id=id))
    
    customer = Customer.query.get_or_404(id)
    name = customer.full_name
    
    db.session.delete(customer)
    db.session.commit()
    
    flash(f'Kunde {name} wurde gelöscht.', 'warning')
    return redirect(url_for('customers.list'))


@bp.route('/<int:id>/revenue', methods=['GET'])
@login_required
def revenue(id):
    """
    API-Endpoint für Umsatzfilter
    GET /customers/{id}/revenue?from=YYYY-MM-DD&to=YYYY-MM-DD
    """
    customer = Customer.query.get_or_404(id)
    
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    if not date_from or not date_to:
        return {'error': 'Missing parameters'}, 400
    
    try:
        from_dt = datetime.strptime(date_from, '%Y-%m-%d')
        to_dt = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        return {'error': 'Invalid date format'}, 400
    
    revenue = customer.get_total_revenue(from_dt, to_dt)
    
    return {
        'customer_id': customer.id,
        'customer_name': customer.full_name,
        'from': date_from,
        'to': date_to,
        'revenue': float(revenue)
    }
