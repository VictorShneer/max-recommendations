from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DateField,BooleanField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration
from datetime import date
from wtforms.fields.html5 import DateField
import requests
class EditIntegration(FlaskForm):
    integration_name = StringField("Название интеграции", validators=[DataRequired()])
    api_key = StringField('API ключ GetResponse', validators=[DataRequired()])
    user_domain = StringField('Домен GetResponse')
    metrika_key = StringField('Ключ Яндекс Метрики', validators=[DataRequired()])
    metrika_counter_id = StringField('ID счетчика Яндекс Метрики', validators=[DataRequired()])
    start_date = DateField('От', validators=[DataRequired()])
    auto_load = BooleanField('Автозагрузка')
    submit = SubmitField("Отправить")

    def validate_api_key(self, api_key):
        r = requests.get('https://api.getresponse.com/v3/accounts', \
                    headers={'X-Auth-Token': 'api-key {}'.format(api_key.data)})
        if r.status_code != 200 :
            raise ValidationError(('Нет контакта с GetResponse'))

class LinkGenerator(FlaskForm):
    link = StringField("Введите ссылку", validators=[DataRequired()])
    submit = SubmitField("Получить ссылку")
