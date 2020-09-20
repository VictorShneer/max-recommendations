from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.tracking import bp
import requests



@bp.route('/tracking', methods=['POST'])
# @current_user_own_integration
@login_required
def tracking(integration_id):
    pass
