"""Production WSGI entry point for the WhoIsHoss microservice."""

from whoishoss import create_app

app = create_app()
