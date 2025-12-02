"""
Main Blueprint - Dashboard/Startseite
Enthält Übersichten für Kunden, Bestellungen und Kontakte
"""
from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import desc, func, or_
from datetime import datetime, timedelta

from models import db, Customer, Order, Contact

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def index():
    """
    Streamlit-inspired CRM Dashboard mit sinnvoller Kundenlogik:
    - KPIs (Revenue, Customers, Orders, Conversion)
    - Customer Lifecycle Stages
    - Top Customers by Revenue & Score
    - Recent Activity
    - Recent Orders
    """
    now = datetime.now()
    
    # === KEY METRICS ===
    total_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(Order.status != 'Storniert').scalar() or 0
    
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    total_products = db.session.query(func.count(func.distinct(Order.id))).scalar() or 0
    
    # Neue Kunden diesen Monat
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_customers_this_month = Customer.query.filter(
        Customer.created_at >= month_start
    ).count()
    
    # Average Order Value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Conversion Rate (Kunden mit Bestellungen / Alle Kunden * 100)
    customers_with_orders = db.session.query(
        func.count(func.distinct(Order.customer_id))
    ).scalar() or 0
    conversion_rate = (customers_with_orders / total_customers * 100) if total_customers > 0 else 0
    
    stats = {
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_contacts': Contact.query.count(),
        'new_customers_this_month': new_customers_this_month,
        'avg_order_value': avg_order_value,
        'conversion_rate': conversion_rate
    }
    
    # === CUSTOMER LIFECYCLE STAGES ===
    # Lead: Kunden ohne Bestellung, aber mit Kontakten
    leads = db.session.query(Customer).outerjoin(Order).filter(
        Order.id == None,
        Customer.contacts.any()
    ).count()
    
    # Prospect: Kunden ohne Bestellung und ohne Kontakte (nur angelegt)
    prospects = db.session.query(Customer).outerjoin(Order).outerjoin(Contact).filter(
        Order.id == None,
        Contact.id == None
    ).count()
    
    # Customer: Kunden mit 1-3 Bestellungen
    customers_active = db.session.query(Customer).join(Order).group_by(Customer.id).having(
        func.count(Order.id).between(1, 3)
    ).count()
    
    # VIP: Kunden mit 4+ Bestellungen oder Rating >= 4
    vip_customers = db.session.query(Customer).outerjoin(Order).group_by(Customer.id).having(
        func.count(Order.id) >= 4
    ).count()
    
    lifecycle_stats = {
        'leads': leads,
        'prospects': prospects,
        'customers': customers_active,
        'vip': vip_customers
    }
    
    # === TOP CUSTOMERS BY REVENUE ===
    # Berechne Revenue und Customer Score für jeden Kunden
    top_customers_data = db.session.query(
        Customer,
        func.sum(Order.total_amount).label('total_revenue'),
        func.count(Order.id).label('order_count'),
        func.max(Order.order_date).label('last_order_date')
    ).join(Order).filter(
        Order.status != 'Storniert'
    ).group_by(Customer.id).order_by(
        desc('total_revenue')
    ).limit(5).all()
    
    top_customers = []
    for customer, revenue, order_count, last_order in top_customers_data:
        # Customer Score Berechnung:
        # - Revenue: 40% (normalisiert auf höchsten Umsatz)
        # - Frequency: 30% (Anzahl Bestellungen)
        # - Recency: 30% (Tage seit letzter Bestellung)
        days_since_order = (now - last_order).days if last_order else 999
        
        # Konvertiere alle Werte zu float für Berechnungen
        revenue_float = float(revenue) if revenue else 0
        total_revenue_float = float(total_revenue) if total_revenue else 0
        
        revenue_score = min((revenue_float / total_revenue_float * 100) if total_revenue_float > 0 else 0, 40)
        frequency_score = min(order_count * 5, 30)  # Max 30 Punkte bei 6+ Orders
        recency_score = max(30 - (days_since_order / 10), 0)  # Verliere 3 Punkte pro 10 Tage
        
        total_score = int(revenue_score + frequency_score + recency_score)
        
        top_customers.append({
            'customer': customer,
            'total_revenue': revenue,
            'order_count': order_count,
            'score': total_score
        })
    
    # === RECENT ACTIVITY (Letzte Kontakte) ===
    recent_contacts = Contact.query.order_by(
        desc(Contact.contact_time)
    ).limit(10).all()
    
    # === RECENT ORDERS ===
    recent_orders = Order.query.order_by(
        desc(Order.order_date)
    ).limit(10).all()
    
    # === CHANNEL COUNTS ===
    channel_counts = {}
    for channel in ['Telefon', 'E-Mail', 'Meeting', 'Chat']:
        channel_counts[channel] = Contact.query.filter_by(channel=channel).count()
    
    # === CUSTOMER HEALTH & CHURN RISK ===
    # Berechne für jeden Kunden: Health Score & Churn Risk
    all_customers = Customer.query.all()
    at_risk_customers = []
    
    for customer in all_customers:
        # Tage seit letzter Bestellung
        last_order = db.session.query(func.max(Order.order_date)).filter(
            Order.customer_id == customer.id
        ).scalar()
        
        if last_order:
            days_since_order = (now - last_order).days
            
            # Churn Risk: Wenn länger als 60 Tage keine Bestellung
            if days_since_order > 60:
                # Berechne Gesamtumsatz
                total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
                    Order.customer_id == customer.id,
                    Order.status != 'Storniert'
                ).scalar() or 0
                
                # Health Score: 0-100
                # Basis: 100 - (Tage seit letzter Order / 3)
                health_score = max(0, 100 - (days_since_order / 3))
                
                if health_score < 40 and float(total_revenue) > 1000:  # Nur wichtige Kunden
                    at_risk_customers.append({
                        'customer': customer,
                        'days_inactive': days_since_order,
                        'health_score': int(health_score),
                        'total_revenue': total_revenue,
                        'last_order_date': last_order
                    })
    
    # Sortiere nach Revenue (höchste zuerst)
    at_risk_customers.sort(key=lambda x: float(x['total_revenue']), reverse=True)
    at_risk_customers = at_risk_customers[:5]  # Top 5 gefährdete Kunden
    
    # === SALES PIPELINE ===
    # Gruppiere Bestellungen nach Status
    pipeline = {
        'Offen': Order.query.filter_by(status='Offen').count(),
        'In Bearbeitung': Order.query.filter_by(status='In Bearbeitung').count(),
        'Bezahlt': Order.query.filter_by(status='Bezahlt').count(),
        'Storniert': Order.query.filter_by(status='Storniert').count()
    }
    
    pipeline_revenue = {
        'Offen': float(db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'Offen'
        ).scalar() or 0),
        'In Bearbeitung': float(db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'In Bearbeitung'
        ).scalar() or 0),
        'Bezahlt': float(db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'Bezahlt'
        ).scalar() or 0)
    }
    
    # === REVENUE FORECAST (Nächster Monat) ===
    # Basierend auf durchschnittlichem monatlichen Wachstum
    last_3_months_revenue = []
    for i in range(3):
        month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status != 'Storniert',
            Order.order_date >= month_start,
            Order.order_date <= month_end
        ).scalar() or 0
        
        last_3_months_revenue.append(float(revenue))
    
    # Berechne Durchschnitt und Trend
    avg_monthly_revenue = sum(last_3_months_revenue) / len(last_3_months_revenue) if last_3_months_revenue else 0
    
    # Trend: Vergleiche letzten Monat mit vorletztem
    if len(last_3_months_revenue) >= 2 and last_3_months_revenue[1] > 0:
        growth_rate = (last_3_months_revenue[0] - last_3_months_revenue[1]) / last_3_months_revenue[1]
        forecast_next_month = last_3_months_revenue[0] * (1 + growth_rate)
    else:
        growth_rate = 0
        forecast_next_month = avg_monthly_revenue
    
    # === CUSTOMER SEGMENTATION (RFM) ===
    segments = {
        'Champions': 0,      # Hohe Frequency, Hoher Revenue, Kürzlich aktiv
        'Loyal': 0,          # Hohe Frequency, mittlerer Revenue
        'Potential': 0,      # Niedriger Frequency, aber hoher Revenue
        'At Risk': 0,        # War aktiv, jetzt inaktiv
        'Lost': 0            # Lange inaktiv
    }
    
    for customer in all_customers:
        last_order = db.session.query(func.max(Order.order_date)).filter(
            Order.customer_id == customer.id
        ).scalar()
        
        order_count = Order.query.filter_by(customer_id=customer.id).count()
        
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.customer_id == customer.id,
            Order.status != 'Storniert'
        ).scalar() or 0
        
        if last_order:
            days_since = (now - last_order).days
            
            if days_since < 30 and order_count >= 5 and float(total_revenue) > 5000:
                segments['Champions'] += 1
            elif days_since < 60 and order_count >= 3:
                segments['Loyal'] += 1
            elif float(total_revenue) > 3000 and order_count < 3:
                segments['Potential'] += 1
            elif days_since > 60 and days_since < 120:
                segments['At Risk'] += 1
            elif days_since > 120:
                segments['Lost'] += 1
        else:
            segments['Lost'] += 1
    
    # === NEXT BEST ACTIONS ===
    recommendations = []
    
    # 1. Offene Bestellungen follow-up
    open_orders_count = pipeline['Offen']
    if open_orders_count > 0:
        recommendations.append({
            'icon': '📋',
            'title': 'Follow-up offene Bestellungen',
            'description': f'{open_orders_count} Bestellungen warten auf Bearbeitung',
            'priority': 'high',
            'action_url': url_for('orders.list')
        })
    
    # 2. At-Risk Kunden kontaktieren
    if len(at_risk_customers) > 0:
        recommendations.append({
            'icon': '⚠️',
            'title': 'At-Risk Kunden reaktivieren',
            'description': f'{len(at_risk_customers)} wertvolle Kunden sind inaktiv',
            'priority': 'high',
            'action_url': url_for('customers.list')
        })
    
    # 3. Champions belohnen
    if segments['Champions'] > 0:
        recommendations.append({
            'icon': '⭐',
            'title': 'Champion-Kunden belohnen',
            'description': f'{segments["Champions"]} Top-Kunden verdienen besondere Aufmerksamkeit',
            'priority': 'medium',
            'action_url': url_for('customers.list')
        })
    
    # 4. Potenzial-Kunden entwickeln
    if segments['Potential'] > 0:
        recommendations.append({
            'icon': '🎯',
            'title': 'Upselling-Chancen nutzen',
            'description': f'{segments["Potential"]} Kunden mit hohem Umsatzpotenzial',
            'priority': 'medium',
            'action_url': url_for('customers.list')
        })
    
    return render_template('index_tabbed.html',
                         now=now,
                         stats=stats,
                         lifecycle_stats=lifecycle_stats,
                         top_customers=top_customers,
                         recent_contacts=recent_contacts,
                         recent_orders=recent_orders,
                         channel_counts=channel_counts,
                         at_risk_customers=at_risk_customers,
                         pipeline=pipeline,
                         pipeline_revenue=pipeline_revenue,
                         forecast_next_month=forecast_next_month,
                         growth_rate=growth_rate * 100,
                         segments=segments,
                         recommendations=recommendations)


@bp.route('/search')
@login_required
def search():
    """Globale Suche über alle Entitäten"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('search_results.html', 
                             customers=[], orders=[], contacts=[], query='')
    
    # Suche Kunden
    customers = Customer.query.filter(
        or_(
            Customer.first_name.ilike(f'%{query}%'),
            Customer.last_name.ilike(f'%{query}%'),
            Customer.email.ilike(f'%{query}%'),
            Customer.phone.ilike(f'%{query}%'),
            Customer.company.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    # Suche Bestellungen
    orders = Order.query.filter(
        Order.order_number.ilike(f'%{query}%')
    ).limit(20).all()
    
    # Suche Kontakte
    contacts = Contact.query.filter(
        or_(
            Contact.subject.ilike(f'%{query}%'),
            Contact.notes.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    return render_template('search_results.html',
                         customers=customers,
                         orders=orders,
                         contacts=contacts,
                         query=query)
