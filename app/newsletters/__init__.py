from flask import Blueprint

bp = Blueprint('newsletters', __name__)

from app.newsletters import routes
