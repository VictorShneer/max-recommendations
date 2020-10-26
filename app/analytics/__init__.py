"""
this blueprint handle 
every needs related to visitors segmentations
based on behavior on customer site
"""
from flask import Blueprint

bp = Blueprint('analytics', __name__)

from app.analytics import routes
