from a2wsgi import ASGIMiddleware

from backend.app.main import app as asgi_app


# Compatibility fallback for Render services that still have a Django-style
# "gunicorn bocatworldcup.wsgi" start command configured in the UI.
application = ASGIMiddleware(asgi_app)
app = application
