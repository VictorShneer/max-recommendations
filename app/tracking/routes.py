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
from functools import wraps

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

# then in your view
@bp.route('/tracking/test', methods=['GET'])
@support_jsonp
def test():
    print('try me!!!!!!!!')
    return jsonify({"foo":"bar"})

# @bp.route('/tracking/<integration_id>', methods=['POST','GET'])
# @current_user_own_integration
# @login_required
# def get_tracking_code(integration_id):
#     req = request.get_json()
#
#     print(req)
#
#     res = make_response(jsonify({"message": "OK"}), 200)
#
#     return res
#
#
# @bp.route('/trackingTest', methods=['POST','GET'])
# @login_required
# def tracking_test():
#     print('hui')
#     return render_template('trackingTest.html')
