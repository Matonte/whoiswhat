"""WSGI entry for production servers: gunicorn wsgi:app"""

from whoiswhat import create_app

app = create_app()
