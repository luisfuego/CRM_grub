"""
Orders Blueprint - Bestellungsverwaltung
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from sqlalchemy import desc, or_
from datetime import datetime
import csv
import io

from models import db, Order, OrderItem, Customer, Product

bp = Blueprint('orders', __name__, url_prefix='/orders')


@bp.route('/')
@login_required
def list():
    """Globale Bestellübersicht (chronologisch)"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    query = Order.query.join(Customer)
    
    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f'%{search}%'),
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    pagination = query.order_by(desc(Order.order_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiken
    stats = {
        'total': Order.query.count(),
        'open': Order.query.filter_by(status='Offen').count(),
        'paid': Order.query.filter_by(status='Bezahlt').count(),
        'cancelled': Order.query.filter_by(status='Storniert').count()
    }
    
    return render_template('orders/list.html',
                         pagination=pagination,
                         search=search,
                         status_filter=status_filter,
                         stats=stats)


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Bestelldetails"""
    order = Order.query.get_or_404(id)
    items = order.items.all()
    
    return render_template('orders/detail.html', order=order, items=items)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Neue Bestellung anlegen"""
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', type=int)
        
        if not customer_id:
            flash('Bitte wählen Sie einen Kunden aus.', 'danger')
            return redirect(url_for('orders.new'))
        
        customer = Customer.query.get_or_404(customer_id)
        
        # Generiere Bestellnummer
        year = datetime.now().year
        last_order = Order.query.filter(
            Order.order_number.like(f'A-{year}%')
        ).order_by(desc(Order.order_number)).first()
        
        if last_order:
            last_num = int(last_order.order_number.split('-')[1])
            order_number = f'A-{last_num + 1}'
        else:
            order_number = f'A-{year}001'
        
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            order_date=datetime.now(),
            status='Offen',
            total_amount=0,
            notes=request.form.get('notes')
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash(f'Bestellung {order.order_number} wurde angelegt.', 'success')
        return redirect(url_for('orders.edit', id=order.id))
    
    # Kundenliste für Dropdown
    customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    
    return render_template('orders/form.html', order=None, customers=customers)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Bestellung bearbeiten"""
    order = Order.query.get_or_404(id)
    
    if request.method == 'POST':
        order.status = request.form.get('status')
        order.notes = request.form.get('notes')
        
        db.session.commit()
        
        flash('Bestellung aktualisiert.', 'success')
        return redirect(url_for('orders.detail', id=id))
    
    items = order.items.all()
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('orders/edit.html', order=order, items=items, products=products)


@bp.route('/<int:id>/add_item', methods=['POST'])
@login_required
def add_item(id):
    """Position zur Bestellung hinzufügen"""
    order = Order.query.get_or_404(id)
    
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    unit_price = request.form.get('unit_price', type=float)
    
    if not product_id or not quantity or not unit_price:
        flash('Bitte füllen Sie alle Felder aus.', 'danger')
        return redirect(url_for('orders.edit', id=id))
    
    item = OrderItem(
        order_id=order.id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price
    )
    
    db.session.add(item)
    
    # Aktualisiere Gesamtsumme
    order.total_amount = order.calculate_total()
    
    db.session.commit()
    
    flash('Position hinzugefügt.', 'success')
    return redirect(url_for('orders.edit', id=id))


@bp.route('/<int:order_id>/remove_item/<int:item_id>', methods=['POST'])
@login_required
def remove_item(order_id, item_id):
    """Position aus Bestellung entfernen"""
    order = Order.query.get_or_404(order_id)
    item = OrderItem.query.get_or_404(item_id)
    
    if item.order_id != order.id:
        flash('Ungültige Position.', 'danger')
        return redirect(url_for('orders.edit', id=order_id))
    
    db.session.delete(item)
    
    # Aktualisiere Gesamtsumme
    order.total_amount = order.calculate_total()
    
    db.session.commit()
    
    flash('Position entfernt.', 'success')
    return redirect(url_for('orders.edit', id=order_id))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Bestellung löschen"""
    if current_user.role not in ['Admin', 'Chef']:
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('orders.detail', id=id))
    
    order = Order.query.get_or_404(id)
    order_number = order.order_number
    
    db.session.delete(order)
    db.session.commit()
    
    flash(f'Bestellung {order_number} wurde gelöscht.', 'warning')
    return redirect(url_for('orders.list'))


@bp.route('/<int:id>/export_csv')
@login_required
def export_csv(id):
    """CSV-Export der Bestellung"""
    order = Order.query.get_or_404(id)
    items = order.items.all()
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow(['Bestellung', order.order_number])
    writer.writerow(['Kunde', order.customer.full_name])
    writer.writerow(['Datum', order.order_date.strftime('%d.%m.%Y')])
    writer.writerow(['Status', order.status])
    writer.writerow([])
    writer.writerow(['Position', 'Produkt', 'Menge', 'Einzelpreis', 'Gesamt'])
    
    # Positionen
    for i, item in enumerate(items, 1):
        writer.writerow([
            i,
            item.product.name,
            item.quantity,
            f"{item.unit_price:.2f}",
            f"{item.line_total:.2f}"
        ])
    
    writer.writerow([])
    writer.writerow(['', '', '', 'Gesamtsumme:', f"{order.total_amount:.2f} EUR"])
    
    # Response erstellen
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=bestellung_{order.order_number}.csv'
    
    return response
