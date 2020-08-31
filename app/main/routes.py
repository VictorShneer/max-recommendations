# main.py
from flask import Blueprint, render_template, redirect, url_for, flash,request, abort, current_app
from flask_login import login_required, current_user
from app.models import User
import pandas as pd
from app.main import bp
from app.main.forms import EditIntegration, LinkGenerator, LoadDataMetrikaToClickhouse
from app.models import Integration, User
from app import db
from app.metrika.secur import current_user_own_integration
from app.models import Notification
from flask import jsonify
from app.clickhousehub.metrica_logs_api import drop_integration
from wtforms.fields.html5 import DateField

@bp.route('/delete_integration', methods=['GET','POST'])
@login_required
def delete_integration():

    # heroku db delete
    integration_id = request.form['integration_id']
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if User.query.filter_by(id = integration.user_id).first() != current_user:
        flash("Ошибка")
        abort(403)
    integration.delete_myself()

    # clickhouse db delete
    drop_integration(current_user.crypto, integration_id)

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
        auto_load = form.auto_load.data,
        start_date = form.start_date.data,
        end_date = form.end_date.data,
        user_id = current_user.id
        )

        db.session.add(integration)
        db.session.flush()

        try:
            ### TODO
            # UUID CUSTOM UNIQUE ID FOR ClickHousE integration
            # -start_date 2016-10-10 -end_date 2016-10-18
            timing = ['-start_date={}'.format(form.start_date.data)]
            if form.end_date.data:
                timing.append('-end_date={}'.format(form.end_date.data))
            params = ['-source=hits', *timing]
            params_2 = ['-source=visits', *timing]
            if current_user.get_task_in_progress('init_clickhouse_tables'):
                flash('Нельзя запускать создание больше одной интеграции одновременно!')
                db.session.rollback()
            else:
                current_user.launch_task('init_clickhouse_tables', ('Init integration...'), current_user.crypto,  integration.id, [params,params_2])
                db.session.commit()
        except:
            flash("Проблемки..")
            db.session.rollback()
            abort(404)

        db.session.commit()
        flash('You just have added new {} integration '.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))

    return render_template('create_integration.html', form=form)



@bp.route('/edit_integration/<integration_id>', methods = ['GET','POST'])
@login_required
def edit_integration(integration_id):

    form = EditIntegration()
    form_to_data_load = LoadDataMetrikaToClickhouse()
    form.metrika_key.render_kw = {'disabled': 'disabled'}
    form.metrika_counter_id.render_kw = {'disabled': 'disabled'}
    del form.start_date
    del form.end_date
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        flash('Настройка вашего аккаунта еще не закончена')
        return redirect(url_for('main.user_integrations'))

    title = integration.integration_name
    if form_to_data_load.validate_on_submit():
        timing = ['-start_date={}'.format(form_to_data_load.start_date.data)]
        if form.end_date.data:
            timing.append('-end_date={}'.format(form_to_data_load.end_date.data))
        params = ['-source=hits', *timing]
        params_2 = ['-source=visits', *timing]

        integration.start_date = form_to_data_load.start_date.data
        integration.end_date = form_to_data_load.end_date.data
        current_user.launch_task('init_clickhouse_tables', ('Инициализация интеграции...'), current_user.crypto,  integration.id, [params,params_2])
        # todo only if success - change integration db records
        db.session.commit()
    elif form.validate_on_submit():
        integration.integration_name = form.integration_name.data
        integration.api_key = form.api_key.data
        integration.user_domain = form.user_domain.data
        db.session.commit()
        flash('Изменения сохранены')
    elif request.method == 'GET':
        form.integration_name.data = integration.integration_name
        form.api_key.data = integration.api_key
        form.user_domain.data = integration.user_domain
        form.metrika_key.data = integration.metrika_key
        form.metrika_counter_id.data = integration.metrika_counter_id
        form.auto_load.data = integration.auto_load

    return render_template("create_integration.html",\
                            form=form,\
                            form_to_data_load=form_to_data_load,\
                            title=title,\
                            start_date=integration.start_date,\
                            end_date=integration.end_date)


@bp.route('/link_creation', methods=['GET','POST'])
@login_required
def link_creation():
    form = LinkGenerator()
    if form.validate_on_submit():
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

#for metrika examples
@bp.route('/metrika-examples')
def metexample():
    return render_template('metrika_example.html')
