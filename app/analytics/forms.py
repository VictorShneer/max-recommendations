"""
Our analytics search based on flask form class
here we declare all fields that allow
user make searches over his site visitors
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, SelectField, SelectMultipleField, widgets
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Integration

class AnalyticsBar(FlaskForm):
    DeviceCategory = SelectMultipleField('Тип устройства', choices=[(1, "Десктоп"), (2, "Мобильный телефон"), (3, 'Планшет'), (4, 'ТВ')], default = 'Не выбрано')
    OperatingSystem = SelectMultipleField('Операционная система', default = 'Не выбрано')
    RegionCity = SelectMultipleField('Город', default = 'Не выбрано')
    MobilePhone = SelectMultipleField('Марка мобильного устроства', default = 'Не выбрано')
    MobilePhoneModel = SelectMultipleField('Модель мобильного устроства', default = 'Не выбрано')
    Browser = SelectMultipleField('Браузер', default = 'Не выбрано')
    clause_visits = SelectField('После/До/Равно', choices=[(-1,'Не выбрано'), (1,'После'), (2,'До'), (3,'Равно')], coerce=int)
    Date = DateField('Дата последнего визита', format='%Y-%m-%d')
    GoalsID = SelectMultipleField('Цели', default = 'Не выбрано')
    clause_visits_from_to = SelectField('Больше/Меньше/Равно', choices=[(-1,'Не выбрано'), (1,'Больше'), (2,'Меньше'), (3,'Равно')], coerce=int)
    amount_of_visits = IntegerField('Количество визитов')
    clause_goals = SelectField('Больше/Меньше/Равно', choices=[(-1,'Не выбрано'), (1,'Больше'), (2,'Меньше'), (3,'Равно')],coerce=int)
    amount_of_goals = IntegerField('Количество выполненных целей')
    clause_url = SelectField('Состоит/Равно', choices=[(-1,'Не выбрано'), (1,'Состоит'), (2,'Равно')],coerce=int)
    URL = SelectMultipleField('URL', default = 'Не выбрано')

    submit = SubmitField("Отправить")
 
class Filters(FlaskForm):
    Filters = SelectMultipleField('Добавить фильтр...', choices=[])