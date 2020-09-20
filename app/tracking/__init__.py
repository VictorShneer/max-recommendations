from flask import Blueprint

bp = Blueprint('tracking', __name__)

from app.tracking import routes
