"""
this bp handle everything
related to authentication
"""
from flask import Blueprint

bp = Blueprint('auth', __name__)

from app.auth import routes
