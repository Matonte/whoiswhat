"""Production WSGI entry point for the Meeting Advisor microservice."""

from meeting_advisor import create_app

app = create_app()
