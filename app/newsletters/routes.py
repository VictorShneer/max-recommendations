from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.newsletters import bp
from app.newsletters.forms import Available_newsletters, \
                                  Available_links, \
                                  Api_key
from app.newsletters.gr_requests import get_newsletters_names,\
                                        get_newsletters_links_for_newsletterId, \
                                        gr_post_wrapped_newsletter
import datetime

@bp.route('/newsletters')
@login_required
def newsletters():
    available_newsletters_form = Available_newsletters()
    available_links_form = Available_links()
    api_key_form = Api_key()
    return render_template('newsletters.html',\
        available_newsletters_form=available_newsletters_form,\
        available_links_form=available_links_form,\
        api_key_form=api_key_form)

@bp.route('/get_newsletters', methods=['POST'])
@login_required
def get_newsletters():
    key = request.json
    response = get_newsletters_names(key)
    return response


@bp.route('/post_wrapped_newsletter', methods=['POST'])
@login_required
def post_wrapped_newsletter():
    timestamp= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    key, newsletter_id, links = request.json['key'], \
                                request.json['newsletterId'], \
                                request.json['links']
    try:
        gr_post_wrapped_newsletter(key, newsletter_id, links)
    except ConnectionRefusedError as err:
        current_user.send_message(f'Ошибка создания письма в GR :( {str(timestamp)}')
        current_user.add_notification('unread_message_count', current_user.new_messages())
        abort(300)
    else:
        current_user.send_message(f'Успех! Черновик с обернутыми ссылками создан в GR. {str(timestamp)}')
        current_user.add_notification('unread_message_count', current_user.new_messages())

    return '<200>'

@bp.route('/get_newsletter_links', methods=['POST'])
@login_required
def get_newsletters_links():
    key = request.json['key']
    newsletterId = request.json['newsletterId']
    response = get_newsletters_links_for_newsletterId(key,newsletterId)
    return response
