"""
Here all CRUD integration forms
and separate GR contacts initializer form
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DateField,BooleanField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration
from datetime import date
from wtforms.fields.html5 import DateField
from app.grhub.grmonster import GrMonster
import requests
from flask import current_app
from ftplib import FTP
from alphabet_detector import AlphabetDetector
from datetime import datetime, timedelta

ad = AlphabetDetector()

class CustomValidators(object):

    def validate_start_date(self, start_date):
        aval_date = (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        if str(start_date.data) >= aval_date:
            raise ValidationError((f'Начальная дата должна быть не позже {aval_date}'))

    def validate_integration_name(self, integration_name):
        if not all([ch.isalnum() or ch=='_' for ch in integration_name.data]):
            raise ValidationError(('Название интеграции может содержать только латинские буквы, цифры и нижнее подчеркивание'))
        elif not ad.only_alphabet_chars(integration_name.data, "LATIN"):
            raise ValidationError(('Название интеграции может содержать только латинские буквы, цифры и нижнее подчеркивание'))
    def validate_api_key(self, api_key):
        r = requests.get('https://api.getresponse.com/v3/accounts', \
                    headers={'X-Auth-Token': 'api-key {}'.format(api_key.data)})
        if r.status_code != 200 :
            raise ValidationError(('Нет контакта с GetResponse'))

    def validate_metrika_counter_id(self, metrika_counter_id):
        headers = {'Authorization':'OAuth {}'.format(self.metrika_key.data)}
        ROOT = 'https://api-metrika.yandex.net/'
        url = ROOT+'management/v1/counter/{}/logrequests'.format(metrika_counter_id.data)
        r = requests.get(url, headers=headers)
        if r.status_code != 200 :
            raise ValidationError(('Нет контакта с Yandex Метрикой. Проверьте ключ и счетчик'))

    def validate_ftp_pass(self, ftp_pass):
        grmonster = GrMonster(api_key = '',\
                                 ftp_login = self.ftp_login.data, \
                                 ftp_pass = self.ftp_pass.data)
        try:
            grmonster = GrMonster(api_key = '',\
                                     ftp_login = self.ftp_login.data, \
                                     ftp_pass = self.ftp_pass.data)
        except Exception as err:
            print(err)
            raise ValidationError(('Нет контакта с FTP. Проверьте логин и пароль'))

# this form class handles the both - C and U integration
class EditIntegration(FlaskForm,CustomValidators):
    integration_name = StringField("Название интеграции", validators=[DataRequired()])
    api_key = StringField('API ключ GetResponse', validators=[DataRequired()])
    ftp_login = StringField('Логин GR FTP', validators=[DataRequired()])
    ftp_pass = StringField('Пароль GR FTP', validators=[DataRequired()])
    metrika_key = StringField('Ключ Яндекс Метрики', validators=[DataRequired()])
    metrika_counter_id = StringField('ID счетчика Яндекс Метрики', validators=[DataRequired()])
    start_date = DateField('От', validators=[DataRequired()])
    auto_load = BooleanField('Автозагрузка')
    submit = SubmitField("Отправить")

class LinkGenerator(FlaskForm):
    link = StringField("Введите ссылку", validators=[DataRequired()])
    submit = SubmitField("Получить ссылку")


class GrInitializer(FlaskForm, CustomValidators):
    integration_name = StringField("Название интеграции", validators=[DataRequired()])
    api_key = StringField('API ключ GetResponse', validators=[DataRequired()])
    ftp_login = StringField('Логин GR FTP', validators=[DataRequired()])
    ftp_pass = StringField('Пароль GR FTP', validators=[DataRequired()])
    submit = SubmitField("Отправить")
