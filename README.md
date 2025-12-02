# CRM System

Ein vollständiges Customer Relationship Management System mit Flask und SQLite.

## Features

- **Kundenverwaltung** - Anlegen, Bearbeiten, Löschen von Kunden
- **Bestellungen** - Bestellungen mit Positionen verwalten
- **Interaktionen** - Telefonate, E-Mails, Meetings dokumentieren
- **Reports & KPIs** - Umsatzstatistiken, Top-Kunden, Charts
- **Benutzerrollen** - Chef/Admin vs. Mitarbeiter
- **CSV-Export** - Daten exportieren

## Installation (Lokal)

```bash
# 1. Virtual Environment erstellen
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Datenbank erstellen & Testdaten laden
python seed.py

# 4. App starten
python app.py
```

Öffne http://127.0.0.1:5000

**Login:** admin@crm.local / admin123

## Deployment auf PythonAnywhere

1. Dateien hochladen (ZIP oder Git)
2. Virtual Environment erstellen:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 crmenv
   pip install -r requirements.txt
   ```
3. Web App erstellen (Manual Configuration, Python 3.10)
4. WSGI-Datei konfigurieren (siehe wsgi.py)
5. Datenbank initialisieren: `python seed.py`
6. Reload

## Projektstruktur

```
CRM/
├── app.py              # Flask App Factory
├── config.py           # Konfiguration
├── models.py           # Datenbankmodelle
├── seed.py             # Testdaten Generator
├── requirements.txt    # Dependencies
├── views/              # Blueprints (Routes)
│   ├── auth.py         # Login/Logout/Profil
│   ├── customers.py    # Kundenverwaltung
│   ├── orders.py       # Bestellungen
│   ├── contacts.py     # Interaktionen
│   ├── reports.py      # Reports & Export
│   └── main.py         # Dashboard
├── templates/          # HTML Templates
└── static/             # CSS, JS, Images
```

## Technologien

- Python 3.10+
- Flask 3.0
- SQLite (keine externe DB nötig)
- Bootstrap 5 (CSS)
- Chart.js (Diagramme)

## Testbenutzer

| E-Mail | Passwort | Rolle |
|--------|----------|-------|
| admin@crm.local | admin123 | Admin |
| chef@crm.local | chef123 | Chef |
| maria@crm.local | maria123 | Mitarbeiter |
