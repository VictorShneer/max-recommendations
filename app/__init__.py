# init.py
from urllib.parse import urlparse
from logging.handlers import RotatingFileHandler
import os
import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_admin import Admin
from app.admin_security import MyModefView, MyAdminIndexView
from rq import Queue
import rq
from redis import Redis


db = SQLAlchemy()
bootstrap = Bootstrap()
login = LoginManager()
migrate = Migrate()
login.login_view = 'auth.login'
login.login_message = "Please login to view that page."
admin=Admin()

def create_app(adminFlag=True,config_class=Config):
    print('Hey yo!')
    app = Flask(__name__)
    app.config.from_object(config_class)


    db.init_app(app)
    migrate.init_app(app,db)
    bootstrap.init_app(app)
    login.init_app(app)


    #ADMIN PANEL
    if (adminFlag):
        from app.models import User, Integration, Role, Task
        admin.init_app(app,index_view = MyAdminIndexView())
        admin.add_view(MyModefView(User, db.session))
        admin.add_view(MyModefView(Integration, db.session))
        admin.add_view(MyModefView(Role, db.session))
        admin.add_view(MyModefView(Task, db.session))

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('max-tasks', connection=app.redis)

    # app.task_queue = rq.Queue('max-tasks', connection=app.redis)
    # blueprint for auth routes in our app
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.metrika import bp as metrika_bp
    app.register_blueprint(metrika_bp)

    # blueprint
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)


    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # blueprint for newsletters routes in our app
    from app.newsletters import bp as newsletters_bp
    app.register_blueprint(newsletters_bp)

    #bp for analytics
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/max_metrika.log', maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Max metrika startup')

    if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
    else:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/max_metrika.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Max metrika startup')


    return app

from app import models
