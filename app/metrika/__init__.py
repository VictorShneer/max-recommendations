"""
this bp handles every need
related to email marketing performance analysis
"""

from flask import Blueprint

bp = Blueprint('metrika', __name__)

from app.metrika import routes
