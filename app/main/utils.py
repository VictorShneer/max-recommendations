from datetime import date, datetime, timedelta
from flask import url_for, redirect, flash
from app.models import Task, Integration
from app import db
from flask_login import current_user

def check_if_date_legal(user_date):
    today = str(date.today())
    try:
        datetime.strptime(user_date, '%Y-%m-%d')
    except Exception as err:
        print(user_date)
        return False

    if today < user_date:
        print(today < user_date)
        return False
    return True


def integration_is_ready(function):
    def wrapper(integration_id):
        integration = Integration.query.filter_by(id = integration_id).first_or_404()
        task = Task.query.filter_by(description=f'Создание базы данных для {integration.integration_name}:{integration.id}').first_or_404()
        try:
            if not task.complete:
                flash('Подождите завершения создания интеграции')
                return redirect(url_for('main.user_integrations'))
        except AttributeError:
            print('Task losted')
        else:
            return function(integration_id)
    # Renaming the function name:
    wrapper.__name__ = function.__name__
    return wrapper

def run_integration_setup(integration,start_date):
    timing = ['-start_date={}'.format(start_date)]
    end_date = date.today()
    days = timedelta(2)    
    end_date = end_date - days
    timing.append('-end_date={}'.format(str(end_date)))
    params = ['-source=hits', *timing]
    params_2 = ['-source=visits', *timing]
    if current_user.get_task_in_progress('init_clickhouse_tables'):
        flash('Нельзя запускать создание больше одной интеграции одновременно!')
        db.session.rollback()
    else:
        # current_user.launch_task('init_clickhouse_tables', \
        #                         # I need this to check futher if integration is ready
        #                         (f'Создание базы данных для {integration.integration_name}:{integration.id}'), \
        #                         integration,
        #                         {'user_id':current_user.id, 'user_crypto':current_user.crypto},
        #                         [params,params_2])
        # current_user.launch_task('set_callback',\
        #                         ('Создание callback уведомления'),\
        #                         integration,\
        #                         {'user_id':current_user.id, 'user_crypto':current_user.crypto})
        # current_user.launch_task('set_ftp',\
        #                         ('Создание FTP директорий'),\
        #                         integration,\
        #                         {'user_id':current_user.id, 'user_crypto':current_user.crypto})
        current_user.launch_task('init_gr_contacts',\
                                'Проставление служебного поля контактам GR аккаунта',\
                                integration,\
                                {'user_id':current_user.id, 'user_crypto':current_user.crypto})
        db.session.commit()