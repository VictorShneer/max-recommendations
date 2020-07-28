from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration

class EditIntegration(FlaskForm):
    integration_name = StringField("Название интеграции", validators=[DataRequired()])
    api_key = StringField('API ключ GetResponse')
    user_domain = StringField('Домен GetResponse')
    metrika_key = StringField('Ключ Яндекс Метрики')
    metrika_counter_id = IntegerField('ID счетчика Яндекс Метрики')
    clickhouse_login = StringField('Логин Базы Данных', validators=[DataRequired()])
    clickhouse_password = StringField('Пароль Базы Данных', validators=[DataRequired()])
    clickhouse_host = StringField('Хост Базы Данных', validators=[DataRequired()])
    clickhouse_db = StringField('Имя Базы Данных', validators=[DataRequired()])
    submit = SubmitField("Отправить")

    # def validate_integration_name(self, integration_name):
    #     integration = Integration.query.filter_by(integration_name=self.integration_name.data).first()
    #     if integration is not None:
    #         raise ValidationError("Кажется, интеграция с таким именем уже существует")


class LinkGenerator(FlaskForm):
    link = StringField("Введите ссылку", validators=[DataRequired()])
    submit = SubmitField("Получить ссылку")
