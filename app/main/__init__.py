"""
Main bp
we store he a lot of things
mostly CRUD integration routes
GR initializer process as well
"""
from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes 
