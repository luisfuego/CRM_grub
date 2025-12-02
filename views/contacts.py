"""
Contacts Blueprint - Kontaktverwaltung
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime

from models import db, Contact, Customer

bp = Blueprint('contacts', __name__, url_prefix='/contacts')


@bp.route('/')
@login_required
def list():
    """Globale Kontaktübersicht (chronologisch, filterbar nach Art)"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    channel_filter = request.args.get('channel', '').strip()
    customer_filter = request.args.get('customer', '').strip()
    
    query = Contact.query.join(Customer)
    
    if channel_filter:
        query = query.filter(Contact.channel == channel_filter)
    
    if customer_filter:
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(f'%{customer_filter}%'),
                Customer.last_name.ilike(f'%{customer_filter}%')
            )
        )
    
    pagination = query.order_by(desc(Contact.contact_time)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiken nach Kanal
    stats = {
        'total': Contact.query.count(),
        'Telefon': Contact.query.filter_by(channel='Telefon').count(),
        'E-Mail': Contact.query.filter_by(channel='E-Mail').count(),
        'Meeting': Contact.query.filter_by(channel='Meeting').count(),
        'Chat': Contact.query.filter_by(channel='Chat').count()
    }
    
    return render_template('contacts/list.html',
                         pagination=pagination,
                         channel_filter=channel_filter,
                         customer_filter=customer_filter,
                         stats=stats)


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Kontaktdetails"""
    contact = Contact.query.get_or_404(id)
    
    return render_template('contacts/detail.html', contact=contact)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Neuen Kontakt anlegen"""
    customer_id = request.args.get('customer_id', type=int)
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', type=int)
        
        if not customer_id:
            flash('Bitte wählen Sie einen Kunden aus.', 'danger')
            return redirect(url_for('contacts.new'))
        
        contact = Contact(
            customer_id=customer_id,
            user_id=current_user.id,
            channel=request.form.get('channel'),
            subject=request.form.get('subject'),
            notes=request.form.get('notes'),
            contact_time=datetime.now(),
            duration_minutes=request.form.get('duration_minutes', type=int),
            rating=request.form.get('rating', type=int) if current_user.is_chef() else None
        )
        
        # Validierung
        if not contact.channel:
            flash('Bitte wählen Sie einen Kanal aus.', 'danger')
            return redirect(url_for('contacts.new'))
        
        db.session.add(contact)
        db.session.commit()
        
        flash('Kontakt wurde erfasst.', 'success')
        return redirect(url_for('customers.detail', id=customer_id))
    
    # Kundenliste für Dropdown
    customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    
    # Wenn customer_id in URL, vorauswählen
    selected_customer = None
    if customer_id:
        selected_customer = Customer.query.get(customer_id)
    
    return render_template('contacts/form.html',
                         contact=None,
                         customers=customers,
                         selected_customer=selected_customer)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Kontakt bearbeiten"""
    contact = Contact.query.get_or_404(id)
    
    # Nur eigene Kontakte oder als Chef/Admin
    if contact.user_id != current_user.id and not current_user.is_chef():
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('contacts.detail', id=id))
    
    if request.method == 'POST':
        contact.channel = request.form.get('channel')
        contact.subject = request.form.get('subject')
        contact.notes = request.form.get('notes')
        contact.duration_minutes = request.form.get('duration_minutes', type=int)
        
        # Rating nur für Chef sichtbar/bearbeitbar
        if current_user.is_chef():
            contact.rating = request.form.get('rating', type=int)
        
        db.session.commit()
        
        flash('Kontakt aktualisiert.', 'success')
        return redirect(url_for('customers.detail', id=contact.customer_id))
    
    customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    
    return render_template('contacts/form.html',
                         contact=contact,
                         customers=customers,
                         selected_customer=contact.customer)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Kontakt löschen"""
    contact = Contact.query.get_or_404(id)
    
    # Nur eigene Kontakte oder als Chef/Admin
    if contact.user_id != current_user.id and not current_user.is_chef():
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('contacts.detail', id=id))
    
    customer_id = contact.customer_id
    
    db.session.delete(contact)
    db.session.commit()
    
    flash('Kontakt wurde gelöscht.', 'warning')
    return redirect(url_for('customers.detail', id=customer_id))
