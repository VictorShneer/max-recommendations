# models.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_security import UserMixin, RoleMixin
from app import db, login
import jwt
from time import time
from hashlib import md5
from flask import current_app
import json
import redis
import rq

roles_users = db.Table('roles_users', \
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),\
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))

class Task(db.Model):
    # look primary key is STRING not Integer            WTF!? :D
    # because this id is NOT SQLAlchemy id
    # but RQ job identificator
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100),index=True, unique=True)
    crypto = db.Column(db.String(100),index=True,unique=True)
    password_hash = db.Column(db.String(100))
    name = db.Column(db.String(1000), index=True)
    active = db.Column(db.Boolean())
    integrations = db.relationship('Integration', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary = roles_users, backref=db.backref('users', lazy='dynamic'))
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password_hash):
        return check_password_hash(self.password_hash, password_hash)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def launch_task(self, name, description, *args, **kwargs):

        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, *args)
        print('---job_id!!')
        print(rq_job.get_id())
        print(args)
        print('----')
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        print(task)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Integration(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    integration_name = db.Column(db.String(100))
    api_key = db.Column(db.String(100))
    user_domain = db.Column(db.String(100))
    metrika_key = db.Column(db.String(100))
    metrika_counter_id = db.Column(db.Integer)
    auto_load = db.Column(db.Boolean)
    start_date = db.Column(db.Date)

    def __repr__(self):
        return '<Integration {}>'.format(self.integration_name)

    def delete_myself(self):
        db.session.delete(self)
        db.session.commit()


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(256))
