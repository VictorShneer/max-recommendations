from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class Available_newsletters(FlaskForm):
    available_newsletters = SelectField(\
        'Доступные письма и черновики')
    submit = SubmitField('Получить список ссылок в письме')

class Available_links(FlaskForm):
    available_links = TextAreaField('Доступные ссылки в выбранном письме')
    submit = SubmitField('Обернуть ссылки в UTM')

class Api_key(FlaskForm):
    key = StringField('API ключ', validators=[DataRequired()])
    submit = SubmitField('Получить список доступных писем и черновиков')

class Converted_links(FlaskForm):
    converted_links = TextAreaField('Обернутые ссылки. Можно редактировать')
