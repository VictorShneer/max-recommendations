from datetime import date, datetime, timedelta
from flask import url_for, redirect, flash
from app.models import Task, Integration
from app import db
from flask_login import current_user
from app.grhub.grmonster import GrMonster
import math

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

def plan_init_gr_contacts(integration_obj, user):
    grmonster = GrMonster(api_key=integration_obj.api_key,\
                            ftp_login=integration_obj.ftp_login,\
                            ftp_pass=integration_obj.ftp_pass)
    hash_field_id = grmonster.get_hash_field_id()
    print('hash_field_id', hash_field_id)
    campaigns = grmonster.get_gr_campaigns()
    campaigns_ids_list = [c[0] for c in campaigns]
    search_contacts_total_pages_count = grmonster.get_search_contacts_total_pages_count(hash_field_id, campaigns_ids_list)
    if search_contacts_total_pages_count <= 100:
        user.launch_task('init_gr_contacts_chunk',\
                            f'Проставление служебного поля контактам GR аккаунта',\
                            grmonster,\
                            {'user_id':user.id, 'user_crypto':user.crypto},\
                            search_contacts_total_pages_count)
        db.session.commit()
    else:
        chunk_size = 100
        chunks = math.ceil(search_contacts_total_pages_count/chunk_size)
        for chunk in range(chunks):
            print(f'Проставление служебного поля контактам GR аккаунта {chunk+1}:{chunks}')
            if user:
                user.launch_task('init_gr_contacts_chunk',\
                                    f'Проставление служебного поля контактам GR аккаунта {chunk+1}:{chunks}',\
                                    grmonster,\
                                    {'user_id':user.id, 'user_crypto':user.crypto})
            db.session.commit()
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
        current_user.launch_task('init_clickhouse_tables', \
                                # I need this to check futher if integration is ready
                                (f'Создание базы данных для {integration.integration_name}:{integration.id}'), \
                                integration,
                                {'user_id':current_user.id, 'user_crypto':current_user.crypto},
                                [params,params_2])
        db.session.commit()
        current_user.launch_task('set_callback',\
                                ('Создание callback уведомления'),\
                                integration,\
                                {'user_id':current_user.id, 'user_crypto':current_user.crypto})
        db.session.commit()
        current_user.launch_task('set_ftp',\
                                ('Создание FTP директорий'),\
                                integration,\
                                {'user_id':current_user.id, 'user_crypto':current_user.crypto})
        db.session.commit()
        plan_init_gr_contacts(integration, current_user)