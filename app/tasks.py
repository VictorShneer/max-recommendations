import time
from rq import get_current_job
from app import db
from app.models import Task
from app import create_app
import sys
from app.clickhousehub.metrica_logs_api import handle_integration


app = create_app(adminFlag=False)
app.app_context().push()



def example(seconds):
    job = get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed')

def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()

def init_clickhouse_tables(crypto, id, params):
    try:
        # В ИДЕАЛЕ узнать за какой период есть данные
        # В ИДЕАЛЕ создать таблицы и выгрузить в них данные за указ. пер.

        # сейчас - создать таблицы
        # и выгрузить в них все доступные данные
        _set_task_progress(0)
        print('task', crypto, id, params)
        handle_integration(crypto,id,params)
        _set_task_progress(100)
    except:
    # обработки непредвиденных ошибок
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
