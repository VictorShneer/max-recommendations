import time
import sys
import requests
from rq import get_current_job
from app import db
from app import create_app
from app.models import Task, Integration
from app.clickhousehub.metrica_logs_api import handle_integration
from app.clickhousehub.metrica_logs_api import drop_integration
from app.clickhousehub.clickhouse import get_tables
from app.metrika.conversion_table_builder import make_clickhouse_pre_aggr_visits


app = create_app(adminFlag=False)
app.app_context().push()


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

def init_clickhouse_tables(token, counter_id, crypto, id, paramss, regular_load=False):
    print()
    _set_task_progress(0)
    print('task', crypto, id, paramss,regular_load)

    for count,params in enumerate(paramss):
        try:
            _set_task_progress(50 * count // len(paramss))
            handle_integration(token, counter_id,crypto,id,params)
        except SystemExit as err:
            app.logger.info('### DATA already in click  -  {}'.format(err))
            continue

    try:
        _set_task_progress(50)
        app.logger.info('### GOOOO make_clickhouse_pre_aggr_visits')
        make_clickhouse_pre_aggr_visits(token, counter_id,crypto,id, regular_load)
        _set_task_progress(75)
        drop_integration(crypto, id, source = 'visits')
        _set_task_progress(100)
    except Exception as err:
        _set_task_progress(100)
        if not regular_load:
            drop_integration(crypto, id)
            Integration.query.filter_by(id = id).first_or_404().delete_myself()
        app.logger.info('### init_clickhouse_tables EXCEPTION regular_load={}'.format(regular_load))
        app.logger.error('### Unhandled exception {exc_info}\n{err}'.format(exc_info=sys.exc_info(), err=err))


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
