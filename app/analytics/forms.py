from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DateField, SelectField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration

class AnalyticsBar(FlaskForm):
    DeviceCategory = SelectMultipleField('Тип устройства', choices=[(0, "Десктоп"), (1, "Мобильный телефон"), (2, 'Планшет'), (3, 'ТВ')], default = 'Не выбрано')
    OperatingSystem = SelectMultipleField('Операционная система', default = 'Не выбрано')
    RegionCity = SelectMultipleField('Город', default = 'Не выбрано')
    MobilePhone = SelectMultipleField('Марка мобильного устроства', default = 'Не выбрано')
    MobilePhoneModel = SelectMultipleField('Модель мобильного устроства', default = 'Не выбрано')
    Browser = SelectMultipleField('Браузер', default = 'Не выбрано')
    clause_visits = SelectField('После/До/Равно', choices=[(0,'Не выбрано'), (1,'После'), (2,'До'), (3,'Равно')], coerce=int, default =0)
    Date = DateField('Дата последнего визита', format='%d-%m-%Y')
    GoalsID = SelectMultipleField('ID Цели', default = 'Не выбрано')
    clause_visits_from_to = SelectField('После/До/Равно', choices=[(0,'Не выбрано'), (1,'После'), (2,'До'), (3,'Равно')], coerce=int, default=0)
    amount_of_visits = IntegerField('Количество визитов', default = '0')
    clause_goals = SelectField('После/До/Равно', choices=[(0,'Не выбрано'), (1,'После'), (2,'До'), (3,'Равно')],coerce=int, default=0)
    amount_of_goals = IntegerField('Количество выполненных целей', default = '0')
    URL = SelectMultipleField('URL', default = 'Не выбрано')

    submit = SubmitField("Отправить")
