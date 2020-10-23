from app import create_app
from app.models import User, Integration, Notification, Role
from app import db
import click
from pprint import pprint
from app.clickhousehub.clickhouse import get_dbs
from app.clickhousehub.clickhouse_custom_request import create_ch_db
from app.clickhousehub.clickhouse_custom_request import give_user_grant
from app.clickhousehub.clickhouse_custom_request import request_iam
from app.utils import represents_int
app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Integration': Integration, 'Notification': Notification}


@app.cli.command()
@click.option('--id', help='User id')
def give_admin_role_to_id(id):
    #check if admin role exists
    if not represents_int(id):
        app.logger.info('hey dog! id shoulde be the INT')
        return -1
    user = User.query.filter_by(id=id).first()
    if not user:
        app.logger.info(f'WTF there is not a user with id: {id}')
        return -1
    admin_role = Role.query.filter_by(name='admin').first()
    app.logger.info(admin_role)
    if not admin_role:
        app.logger.info('Создаю админскую роль')
        # create admin role
        new_admin_role = Role(name='admin', description='Admin', users=[user])
        db.session.add(new_admin_role)
        db.session.commit()
        app.logger.info('Готово! Роль создана и присвоена')
    else:
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            app.logger.info(user.roles)
            db.session.commit()

        app.logger.info('Готово! Роль присвоена')




@app.cli.command()
def check_ch_auth():
    request_iam()

@app.cli.command()
def regular_load_to_clickhouse():
    """Clickhouse cron job."""
    users = User.query.filter_by(active=True).all()
    app.logger.info('### Users: {}'.format(str(users)))
    for user in users:
        user_integrations=Integration.query.filter_by(user_id=user.id).\
                                            filter_by(auto_load=True).all()
        app.logger.info("### Integrations: {}".format(str(user_integrations)))
        for integration in user_integrations:
            app.logger.info('### user: {} integration {}'.format(user, integration))
            mode = '-mode=regular_early'
            params = ['-source=hits', mode]
            params_2 = ['-source=visits', mode]
            user.launch_task('init_clickhouse_tables', \
                                ('Автоматическая загрузка метрик'), \
                                integration, \
                                {'user_id':user.id, 'user_crypto':user.crypto}, \
                                [params,params_2], \
                                True)
            db.session.commit()
    app.logger.info('### Done!')

@app.cli.command()
@click.option('--id', help='User id')
@click.option('--crypto', help='Crypto you want to set')
def init_user_in_clickhouse(id,crypto):
    """Clickhouse user initialization."""
    # check if arguments passed
    if not all([id,crypto]):
        app.logger.info('Hey dog! I need id and crypto to work')
        return -1
    # check if db already exists
    if crypto in get_dbs():
        app.logger.info('db already exists dog')
    # get user from db by id or except
    try:
        user = User.query.filter_by(id=id).one()
        app.logger.info('User {} found #id: {}'.format(user.email, user.id))
    except Exception as e:
        app.logger.info('No user was foung for {}'.format(id))
        return -1
    # check if user already got crypto
    if user.crypto != None:
        app.logger.info('This user already set up dog')
        return -1
    # assign crypto if it unique
    try:
        user.crypto = crypto
        db.session.commit()
        app.logger.info('{} assigned to {} with id: {}'.format(crypto, user.email, user.id))
    except Exception as e:
        app.logger.info('{} - this crypto already exists'.format(crypto))
        return -1
    # now let's create clickhouse db
    # and
    # give user grant access to crypto db
    try:
        # dont forget to update iam token
        iam_token = request_iam()
        if not iam_token:
            raise Exception('Failed to request iam')
        create_ch_db(crypto)
        give_user_grant('user1', crypto) ## # TODO: drop hardcode use config user name
    except Exception as err:
        user.crypto = None
        db.session.commit()
        app.logger.info(str(err) + '\nsmth went wrong dog :(( try again later..')

    app.logger.info('### Done!')
