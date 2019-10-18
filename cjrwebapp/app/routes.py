from flask import render_template, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
import os.path
import os
import shutil
import glob
import json

from app import app

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import cjrlib.cjr_queries
import cjrlib.cjr_db_connection

DB_FILE_DIR = os.path.join(app.instance_path, 'dbfile')

class UploadDBForm(FlaskForm):
    sqlite_file = FileField(validators=[FileRequired(), FileAllowed(['db', 'sqlite'], 'SQLite database files only!')])
    upload = SubmitField('Upload')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Compute Job Recorder')


@app.route('/upload', methods=['GET', 'POST'])
def uploaddb():
    form = UploadDBForm()
    if form.validate_on_submit():
        f = form.sqlite_file.data
        filename = secure_filename(f.filename)
        flash('File to upload {}'.format(filename))
        cjrdb_conn = None
        if os.getenv('CJR_DB_FILE', None) is not None:
            cjrdb_conn = cjrlib.cjr_db_connection.CJRDBConnection()
            if cjrdb_conn is not None:
                cjrdb_conn.delete_obj()
        if os.path.exists(DB_FILE_DIR):
            shutil.rmtree(DB_FILE_DIR)
        os.makedirs(DB_FILE_DIR, exist_ok=True)
        f.save(os.path.join(DB_FILE_DIR, filename))

        # Find the database file which has been saved to the local file system.
        dbfiles = glob.glob(os.path.join(DB_FILE_DIR, '*'))
        db_file = None
        db_file_basename = ''
        if len(dbfiles) == 0:
            flash('Something has gone wrong no input database file was file.')
            return redirect('/upload')
        elif len(dbfiles) == 1:
            db_file = dbfiles[0]
            db_file_basename = os.path.basename(db_file)
        else:
            flash('Something has gone wrong there seem to be multiple input database files.')
            return redirect('/upload')

        os.environ['CJR_DB_FILE'] = 'sqlite:///' + db_file
        if cjrdb_conn is None:
            cjrdb_conn = cjrlib.cjr_db_connection.CJRDBConnection()
        else:
            cjrdb_conn.refresh_db()
        flash('Successfully uploaded "{}".'.format(db_file_basename))
        return redirect('/joblist')
    return render_template('upload.html', title='Upload: Compute Job Recorder', form=form)


@app.route('/joblist')
def joblist():
    try:
        job_names = cjrlib.cjr_queries.query_job_names()
    except Exception as e:
        flash('Something has gone wrong reading the database file to retrieve job names - try another file.')
        return redirect('/upload')

    jobs = []
    for job_name in job_names:
        versions = cjrlib.cjr_queries.get_job_versions(job_name)
        for version in versions:
            jobs.append({'jobname': job_name, 'version': version})

    return render_template('joblist.html', jobs=jobs)

@app.route('/tasklist', methods=['GET'])
def tasklist():
    job_name = request.args.get('jobname')
    version = request.args.get('version')
    status = request.args.get('status')

    tasks = []
    if status == 'all':
        try:
            tasks = cjrlib.cjr_queries.get_all_tasks(job_name, version)
        except:
            flash('Something has gone wrong, the job/version combination is probably not valid')
    elif status == 'uncomplete':
        try:
            tasks = cjrlib.cjr_queries.get_uncompleted_tasks(job_name, version)
        except:
            flash('Something has gone wrong, the job/version combination is probably not valid')
    else:
        flash('Something has gone wrong, status provided is not recognised')
        
    return render_template('tasklist.html', job={'jobname':job_name, 'version':version}, tasks=tasks)


@app.route('/taskinfo', methods=['GET'])
def taskinfo():
    job_name = request.args.get('jobname')
    version = request.args.get('version')
    task_id = request.args.get('taskid')

    task = {}
    try:
        task = cjrlib.cjr_queries.get_task(job_name, task_id, version)
    except:
        flash('Something has gone wrong, the task/job/version combination is probably not valid')

    params_str = json.dumps(task['params'], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=True)
    task['params'] = params_str
    update_info_str = json.dumps(task['update_info'], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=True)
    task['update_info'] = update_info_str
    end_info_str = json.dumps(task['end_info'], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=True)
    task['end_info'] = end_info_str

    return render_template('taskinfo.html', task=task)

