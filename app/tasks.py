import time
import sys
import requests
from rq import get_current_job
from app import db
from app import create_app
from app.models import Task, Integration,Message, User
from app.clickhousehub.metrica_logs_api import handle_integration
from app.clickhousehub.metrica_logs_api import drop_integration
from app.clickhousehub.clickhouse import get_tables
import concurrent.futures
from app.grhub.grmonster import GrMonster

app = create_app(adminFlag=False)
app.app_context().push()


# TO DO relocate to GrMonster
def post_contact_to_list(email, campaign_id, api_key):
    r = requests.post('https://api.getresponse.com/v3/contacts', \
                        headers = {'X-Auth-Token': 'api-key {}'.format(api_key)}, \
                        json = {'email':email, 'campaign': {'campaignId':campaign_id}})
    return (r.status_code, r.text)


def send_search_contacts_to_gr(search_contacts_list, campaignId, api_key, user_id):
    _set_task_progress(0)
    responses = []
    # for contact_email in search_contacts_list:
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its URL
        future_to_email = {executor.submit(post_contact_to_list, email, campaignId, api_key): email for email in search_contacts_list}
        for idx,future in enumerate(concurrent.futures.as_completed(future_to_email)):
            _set_task_progress(int((idx*100)/len(search_contacts_list)))
            email = future_to_email[future]
            try:
                response_status = future.result()
                responses.append(response_status)
            except Exception as exc:
                print('%r generated an exception: %s' % (email, exc))
            else:
                print('%r address loaded with status %d' % (email, response_status[0]))
    _set_task_progress(100, len(responses), user_id)



def _set_task_progress(progress, comment='', user_id=0):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': comment if comment else progress})
        if  progress >= 100:
            task.complete = True
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            user.send_message(comment)
            user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()

def init_clickhouse_tables(token, counter_id, crypto, id, paramss, user_id, regular_load=False,):
    _set_task_progress(0)
    try:
        for count,params in enumerate(paramss):
            _set_task_progress(50 * count // len(paramss))
            handle_integration(token, counter_id,crypto,id,params)
        if regular_load:
            _set_task_progress(100, 'Ежедневная автоматическая загрузка - Готово', user_id)
        else:
            _set_task_progress(100, 'Создание интеграции - Готово', user_id)
    except Exception as err:
        _set_task_progress(100)
        if not regular_load:
            _set_task_progress(100, 'Создание интеграции - Ошибка', user_id)
            drop_integration(crypto, id)
            Integration.query.filter_by(id = id).first_or_404().delete_myself()
        else:
            _set_task_progress(100, 'Ежедневная автоматическая загрузка - Ошибка', user_id)
        app.logger.info('### init_clickhouse_tables EXCEPTION regular_load={}'.format(regular_load))
        app.logger.error('### Unhandled exception {exc_info}\n{err}'.format(exc_info=sys.exc_info(), err=err))

def fill_encode_email_custom_field_for_subscribers_chunk(id_email_dic_list,grmonster):
    _set_task_progress(33, 'Продолжается инициализация GR аккаунта...')
    grmonster.upsert_every_email_with_hashed_email(id_email_dic_list)
    _set_task_progress(100)

def init_gr_account(api_key, user_id, callback_url):
    _set_task_progress(0)
    grmonster = GrMonster(api_key=api_key, \
                            callback_url=callback_url)
    try:
        grmonster.prepare_GR_account()
    except KeyError as err:
        _set_task_progress(50, f'Инициализация контактов ГР - Ошибка - \n{err}' ,user_id)
    else:
        contacts_id_email_dic_list = grmonster.get_id_email_dic_list()
        length = len(contacts_id_email_dic_list)
        chunks = 1+length // app.config['GR_CHUNK_SIZE']
        estimation = len(contacts_id_email_dic_list) // 5 // 60
        app.logger.info(f'Contacts to instantiate : {length}' + \
                                f'\n{chunks} chunks by 5000 contacts' + \
                                f'\n estimation time is {estimation} minutes')
        user = User.query.filter_by(id=user_id).first()
        while contacts_id_email_dic_list:
            user.launch_task('fill_encode_email_custom_field_for_subscribers_chunk',\
                            'Группа контактов на инициации...',\
                            contacts_id_email_dic_list[:app.config['GR_CHUNK_SIZE']],\
                            grmonster
                            )
            contacts_id_email_dic_list = contacts_id_email_dic_list[app.config['GR_CHUNK_SIZE']:]

    try:
        set_callback_response = grmonster.set_callback_if_not_busy()
    except KeyError as err:
        _set_task_progress(99, f'Создание уведомления - Ошибка - \n{err}' ,user_id)
        _set_task_progress(100, f'Инициализация gr аккаунта - Есть ошибки - \n{err}' ,user_id)
    else:
        _set_task_progress(99, f'Создание уведомления - Успех' ,user_id)
        _set_task_progress(100, f'Инициализация gr аккаунта - Успех' ,user_id)



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
