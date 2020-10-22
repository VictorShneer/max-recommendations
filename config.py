import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, 'con.env'))


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-!@#-'

    POSTS_PER_PAGE = 10
    MAX_WORKERS = os.environ.get('MAX_WORKERS') or 5

    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                'postgres://xgb_grmax:497eabdajk@postgres76.1gb.ru:5432/xgb_grmax'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    KEY = 'u0bwk7n5i3u9w2g2hndz8yn346x361g0'

    #GR FTP
    GR_FTP_HOST = 'ftp.getresponse360.pl'

    ADMIN_ROLE_TITLE = 'admin'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    #REDIS
    REDISTOGO_URL = os.environ.get('REDISTOGO_URL') or 'redis://'
    GR_CHUNK_SIZE = 1000

    # CLICKHOUSE
    CLICKHOUSE_LOGIN = 'user1'
    CLICKHOUSE_PASSWORD = 'password'
    CLICKHOUSE_HOST = 'rc1b-6wcv9d6xfzgvj459.mdb.yandexcloud.net'
    CERTIFICATE_PATH = 'app/YandexInternalRootCA.crt'
    AUTH = {
        'X-ClickHouse-User': 'user1',
        'X-ClickHouse-Key': 'password'
    }

    #CLICKHOUSE
    KEY_IDENTIFIER = 'aje5j6vfpie6d3hmu344'
    SERVICE_ID = 'aje82uuu3kjjl101v6oj'


    # CALLBACKS
    CALLBACK_URL = '/metrika/callback_add_custom_field/'
    ADMINS = ['implixgr360@gmail.com']

