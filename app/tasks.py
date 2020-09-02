import time
import sys
import requests
from rq import get_current_job
from app import db
from app.models import Task, Integration
from app import create_app
from app.clickhousehub.metrica_logs_api import handle_integration
from app.clickhousehub.metrica_logs_api import drop_integration
from app.clickhousehub.clickhouse import get_tables

app = create_app(adminFlag=False)
app.app_context().push()


def drop_integration_task(crypto, integration_id):
    _set_task_progress(0)
    try:
        drop_integration(crypto, integration_id)
        _set_task_progress(100)
    except:
    # обработки непредвиденных ошибок
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())

def example(seconds):
    job = get_current_job()
    print('Starting task')
    _set_task_progress(0)
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        _set_task_progress(100 * i // seconds)
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    _set_task_progress(100)
    job.save_meta()
    print('Task completed')

def _set_task_progress(progress, comment=''):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': comment if comment else progress})

        if  progress >= 100:
            task.complete = True
        db.session.commit()

def init_clickhouse_tables(token, counter_id, crypto, id, paramss, regular_load=True):
    try:
        # В ИДЕАЛЕ узнать за какой период есть данные
        # В ИДЕАЛЕ создать таблицы и выгрузить в них данные за указ. пер.
        # В ИДЕАЛЕ проверить все ли ок

        # сейчас - создать таблицы
        # и выгрузить в них все доступные данные
        _set_task_progress(0)
        print('task', crypto, id, paramss)
        for count,params in enumerate(paramss):
            _set_task_progress(100 * count // len(paramss))
            handle_integration(token, counter_id,crypto,id,params)
        _set_task_progress(100)

    except:
        # обработки непредвиденных ошибок
        # вывести уведомлялку, что была проблема
        _set_task_progress(100)
        app.logger.info('init_clickhouse_tables EXCEPTION auto_load={}'.format(auto_load))
        if not regular_load:
            drop_integration(crypto, id)
            Integration.query.filter_by(id = id).first_or_404().delete_myself()
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
