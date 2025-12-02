"""
Seeder Script - Generiert Beispieldaten für das CRM
Erstellt: >10 Kunden, >50 Bestellungen, >50 Kontakte
"""
from datetime import datetime, timedelta
import random
from faker import Faker

from app import create_app
from models import db, User, Customer, Product, Order, OrderItem, Contact


def seed_database():
    """Erstellt alle Beispieldaten"""
    app = create_app('development')
    
    with app.app_context():
        print("🌱 Starte Seeding...")
        
        # Lösche alte Daten (Optional)
        print("   Lösche alte Daten...")
        db.drop_all()
        db.create_all()
        
        fake = Faker('de_AT')
        
        # 1. Benutzer erstellen
        print("   Erstelle Benutzer...")
        admin = User(name='Admin', email='admin@crm.local', role='Admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        chef = User(name='Mag. Sarah König', email='koenig@crm.local', role='Chef')
        chef.set_password('chef123')
        db.session.add(chef)
        
        mitarbeiter1 = User(name='Lukas Graf', email='graf@crm.local', role='Mitarbeiter')
        mitarbeiter1.set_password('user123')
        db.session.add(mitarbeiter1)
        
        mitarbeiter2 = User(name='Anna Weber', email='weber@crm.local', role='Mitarbeiter')
        mitarbeiter2.set_password('user123')
        db.session.add(mitarbeiter2)
        
        db.session.commit()
        users = [admin, chef, mitarbeiter1, mitarbeiter2]
        print(f"   ✓ {len(users)} Benutzer erstellt")
        
        # 2. Produkte erstellen
        print("   Erstelle Produkte...")
        products_data = [
            ('PROD-001', 'Software-Lizenz Enterprise', 499.00, 'Software'),
            ('PROD-002', 'Consulting Stunde', 120.00, 'Dienstleistung'),
            ('PROD-003', 'Server-Hosting Monat', 89.00, 'Hosting'),
            ('PROD-004', 'Website-Design Paket', 1500.00, 'Webdesign'),
            ('PROD-005', 'SEO Optimierung', 750.00, 'Marketing'),
            ('PROD-006', 'Hardware Workstation', 2500.00, 'Hardware'),
            ('PROD-007', 'Wartungsvertrag Jahr', 1200.00, 'Wartung'),
            ('PROD-008', 'Schulung Tag', 800.00, 'Training'),
            ('PROD-009', 'Cloud Storage 100GB', 29.00, 'Cloud'),
            ('PROD-010', 'Backup-Service Monat', 45.00, 'Backup'),
        ]
        
        products = []
        for sku, name, price, category in products_data:
            product = Product(
                sku=sku,
                name=name,
                base_price=price,
                category=category,
                is_active=True
            )
            db.session.add(product)
            products.append(product)
        
        db.session.commit()
        print(f"   ✓ {len(products)} Produkte erstellt")
        
        # 3. Kunden erstellen (15 Kunden)
        print("   Erstelle Kunden...")
        customers = []
        cities = ['Wien', 'Graz', 'Linz', 'Salzburg', 'Innsbruck', 'Klagenfurt', 'Wels', 'St. Pölten']
        
        for i in range(15):
            city = random.choice(cities)
            customer = Customer(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                company=fake.company() if random.random() > 0.3 else None,
                address=fake.street_address(),
                city=city,
                postal_code=fake.postcode(),
                country='Österreich',
                notes=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
                rating=random.randint(1, 5) if random.random() > 0.3 else None,
                created_at=fake.date_time_between(start_date='-2y', end_date='now')
            )
            db.session.add(customer)
            customers.append(customer)
        
        db.session.commit()
        print(f"   ✓ {len(customers)} Kunden erstellt")
        
        # 4. Bestellungen erstellen (60 Bestellungen)
        print("   Erstelle Bestellungen...")
        orders = []
        statuses = ['Offen', 'Bezahlt', 'Bezahlt', 'Bezahlt', 'Storniert']  # Mehr Bezahlt
        
        for i in range(60):
            customer = random.choice(customers)
            order_date = fake.date_time_between(start_date='-1y', end_date='now')
            
            order_number = f'A-{2024}{str(i+1).zfill(4)}'
            status = random.choice(statuses)
            
            order = Order(
                order_number=order_number,
                customer_id=customer.id,
                order_date=order_date,
                status=status,
                total_amount=0,  # Wird später berechnet
                created_at=order_date
            )
            db.session.add(order)
            db.session.flush()  # Um ID zu bekommen
            
            # Bestellpositionen (1-5 pro Bestellung)
            num_items = random.randint(1, 5)
            total = 0
            
            for j in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                unit_price = product.base_price
                
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=random.choice([0, 0, 0, 5, 10])  # Manchmal Rabatt
                )
                db.session.add(item)
                total += item.line_total
            
            order.total_amount = total
            orders.append(order)
        
        db.session.commit()
        print(f"   ✓ {len(orders)} Bestellungen erstellt")
        
        # 5. Kontakte erstellen (70 Kontakte)
        print("   Erstelle Kontakte...")
        channels = ['Telefon', 'E-Mail', 'Meeting', 'Chat']
        subjects = [
            'Angebotsnachfrage',
            'Rückfrage zur Rechnung',
            'Technischer Support',
            'Terminvereinbarung',
            'Projektbesprechung',
            'Feedback zur Dienstleistung',
            'Verlängerung Vertrag',
            'Liefertermin',
            'Produktinformation',
            'Reklamation'
        ]
        
        contacts = []
        for i in range(70):
            customer = random.choice(customers)
            user = random.choice(users[1:])  # Nicht Admin
            contact_time = fake.date_time_between(start_date='-6m', end_date='now')
            
            contact = Contact(
                customer_id=customer.id,
                user_id=user.id,
                channel=random.choice(channels),
                subject=random.choice(subjects),
                notes=fake.text(max_nb_chars=150) if random.random() > 0.3 else None,
                contact_time=contact_time,
                duration_minutes=random.randint(5, 60) if random.random() > 0.5 else None,
                rating=random.randint(1, 5) if random.random() > 0.7 else None,  # Nur manchmal Bewertung
                created_at=contact_time
            )
            db.session.add(contact)
            contacts.append(contact)
        
        db.session.commit()
        print(f"   ✓ {len(contacts)} Kontakte erstellt")
        
        print("\n✅ Seeding abgeschlossen!")
        print(f"\n📊 Zusammenfassung:")
        print(f"   - Benutzer: {len(users)}")
        print(f"   - Kunden: {len(customers)}")
        print(f"   - Produkte: {len(products)}")
        print(f"   - Bestellungen: {len(orders)}")
        print(f"   - Kontakte: {len(contacts)}")
        print(f"\n👤 Login-Daten:")
        print(f"   Admin:       admin@crm.local / admin123")
        print(f"   Chef:        koenig@crm.local / chef123")
        print(f"   Mitarbeiter: graf@crm.local / user123")
        print(f"   Mitarbeiter: weber@crm.local / user123")


if __name__ == '__main__':
    # Faker installieren falls nicht vorhanden
    try:
        from faker import Faker
    except ImportError:
        print("❌ Faker ist nicht installiert!")
        print("   Bitte installieren mit: pip install faker")
        exit(1)
    
    seed_database()
