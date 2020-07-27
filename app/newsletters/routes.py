from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.newsletters import bp
from app.newsletters.forms import Available_newsletters, Available_links, \
    Api_key, Converted_links
from app.newsletters.gr_requests import get_newsletters_names


@bp.route('/newsletters')
@login_required
def newsletters():
    available_newsletters_form = Available_newsletters()
    available_links_form = Available_links()
    api_key_form = Api_key()
    converted_links_form = Converted_links()
    return render_template('newsletters.html',\
        available_newsletters_form=available_newsletters_form,\
        available_links_form=available_links_form,\
        api_key_form=api_key_form,\
        converted_links_form=converted_links_form)

@bp.route('/get_newsletters', methods=['POST'])
@login_required
def get_newsletters():
    key = request.json
    response = get_newsletters_names(key)
    return response
