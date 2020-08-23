from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DateField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration

class EditIntegration(FlaskForm):
    integration_name = StringField("Название интеграции", validators=[DataRequired()])
    api_key = StringField('API ключ GetResponse')
    user_domain = StringField('Домен GetResponse')
    metrika_key = StringField('Ключ Яндекс Метрики')
    metrika_counter_id = IntegerField('ID счетчика Яндекс Метрики')

    start_date = DateField('От', format='%d/%m/%Y', validators=[DataRequired()])
    end_date = DateField('До', format='%d/%m/%Y')

    submit = SubmitField("Отправить")



class LinkGenerator(FlaskForm):
    link = StringField("Введите ссылку", validators=[DataRequired()])
    submit = SubmitField("Получить ссылку")
