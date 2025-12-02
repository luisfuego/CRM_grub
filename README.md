# CRM System

Ein vollständiges Customer Relationship Management System mit Flask und SQLite.

**Live Demo:** https://luisfuego.pythonanywhere.com (falls deployed)

**GitHub Repository:** https://github.com/luisfuego/CRM_grub

---

## Inhaltsverzeichnis

1. [Features](#features)
2. [Technologien](#technologien)
3. [Datenbankdesign](#datenbankdesign)
4. [Installation (Lokal)](#installation-lokal)
5. [Deployment auf PythonAnywhere](#deployment-auf-pythonanywhere)
6. [Projektstruktur](#projektstruktur)
7. [API-Endpunkte](#api-endpunkte)
8. [Testbenutzer](#testbenutzer)
9. [Screenshots](#screenshots)

---

## Features

### Kernfunktionen
- **Kundenverwaltung** - Vollständiges CRUD (Create, Read, Update, Delete)
- **Bestellungen** - Bestellungen mit mehreren Positionen verwalten
- **Interaktionen** - Telefonate, E-Mails, Meetings dokumentieren
- **Reports & KPIs** - Umsatzstatistiken, Top-Kunden, Charts
- **Benutzerrollen** - Chef/Admin vs. Mitarbeiter (unterschiedliche Rechte)
- **CSV-Export** - Kunden, Bestellungen, Interaktionen exportieren

### Zusatzfunktionen
- **Globale Suche** - Suche über Kunden, Bestellungen und Interaktionen
- **Dashboard mit KPIs** - Umsatz, Kundenanzahl, offene Bestellungen
- **Kundenanalyse** - RFM-Segmentierung, Churn-Risk-Analyse
- **Responsive Design** - Funktioniert auf Desktop und Mobile

---

## Technologien

| Komponente | Technologie | Version |
|------------|-------------|---------|
| Backend | Flask | 3.0.0 |
| Datenbank | SQLite + SQLAlchemy | 3.1.1 |
| Migrationen | Flask-Migrate | 4.0.5 |
| Authentifizierung | Flask-Login | 0.6.3 |
| Frontend | Bootstrap 5 | 5.3.2 |
| Icons | Bootstrap Icons | 1.11.2 |
| Charts | Chart.js | 4.4.0 |
| Python | Python | 3.10+ |

---

## Datenbankdesign

### ER-Diagramm (Entity Relationship)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │       │  customers  │       │  products   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ name        │       │ first_name  │       │ sku         │
│ email       │       │ last_name   │       │ name        │
│ password    │       │ email       │       │ description │
│ role        │       │ phone       │       │ base_price  │
│ is_active   │       │ company     │       │ category    │
│ created_at  │       │ address     │       │ is_active   │
└─────────────┘       │ city        │       └──────┬──────┘
      │               │ postal_code │              │
      │               │ country     │              │
      │               │ notes       │              │
      │               │ rating      │              │
      │               │ created_at  │              │
      │               └──────┬──────┘              │
      │                      │                     │
      │         ┌────────────┴────────────┐        │
      │         │                         │        │
      ▼         ▼                         ▼        ▼
┌─────────────────┐               ┌─────────────────┐
│    contacts     │               │     orders      │
├─────────────────┤               ├─────────────────┤
│ id (PK)         │               │ id (PK)         │
│ customer_id(FK) │               │ order_number    │
│ user_id (FK)    │               │ customer_id(FK) │
│ channel         │               │ order_date      │
│ subject         │               │ status          │
│ notes           │               │ total_amount    │
│ contact_time    │               │ notes           │
│ duration        │               │ created_at      │
│ rating          │               └────────┬────────┘
│ created_at      │                        │
└─────────────────┘                        │
                                           ▼
                               ┌─────────────────────┐
                               │    order_items      │
                               ├─────────────────────┤
                               │ id (PK)             │
                               │ order_id (FK)       │
                               │ product_id (FK)     │
                               │ quantity            │
                               │ unit_price          │
                               └─────────────────────┘
```

### Tabellen-Beschreibung

| Tabelle | Beschreibung | Beziehungen |
|---------|--------------|-------------|
| `users` | Benutzer des Systems | 1:n → contacts |
| `customers` | Kundenstammdaten | 1:n → orders, contacts |
| `products` | Produktkatalog | 1:n → order_items |
| `orders` | Bestellungen | n:1 → customers, 1:n → order_items |
| `order_items` | Bestellpositionen | n:1 → orders, products |
| `contacts` | Kundeninteraktionen | n:1 → customers, users |

### Migrationen

Das Projekt unterstützt Flask-Migrate für Datenbankmigrationen:

```bash
# Migration erstellen
flask db migrate -m "Beschreibung der Änderung"

# Migration anwenden
flask db upgrade

# Migration rückgängig machen
flask db downgrade
```

---

## Installation (Lokal)

### Voraussetzungen

- Python 3.10 oder höher
- pip (Python Package Manager)
- Git

### Schritt-für-Schritt Anleitung

#### 1. Repository klonen

```bash
git clone https://github.com/luisfuego/CRM_grub.git
cd CRM_grub
```

#### 2. Virtual Environment erstellen

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

#### 4. Umgebungsvariablen setzen (optional)

Erstelle eine `.env` Datei:
```bash
SECRET_KEY=dein-geheimer-schluessel-hier
DATABASE_URL=sqlite:///crm.db
FLASK_ENV=development
```

#### 5. Datenbank erstellen & Testdaten laden

```bash
python seed.py
```

Dies erstellt:
- 3 Benutzer (Admin, Chef, Mitarbeiter)
- 20 Kunden mit Kontaktdaten
- 10 Produkte
- 60+ Bestellungen
- 70+ Interaktionen

#### 6. Anwendung starten

```bash
python app.py
```

#### 7. Im Browser öffnen

```
http://127.0.0.1:5000
```

**Login-Daten:** admin@crm.local / admin123

---

## Deployment auf PythonAnywhere

### Voraussetzungen

- GitHub-Account mit Repository: `CRM_grub`
- PythonAnywhere-Account (Free oder Paid)

### Schritt 1: Repository klonen

1. Auf **PythonAnywhere** anmelden
2. Im Dashboard **"Consoles → Bash"** öffnen
3. Repository klonen:
   ```bash
   git clone https://github.com/luisfuego/CRM_grub.git
   ```
4. In das Projekt wechseln:
   ```bash
   cd CRM_grub
   ```

### Schritt 2: Virtuelle Umgebung erstellen

```bash
# Virtualenv erstellen
mkvirtualenv --python=/usr/bin/python3.10 crmenv

# Sicherstellen, dass die Umgebung aktiv ist
workon crmenv

# Dependencies installieren
pip install -r requirements.txt
```

### Schritt 3: Datenbank initialisieren

```bash
# Secret Key setzen
export SECRET_KEY='mein-geheimer-schluessel'

# Datenbank und Testdaten erstellen
python seed.py
```

### Schritt 4: Web-App erstellen

1. Tab **"Web"** öffnen
2. **"Add a new web app"** klicken
3. **"Manual configuration"** auswählen (NICHT "Flask"!)
4. **Python 3.10** wählen

### Schritt 5: Web-App konfigurieren

Im Web-Tab folgende Einstellungen vornehmen:

| Einstellung | Wert |
|-------------|------|
| **Source code** | `/home/DEIN_USERNAME/CRM_grub` |
| **Working directory** | `/home/DEIN_USERNAME/CRM_grub` |
| **Virtualenv** | `/home/DEIN_USERNAME/.virtualenvs/crmenv` |

### Schritt 6: WSGI konfigurieren

1. Im Web-Tab auf den Link zur **WSGI configuration file** klicken
2. **GESAMTEN Inhalt löschen** und folgenden Code einfügen:

```python
import sys
import os

# Projektpfad (ANPASSEN!)
project_home = '/home/DEIN_USERNAME/CRM_grub'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Environment Variables
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'mein-super-geheimer-schluessel-123'
os.environ['DATABASE_URL'] = 'sqlite:///crm.db'

# Flask App importieren
from app import create_app
application = create_app()
```

3. **DEIN_USERNAME** durch deinen PythonAnywhere-Benutzernamen ersetzen!
4. **Speichern**

### Schritt 7: Static Files konfigurieren (optional)

Im Web-Tab unter **"Static files"**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/DEIN_USERNAME/CRM_grub/static` |

### Schritt 8: Web-App starten

1. Im Web-Tab **"Reload"** klicken
2. App öffnen: `https://DEIN_USERNAME.pythonanywhere.com`

### Fehlerbehebung

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `ModuleNotFoundError` | Virtualenv falsch | Pfad in Web-Tab prüfen |
| `no such table: users` | DB nicht initialisiert | `python seed.py` ausführen |
| `SECRET_KEY must be set` | Env Variable fehlt | In WSGI-Datei setzen |
| `TemplateNotFound` | Pfad falsch | Source code Pfad prüfen |
| `500 Internal Server Error` | Verschiedene | Error Log im Web-Tab prüfen |

### Updates deployen

```bash
# In PythonAnywhere Bash Console:
cd CRM_grub
git pull origin main
workon crmenv
pip install -r requirements.txt  # falls neue Dependencies

# Dann im Web-Tab "Reload" klicken
```

---

## Projektstruktur

```
CRM_grub/
│
├── app.py                  # Flask Application Factory
├── config.py               # Konfigurationsklassen (Dev, Prod, Test)
├── models.py               # SQLAlchemy Datenbankmodelle
├── seed.py                 # Testdaten-Generator
├── wsgi.py                 # WSGI-Konfiguration für PythonAnywhere
├── requirements.txt        # Python Dependencies
├── README.md               # Diese Dokumentation
│
├── views/                  # Flask Blueprints (Controller)
│   ├── __init__.py
│   ├── main.py             # Dashboard, Suche
│   ├── auth.py             # Login, Logout, Profil
│   ├── customers.py        # Kundenverwaltung
│   ├── orders.py           # Bestellverwaltung
│   ├── contacts.py         # Interaktionen
│   └── reports.py          # Reports, KPIs, Export
│
├── templates/              # Jinja2 HTML-Templates
│   ├── base.html           # Basis-Layout mit Navigation
│   ├── index_tabbed.html   # Dashboard mit Tabs
│   ├── search_results.html # Suchergebnisse
│   │
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   └── edit_profile.html
│   │
│   ├── customers/
│   │   ├── list.html       # Kundenübersicht
│   │   ├── detail.html     # Kundendetail
│   │   └── form.html       # Kunde anlegen/bearbeiten
│   │
│   ├── orders/
│   │   ├── list.html       # Bestellübersicht
│   │   ├── detail.html     # Bestelldetail
│   │   ├── form.html       # Neue Bestellung
│   │   └── edit.html       # Bestellung bearbeiten
│   │
│   ├── contacts/
│   │   ├── list.html       # Interaktionsübersicht
│   │   ├── detail.html     # Interaktionsdetail
│   │   └── form.html       # Interaktion anlegen
│   │
│   ├── reports/
│   │   └── dashboard.html  # Reports & KPIs
│   │
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
└── static/
    └── css/
        └── style.css       # Custom CSS Styles
```

---

## API-Endpunkte

### Authentifizierung

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET/POST | `/auth/login` | Login-Seite |
| GET | `/auth/logout` | Logout |
| GET/POST | `/auth/register` | Registrierung |
| GET | `/auth/profile` | Benutzerprofil |
| GET/POST | `/auth/profile/edit` | Profil bearbeiten |

### Dashboard

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/` | Dashboard mit KPIs |
| GET | `/search?q=` | Globale Suche |

### Kunden

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/customers/` | Kundenübersicht |
| GET | `/customers/<id>` | Kundendetail |
| GET/POST | `/customers/new` | Kunde anlegen |
| GET/POST | `/customers/<id>/edit` | Kunde bearbeiten |
| POST | `/customers/<id>/delete` | Kunde löschen |

### Bestellungen

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/orders/` | Bestellübersicht |
| GET | `/orders/<id>` | Bestelldetail |
| GET/POST | `/orders/new` | Bestellung anlegen |
| GET/POST | `/orders/<id>/edit` | Bestellung bearbeiten |
| POST | `/orders/<id>/add_item` | Position hinzufügen |
| POST | `/orders/<id>/remove_item/<item_id>` | Position entfernen |
| POST | `/orders/<id>/delete` | Bestellung löschen |

### Interaktionen

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/contacts/` | Interaktionsübersicht |
| GET | `/contacts/<id>` | Interaktionsdetail |
| GET/POST | `/contacts/new` | Interaktion anlegen |
| GET/POST | `/contacts/<id>/edit` | Interaktion bearbeiten |
| POST | `/contacts/<id>/delete` | Interaktion löschen |

### Reports & Export

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/reports/` | Reports Dashboard |
| GET | `/reports/export/customers` | Kunden als CSV |
| GET | `/reports/export/orders` | Bestellungen als CSV |
| GET | `/reports/export/contacts` | Interaktionen als CSV |

---

## Testbenutzer

Nach Ausführung von `python seed.py` sind folgende Benutzer verfügbar:

| E-Mail | Passwort | Rolle | Rechte |
|--------|----------|-------|--------|
| admin@crm.local | admin123 | Admin | Vollzugriff |
| chef@crm.local | chef123 | Chef | Vollzugriff + Bewertungen sehen |
| maria@crm.local | maria123 | Mitarbeiter | Nur eigene Interaktionen |

### Rollenberechtigungen

| Aktion | Admin | Chef | Mitarbeiter |
|--------|-------|------|-------------|
| Kunden verwalten | ✅ | ✅ | ✅ |
| Bestellungen verwalten | ✅ | ✅ | ✅ |
| Interaktionen - eigene | ✅ | ✅ | ✅ |
| Interaktionen - alle sehen | ✅ | ✅ | ❌ |
| Kundenbewertungen sehen | ✅ | ✅ | ❌ |
| Benutzer verwalten | ✅ | ❌ | ❌ |
| Daten löschen | ✅ | ✅ | ❌ |

---

## Screenshots

### Dashboard
Das Dashboard zeigt alle wichtigen KPIs auf einen Blick:
- Gesamtumsatz, Kunden, Bestellungen
- Umsatz-Trend (Chart)
- Letzte Aktivitäten
- Kundensegmentierung

### Kundenverwaltung
- Übersichtliche Kundenliste mit Suche und Filter
- Kundendetail mit Bestellhistorie und Interaktionen
- Quick-Actions für häufige Aktionen

### Bestellungen
- Status-basierte Filterung (Offen, Bezahlt, Storniert)
- Positionen hinzufügen/entfernen
- Automatische Berechnung der Gesamtsumme

### Reports
- Umsatzstatistiken mit Charts
- Top-Kunden nach Umsatz
- Export-Funktionen für alle Daten

---

## Lizenz

Dieses Projekt wurde im Rahmen des Unterrichts an der HTL TGM Wien erstellt.

**Schule:** TGM - Die Schule der Technik  
**Klasse:** 5BHWII  
**Fach:** SWP (Softwareentwicklungsprojekt)  
**Jahr:** 2024/2025

---

## Kontakt

Bei Fragen oder Problemen:
- GitHub Issues: https://github.com/luisfuego/CRM_grub/issues
