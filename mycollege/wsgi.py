# mycollege/wsgi.py
"""
WSGI config for mycollege project.

It exposes the WSGI callable as a module-level variable named ``application``.
This file is used by Django's built-in server and most production WSGI servers.
"""

import os
from django.core.wsgi import get_wsgi_application

# Point to your project's settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mycollege.settings")

application = get_wsgi_application()
