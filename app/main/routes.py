"""
main routes
CRUD integration
GR initializer
profile
"""
from flask import Blueprint, render_template, redirect, url_for, flash,request, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Message,Integration,Notification
import pandas as pd
from app.main import bp
from app.main.forms import EditIntegration, LinkGenerator, GrInitializer
from app import db
from app.metrika.secur import current_user_own_integration
from flask import jsonify
from app.clickhousehub.metrica_logs_api import drop_integration
from wtforms.fields.html5 import DateField
import datetime
from app.auth.email import send_password_reset_email
from app.grhub.grmonster import GrMonster
from app.main.utils import run_integration_setup
from app.main.utils import plan_init_gr_contacts
from app.auth.forms import ResetPasswordRequestForm,ChangeEmailForm

@bp.route('/delete_integration', methods=['GET','POST'])
@login_required
def delete_integration():
    integration_id = request.form['integration_id']
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if User.query.filter_by(id = integration.user_id).first() != current_user:
        flash("Ошибка")
        abort(403)
    # disable gr callback
    grmonster = GrMonster(api_key=integration.api_key, callback_url=integration.callback_url)
    try:
        grmonster.disable_callback()
    except ConnectionRefusedError:
        current_app.logger.info('Callback already disabled')
        pass
    # heroku db delete
    integration.delete_myself()
    # clickhouse db delete
    drop_integration(current_user.crypto, integration_id)

    return '<200>'

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html')

@bp.route('/admin')
@login_required
def admin():
    if current_user.email == 'george@mail.ru':
        list_users = []
        users = User.query.all()
        for user in users:
            list_users.append(str('Name: ' + user.name + ' Email: ' + user.email))
        print (list_users)
        pands_users = pd.DataFrame(list_users)
        pands_users.columns = ['Users']
        return render_template('admin.html', tables=[pands_users.to_html(classes='data', index=False)], titles=pands_users.columns.values)
    else:
        return render_template('index.html')

@bp.route('/user_integrations', methods=['GET'])
@login_required
def user_integrations():
    user = User.query.filter_by(id=current_user.id).first()
    integrations = user.integrations.all()
    tasks = current_user.get_tasks_in_progress()
    return render_template('user_integrations.html', integrations=integrations)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    current_user.last_notification_view_time = datetime.datetime.utcnow()
    current_user.add_notification('unread_notification_count', 0)
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.order_by(Notification.timestamp.asc()) # .filter(Notification.timestamp > since)
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@bp.route('/create_integration', methods=['GET','POST'])
@login_required
def create_integration():
    if current_user.crypto is None:
        flash('Настройка вашего аккаунта еще не закончена')
        return redirect(url_for('main.user_integrations'))
    form = EditIntegration()
    if form.validate_on_submit():
        integration = Integration(
        integration_name = form.integration_name.data,
        api_key = form.api_key.data,
        ftp_login = form.ftp_login.data,
        ftp_pass= form.ftp_pass.data,
        metrika_key = form.metrika_key.data,
        metrika_counter_id = form.metrika_counter_id.data,
        auto_load = form.auto_load.data,
        user_id = current_user.id
        )
        db.session.add(integration)
        db.session.flush()
        integration.set_callback_url(request.url_root)
        try:
            run_integration_setup(integration, form.start_date.data)
        except Exception as err:
            flash("Что-то пошло не так..")
            current_app.logger.info(err)
            db.session.rollback()
            abort(404)

        db.session.commit()
        flash('Запущено создание {}'.format(integration.integration_name))
        
        return redirect(url_for('main.user_integrations'))

    return render_template('create_integration.html', form=form)

# this route handle GR initialization with out YM keys and counters
@bp.route('/gr_init', methods = ['GET','POST'])
@login_required
def gr_init():
    form = GrInitializer()
    if form.validate_on_submit():
        integration = Integration(
        integration_name = form.integration_name.data,
        api_key = form.api_key.data,
        ftp_login = form.ftp_login.data,
        ftp_pass = form.ftp_pass.data,
        user_id = current_user.id
        )
        db.session.add(integration)
        db.session.flush()
        integration.set_callback_url(request.url_root)
        try:
            plan_init_gr_contacts(integration, current_user)
        except Exception as err:
            flash("Проблемки..")
            current_app.logger.info(err)
            db.session.rollback()
            abort(404)
        return redirect(url_for('main.user_integrations'))
    return render_template('create_integration.html', form=form)

@bp.route('/edit_integration/<integration_id>', methods = ['GET','POST'])
@login_required
def edit_integration(integration_id):

    form = EditIntegration()
    form.metrika_key.render_kw = {'readonly': True}
    form.metrika_counter_id.render_kw = {'readonly':True}
    form.api_key.render_kw = {'readonly':True}
    form.ftp_login.render_kw = {'readonly':True}
    form.ftp_pass.render_kw = {'readonly':True}
    del form.start_date
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        flash('Настройка вашего аккаунта еще не закончена')
        return redirect(url_for('main.user_integrations'))

    title = integration.integration_name
    if form.validate_on_submit():
        integration.integration_name = form.integration_name.data
        integration.api_key = form.api_key.data
        integration.auto_load = form.auto_load.data
        db.session.commit()
        flash('Изменения сохранены')
    elif request.method == 'GET':
        form.integration_name.data = integration.integration_name
        form.api_key.data = integration.api_key
        form.ftp_login.data = integration.ftp_login
        form.ftp_pass.data = integration.ftp_pass
        form.metrika_key.data = integration.metrika_key
        form.metrika_counter_id.data = integration.metrika_counter_id
        form.auto_load.data = integration.auto_load
    return render_template("create_integration.html",\
                            form=form,\
                            title=title)

@bp.route('/link_creation', methods=['GET','POST'])
@login_required
def link_creation():
    form = LinkGenerator()
    if form.validate_on_submit():
        print('hey')
        input_link = form.link.data.strip()
        last_sym = input_link[-1:]
        if (input_link.find('?') == -1):
            link = input_link + "?mxm={CUSTOM 'hash_metrika'}"
        else:
            if (last_sym == "?" or last_sym == "&"):
                link = input_link + "mxm={CUSTOM 'hash_metrika'}"
            else:
                link = input_link + "&mxm={CUSTOM 'hash_metrika'}"
        flash('Ваша ссылка: {} '.format(link))
        return render_template('link_creation.html', form=form)
    return render_template('link_creation.html', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    reset_password_request_form = ResetPasswordRequestForm()
    reset_password_request_form.email.render_kw = {'readonly': True, 'value': current_user.email}
    change_email_form = ChangeEmailForm()
    user = User.query.filter_by(id=current_user.id).first()   
    if reset_password_request_form.validate_on_submit() and reset_password_request_form.submit.data:
        print(reset_password_request_form.submit.data)
        user = User.query.filter_by(email=reset_password_request_form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Проверьте почту для сброса пароля')
        return redirect(url_for('main.profile'))
    if change_email_form.validate_on_submit() and change_email_form.submit_new_email.data:
        user.email = change_email_form.email.data
        db.session.commit()
        flash('Email изменен')
        return redirect(url_for('main.profile'))
    return render_template('profile.html',\
                            reset_password_request_form = reset_password_request_form,\
                            change_email_form = change_email_form)

#for documentation
@bp.route('/documentation')
def documentation():
    return render_template('documentation.html')

#for documentation
@bp.route('/documentation/api_key_from_ym')
def api_key_from_ym():
    return render_template('doc_api_key_from_ym.html')
