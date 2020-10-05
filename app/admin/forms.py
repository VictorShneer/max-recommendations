from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from app.models import User



class AssignCryptoForm(FlaskForm):

    user_id = IntegerField('Id Пользователя', validators=[DataRequired()])
    crypto = StringField('Crypto', validators=[DataRequired()])
    submit = SubmitField('Go!')

    def validate_user_id(self, user_id):
        user = User.query.filter_by(id=user_id.data).first()
        if not user:
            raise ValidationError('С таким ID нет пользователя')