from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from app.models import User

class EditIntegration(FlaskForm):
    integration_name = StringField("integration_name", validators=[DataRequired()])
    api_key = StringField('API')
    user_domain = StringField('Domain')
    metrika_key = StringField('metrika_key')
    metrika_counter_id = IntegerField('metrika_counter_id')
    clickhouse_login = StringField('clickhouse_login', validators=[DataRequired()])
    clickhouse_password = StringField('clickhouse_password', validators=[DataRequired()])
    clickhouse_host = StringField('clickhouse_host', validators=[DataRequired()])
    clickhouse_db = StringField('clickhouse_db', validators=[DataRequired()])
    submit = SubmitField("Submit")
