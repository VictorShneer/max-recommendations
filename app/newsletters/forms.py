"""
this forms 
allow user to gel all GR newsletters and newsletters links 
"""
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class Available_newsletters(FlaskForm):
    available_newsletters = SelectField(\
        'Доступные письма и черновики')
    submit = SubmitField('Получить список ссылок в письме')

class Available_links(FlaskForm):
    available_links = SelectMultipleField('Доступные ссылки в выбранном письме', choices=[])
    submit = SubmitField('Обернуть выбранные ссылки и отправить в GetResponse')

class Api_key(FlaskForm):
    key = StringField('API ключ', validators=[DataRequired()])
    submit = SubmitField('Получить список доступных писем и черновиков')
