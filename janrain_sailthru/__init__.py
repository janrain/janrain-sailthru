"""Flask application setup."""
import flask
import logging
import logging.handlers
from .config import apply_configuration
from .routes import add_routes

app = flask.Flask(__name__)
apply_configuration(app)
add_routes(app)
