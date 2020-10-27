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

@bp.route('/tracking/test', methods=['GET', 'POST'])
def test():
    print('try me!!!!!!!!')
    req = request.get_json()
    print(req)

    res = make_response(jsonify({"message": "OK"}), 200)

    return res

@bp.route('/tracking/dev', methods=['GET', 'POST'])
def test():
    print('DEV NO CORS')
    req = request.get_json()
    print(req)

    res = make_response(jsonify({"DEV": "SUCCESS"}), 200)

    return res
