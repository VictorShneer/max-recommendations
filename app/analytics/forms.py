from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DateField, SelectField, RadioField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration

class AnalyticsBar(FlaskForm):
    device_category = SelectField('Тип устройства', choices=[(0, "Десктоп"), (1, "Мобильный телефон"), (2, 'Планшет'), (3, 'ТВ')], default = 'Не выбрано')
    operating_system = SelectField('Операционная система', default = 'Не выбрано')
    region_city = SelectField('Город', default = 'Не выбрано')
    url = SelectField('URL', default = 'Не выбрано')
    clause_visits = SelectField('От/До/Дата', choices=[(0,'От'), (1,'До'), (2,'Дата'), (3,'Не выбрано')], default =3)
    last_visit_date = DateField('Дата последнего визита', format='%d/%m/%Y')
    clause_visits_from_to = SelectField('От/До/Количество', choices=[(0,'От'), (1,'До'), (2,'Количество'), (3,'Не выбрано')], default=3)
    amount_of_visits = IntegerField('Количество визитов', default = '0')
    amount_of_goals = IntegerField('Количество выполненных целей', default = '0')
    clause_goals = SelectField('От/До/Количество', choices=[(0,'От'), (1,'До'), (2,'Количество'), (3,'Не выбрано')], default=3)
    goals_id = SelectField('ID Цели', default = 'Не выбрано')
    submit = SubmitField("Отправить")
