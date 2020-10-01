from datetime import date, datetime
from flask import url_for, redirect, flash
from app.models import Task
def check_if_date_legal(user_date):
    today = str(date.today())
    try:
        datetime.strptime(user_date, '%Y-%m-%d')
    except Exception as err:
        print(user_date)
        return False

    if today < user_date:
        print(today < user_date)
        return False
    return True


def integration_is_ready(function):
    def wrapper(integration_id):
        task = Task.query.filter_by(description=f'Init integration id:{integration_id}').first()
        try:
            if not task.complete:
                flash('Подождите завершения создания интеграции')
                return redirect(url_for('main.user_integrations'))
        except AttributeError:
            print('Task losted')
        finally:
            return function(integration_id)
    # Renaming the function name:
    wrapper.__name__ = function.__name__
    return wrapper
