# main.py

from flask import Blueprint, render_template, redirect, url_for, flash,request, abort
from flask_login import login_required, current_user
from app.models import User
import pandas as pd
from app.main import bp
from app.main.forms import EditIntegration, LinkGenerator
from app.models import Integration, User
from app import db
from app.metrika.secur import current_user_own_integration
from app.models import Notification
from flask import jsonify

@bp.route('/delete_integration', methods=['GET','POST'])
@login_required
def delete_integration():
    integration_id = request.form['integration_id']
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if User.query.filter_by(id = integration.user_id).first() != current_user:
        flash("Ошибка")
        abort(403)
    integration.delete_myself()

    return '<200>'

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

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

    return render_template('user_integrations.html', integrations=integrations)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
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
        user_domain = form.user_domain.data,
        metrika_key = form.metrika_key.data,
        metrika_counter_id = form.metrika_counter_id.data,
        user_id = current_user.id
        )

        db.session.add(integration)
        db.session.flush()

        try:
            ### TODO
            # UUID CUSTOM UNIQUE ID FOR ClickHousE integration
            params = ['-source=hits', '-mode=history']
            params_2 = ['-source=visits', '-mode=history']
            if current_user.get_task_in_progress('init_integration'):
                flash('Нельзя запускать создание больше одной интеграции одновременно!')
                db.session.rollback()
            else:
                # print('launch', current_user.crypto,  integration.id, params)
                # current_user.launch_task('example','test',15)
                current_user.launch_task('init_clickhouse_tables', ('Init integration...'), current_user.crypto,  integration.id, [params,params_2])
                # current_user.launch_task('init_clickhouse_tables', ('Init integration...'), current_user.crypto,  integration.id, params_2)
                # current_user.launch_task('init_clickhouse_tables', ('Init integration...'), )
                db.session.commit()
        except:
            flash("Проблемки..")
            db.session.rollback()
            abort(404)

        db.session.commit()
        flash('You just have add new {} integration '.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))

    return render_template('create_integration.html', form=form)



@bp.route('/edit_integration/<integration_id>', methods = ['GET','POST'])
@login_required
def edit_integration(integration_id):

    form = EditIntegration()
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        flash('Настройка вашего аккаунта еще не закончена')
        return redirect(url_for('main.user_integrations'))

    title = integration.integration_name
    if form.validate_on_submit():
        integration.integration_name = form.integration_name.data
        integration.api_key = form.api_key.data
        integration.user_domain = form.user_domain.data
        integration.metrika_key = form.metrika_key.data
        integration.metrika_counter_id = form.metrika_counter_id.data
        # integration.clickhouse_login = form.clickhouse_login.data
        # integration.clickhouse_password = form.clickhouse_password.data
        # integration.clickhouse_host = form.clickhouse_host.data
        # integration.clickhouse_db = form.clickhouse_db.data
        db.session.commit()
        flash('Изменения сохранены')
    elif request.method == 'GET':
        form.integration_name.data = integration.integration_name
        form.api_key.data = integration.api_key
        form.user_domain.data = integration.user_domain
        form.metrika_key.data = integration.metrika_key
        form.metrika_counter_id.data = integration.metrika_counter_id
        # form.clickhouse_login.data = integration.clickhouse_login
        # form.clickhouse_password.data = integration.clickhouse_password
        # form.clickhouse_host.data = integration.clickhouse_host
        # form.clickhouse_db.data = integration.clickhouse_db
    return render_template("create_integration.html", form=form, title=title)


@bp.route('/link_creation', methods=['GET','POST'])
@login_required
def link_creation():
    form = LinkGenerator()
    if form.validate_on_submit():
        link = form.link.data + "?utm_campaign=&utm_content=&utm_medium=&utm_source={{CONTACT `subscriber_email`}}&utm_term="
        flash('Ваша ссылка: {} '.format(link))
        return render_template('link_creation.html', form=form)
    return render_template('link_creation.html', form=form)

#for metrika examples
@bp.route('/metrika-examples')
def metexample():
    return render_template('metrika_example.html')
