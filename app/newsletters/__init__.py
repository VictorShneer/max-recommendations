"""
this bp 
handle user needs to 
fast wrap all links in GR newsletter
into hashmetrika custom field param
"""
from flask import Blueprint

bp = Blueprint('newsletters', __name__)

from app.newsletters import routes
