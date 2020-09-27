from datetime import date, datetime
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
