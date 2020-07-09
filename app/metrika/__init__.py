from flask import Blueprint

bp = Blueprint('metrika', __name__)

from app.metrika import routes
