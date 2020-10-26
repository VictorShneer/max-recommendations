from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, make_response, jsonify
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.tracking import bp
import requests
from app.analytics.utils import current_user_own_integration
import traceback
from pprint import pprint
import pandas as pd
import json



@bp.route('/tracking/<integration_id>', methods=['POST','GET'])
@current_user_own_integration
@login_required
def get_tracking_code(integration_id):
    req = request.get_json()

    print(req)

    res = make_response(jsonify({"message": "OK"}), 200)

    return res


@bp.route('/trackingTest', methods=['POST','GET'])
@login_required
def tracking_test():
    print('hui')
    return render_template('trackingTest.html')
