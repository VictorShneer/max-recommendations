#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.models import User
from config import Config
from flask import current_app
from run import init_user_in_clickhouse
from app.clickhousehub.clickhouse import get_dbs
from app.clickhousehub.clickhouse import get_tables
from app.clickhousehub.clickhouse_custom_request import request_iam
from app.clickhousehub.clickhouse_custom_request import give_user_grant
from app.clickhousehub.clickhouse_custom_request import create_ch_db
from app.clickhousehub.clickhouse_custom_request import show_dbs_api
from app.clickhousehub.clickhouse_custom_request import delete_ch_db
from app.clickhousehub.metrica_logs_api import handle_integration



class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    TEST_USER_CRYPTO = 'unit_test_customer'
    TEST_USER_METRICA_TOKEN = 'AgAAAAAOfQzUAAZsVJowlKqpKEEOvNCfAFr78lg'
    TEST_USER_METRICA_COUNTER = '65168419'
    INTEGRATION_ID = '1'
    PARAMS =  ['-source=hits', '-start_date=2020-06-20', '-end_date=2020-07-20']

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig, adminFlag=False)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(name='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_a_request_iam_key(self):
        self.assertTrue(request_iam())
        print('REQUEST iam key SUCCESS')
    
    def test_b_create_ch_db(self):
        create_ch_db(current_app.config['TEST_USER_CRYPTO'])
        self.assertTrue(current_app.config['TEST_USER_CRYPTO'] in show_dbs_api())
        print('CREATING ch db SUCCESS')

    def test_c_grant_permission(self):
        give_user_grant('user1', current_app.config['TEST_USER_CRYPTO'])
        self.assertTrue(current_app.config['TEST_USER_CRYPTO'] in get_dbs())
        print('GRANT premission SUCCESS')

    def test_cc_integrate_with_metrika_api(self):
        handle_integration(current_app.config['TEST_USER_METRICA_TOKEN'],\
                            current_app.config['TEST_USER_METRICA_COUNTER'],\
                            current_app.config['TEST_USER_CRYPTO'],\
                            current_app.config['INTEGRATION_ID'], \
                            current_app.config['PARAMS'])
        self.assertTrue('hits_raw_'+current_app.config['INTEGRATION_ID'] in get_tables())

    def test_d_delete_ch_db(self):
        delete_ch_db(current_app.config['TEST_USER_CRYPTO'])
        self.assertFalse(current_app.config['TEST_USER_CRYPTO'] in get_dbs())
        self.assertFalse(current_app.config['TEST_USER_CRYPTO'] in show_dbs_api())
        print('DELETING db SUCCESS')


if __name__ == '__main__':
    unittest.main(verbosity=3)
