import time
import sys
import requests
import datetime
from rq import get_current_job
from app import db
from app import create_app
from app.models import Task, Integration,Message, User
from app.clickhousehub.metrica_logs_api import handle_integration
from app.clickhousehub.metrica_logs_api import drop_integration
from app.clickhousehub.clickhouse import get_tables
import concurrent.futures
from app.grhub.grmonster import GrMonster
from app.clickhousehub.clickhouse import get_dbs
from app.clickhousehub.clickhouse_custom_request import create_ch_db
from app.clickhousehub.clickhouse_custom_request import give_user_grant
from app.clickhousehub.clickhouse_custom_request import request_iam


app = create_app(adminFlag=False)
app.app_context().push()


def send_search_contacts_to_gr_ftp(contacts_list, external_name, grmonster, user_id):
    _set_task_progress(0)
    grmonster.store_external_segment_from_list(contacts_list, external_name)
    _set_task_progress(100, 'hey ftp done', user_id)
def assign_crypto_to_user_id(admin_user_id, user_id, crypto):
    print(type(user_id))
    print()
    _set_task_progress(0)
    # check if db already exists
    if crypto in get_dbs():
        _set_task_progress(100,'ERROR db with this name already exists, dog', admin_user_id)
        return -1
    # get user from db by id or except
    try:
        user = User.query.filter_by(id=user_id).one()
    except Exception as e:
        _set_task_progress(100,'ERROR No user was foung for {}'.format(user_id), admin_user_id)
        return -1
    # check if user already got crypto
    if user.crypto != None:
        _set_task_progress(100,'ERROR This user already set up, dog', admin_user_id)
        return -1
    # assign crypto if it unique
    try:
        user.crypto = crypto
        db.session.commit()
    except Exception as e:
        _set_task_progress(100,'ERROR {} - this crypto already exists'.format(crypto), admin_user_id)
        return -1
    # now let's create clickhouse db
    # and
    # give user grant access to crypto db
    try:
        _set_task_progress(50, 'Пока все ОК! Запрашиваю токен и создаю базы данных')
        # dont forget to update iam token
        iam_token = request_iam()
        if not iam_token:
            raise Exception('ERROR Failed to request iam')
        create_ch_db(crypto)
        give_user_grant('user1', crypto) ## # TODO: drop hardcode use config user name
    except Exception as err:
        user.crypto = None
        db.session.commit()
        _set_task_progress(100,'ERROR \n' + str(err) + '\nsmth went wrong dog :(( try again later..', admin_user_id)
        return -1

    _set_task_progress(100, f'Победа - {user.email} присвоен {user.crypto}', admin_user_id)
    app.logger.info('### Done!')


def send_search_contacts_to_gr(search_contacts_list, campaignId, api_key, user_id):
    _set_task_progress(0)
    success_load_count = 0
    grmonster = GrMonster(api_key, '')
    # for contact_email in search_contacts_list:
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its URL
        future_to_email = {executor.submit(grmonster.post_contact_to_list, email, campaignId): email for email in search_contacts_list}
        for idx,future in enumerate(concurrent.futures.as_completed(future_to_email)):
            _set_task_progress(int((idx*100)/len(search_contacts_list)))
            email = future_to_email[future]
            try:
                response = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (email, exc))
            else:
                success_load_count+=1
                print('%r address loaded with status %d' % (email, response.status_code))
    report_string = f'Загружено контатов в GR: {success_load_count} из {len(search_contacts_list)}'
    _set_task_progress(100, report_string, user_id)



def _set_task_progress(progress, comment='', user_id=0):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': comment if comment else \
                                                            str(progress) + '%'})
        if  progress >= 100:
            task.complete = True
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            timestamp= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user.send_message(f'{str(timestamp)} : {comment} ')
            user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()

def init_clickhouse_tables(token, counter_id, crypto, id, paramss, user_id, regular_load=False):
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

    # callbacks and ftp folders init
    if not regular_load:
        try:
            integration = Integration.query.filter_by(id = id).first()
            grmonster = GrMonster(api_key=integration.api_key, \
                                    callback_url=integration.callback_url, \
                                    ftp_login = integration.ftp_login, \
                                    ftp_pass = integration.ftp_pass)
            set_callback_response = grmonster.set_callback_if_not_busy()
            grmonster.init_ftp_folders()
        except KeyError as err:
            _set_task_progress(100, f'Создание уведомления - Ошибка - \n{err}' ,user_id)
        else:
            _set_task_progress(100, f'Создание уведомления - Успех' ,user_id)

#legacy ???
def fill_encode_email_custom_field_for_subscribers_chunk(id_email_dic_list,grmonster):
    _set_task_progress(33, 'Продолжается инициализация GR аккаунта...')
    grmonster.upsert_every_email_with_hashed_email(id_email_dic_list)
    _set_task_progress(100)

#legacy ???
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


