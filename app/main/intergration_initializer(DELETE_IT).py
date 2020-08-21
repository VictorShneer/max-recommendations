from flask import app

def create_integration_tables(crypto, id):
    params = ['-source=hits', '-mode=history']
    params = ['-source=visits', '-mode=history']
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))

    
# python metrica_logs_api.py -mode history -source hits

# python metrica_logs_api.py -mode history -source visits
