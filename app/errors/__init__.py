"""
This bp catch errors like 404, 500
and view user nice and pretty pages 
"""
from flask import Blueprint

bp = Blueprint('errors', __name__)

from app.errors import handlers