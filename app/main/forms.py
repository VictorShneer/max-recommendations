from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from app.models import User

class EditIntegration(FlaskForm):
    integration_name = StringField("Название интеграции", validators=[DataRequired()])
    api_key = StringField('API ключ GetReponse')
    user_domain = StringField('Домен GetReponse')
    metrika_key = StringField('Ключ Яндекс Метрики')
    metrika_counter_id = IntegerField('ID счетчика Яндекс Метрики')
    clickhouse_login = StringField('Логин Базы Данных', validators=[DataRequired()])
    clickhouse_password = StringField('Пароль Базы Данных', validators=[DataRequired()])
    clickhouse_host = StringField('Хост Базы Данных', validators=[DataRequired()])
    clickhouse_db = StringField('Имя Базы Данных', validators=[DataRequired()])
    submit = SubmitField("Отправить")

class LinkGenerator(FlaskForm):
    link = StringField("Введите ссылку", validators=[DataRequired()])
    submit = SubmitField("Получить ссылку")
