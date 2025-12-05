"""
WSGI Configuration for PythonAnywhere
Kopiere diesen Inhalt in die WSGI-Konfigurationsdatei auf PythonAnywhere
"""
import sys
import os

# Pfad zu deinem Projekt (ANPASSEN!)
project_home = '/home/DEIN_USERNAME/CRM'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Environment Variables
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'aendere-diesen-schluessel-fuer-produktion'

# Flask App importieren
from app import create_app
application = create_app()
