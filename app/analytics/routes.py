from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.analytics import bp
from app.analytics.utils import current_user_own_integration


@bp.route('/analytics/<integration_id>/get_data')
@login_required
def analytics_get_data():
    # TODO Getting the data for the table
    pass


@bp.route('/analytics/<integration_id>', methods = ['GET'])
@login_required
@current_user_own_integration
def analytics(integration_id):
    return render_template('analytics.html')
