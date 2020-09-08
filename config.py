import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, 'con.env'))


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-!@#-'


    MAX_WORKERS = os.environ.get('MAX_WORKERS') or 20

    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    KEY = 'u0bwk7n5i3u9w2g2hndz8yn346x361g0'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    #REDIS
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    # CLICKHOUSE
    CLICKHOUSE_LOGIN = 'user1'
    CLICKHOUSE_PASSWORD = 'password'
    CLICKHOUSE_HOST = 'rc1b-6wcv9d6xfzgvj459.mdb.yandexcloud.net'
    CLICKHOUSE_DB = 'db1'
    CERTIFICATE_PATH = 'app/YandexInternalRootCA.crt'
    AUTH = {
        'X-ClickHouse-User': 'user1',
        'X-ClickHouse-Key': 'password'
    }

    #CLICKHOUSE
    IAM_TOKEN = 'CggVAgAAABoBMxKABIYdS8OLSL4kZpxfHqxrOJzI-UHgJY9s6qnfTEoW1RV_LpMVznijytPcVbsvKQOcNb6T-hMXNXEHZYW_Y1Qf5zUkQROxQyIUhs1I9_qcoS_6ksM0xyvmbgGIwhk-wkkuWxS-hUchaSKYhY9VpUUGJv20WNHx8Yww3M9yp5aP686KE_pkFH_VAZ9etw1ZoqDwHA4r1sv1JIrb0AffRtcDzUiauUGAwFX3FJt7xu-R9znlb5j089i7sdCGS3rWVIryjL_TH2MGzCiD3cDVeWd0lOpXmRt5uF2dwAUEZdp7C7vX9DoaZ0AJyus5OvKouHGhzjEVgw5OeMN4DlnJrC3Hd4MFB6HX-sGtD3d8N3LuYnltgmuaktqarcCKEeg722FRQ0wtu8uZgIxWHajUjV9JlmtZvaxMhGRWFifWV0pMdv3HFcRFGAFevnVGntHy1fzB62a_WZxS2Mnhvq8KWJNyDhdLr5ifbI4iwS7gUBXe-_dNs6Sw2ZwrD4Tm0iE0l0hBcvjhdS_H3eoUbWlII87vlxTTowZs3kJ4Jyxl1VUMgqhHMbqfq5C9RHb8eghVtZhcDfejmRNWHlBjti76KtZb1tUg17rXAaijSzit9NOnQHLCJlM4_c_CPz2BMEeN9ERh2ctl0G0chVnW9Vzknz0YsZKDUdSa2cDdlWAxlZNPDQmcGiQQhpvf-gUYxuzh-gUiFgoUYWplNWpiOWxwMWRyNGN1Zjlncmg='


    ADMINS = ['implixgr360@gmail.com']
