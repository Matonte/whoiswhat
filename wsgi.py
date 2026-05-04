"""WSGI entry for production servers: gunicorn wsgi:app"""

from contact_advisor import create_app

app = create_app()
