from flask import render_template, flash, redirect, request, session
from werkzeug.utils import secure_filename
import os.path
import os
import json
import uuid
import time

from app import app

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

import cjrlib.cjr_queries
import cjrlib.cjr_db_connection

DB_FILE_DIR = os.path.join(app.instance_path, 'dbfile')

class UploadDBForm(FlaskForm):
    sqlite_file = FileField(validators=[FileRequired(), FileAllowed(['db', 'sqlite'], 'SQLite database files only!')])
    upload = SubmitField('Upload')


def get_db_connect_str():
    if 'db_file' not in session:
        flash('A database file has not be specified, please upload.')
        return None
    lcl_filename = session['db_file']
    ful_lcl_filepath = os.path.join(DB_FILE_DIR, lcl_filename)
    if not os.path.exists(ful_lcl_filepath):
        flash('Something has gone wrong no input database file was found.')
        return None
    cjr_db_file = 'sqlite:///' + ful_lcl_filepath
    return cjr_db_file


def rm_old_files(file_path, max_day_age=1):
    """
    Check and remove files which are over the max_age since last modification.
    :param file_path: the file path to check for old files.
    :param max_day_age: maximum age of file (base of modification) in days
    """
    now_t = time.time()
    for f in os.listdir(file_path):
        c_file = os.path.join(file_path, f)
        if os.path.isfile(c_file):
            if os.stat(c_file).st_mtime < (now_t - max_day_age * 86400):
                os.remove(c_file)


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
        # Create directory if not present
        if not os.path.exists(DB_FILE_DIR):
            os.makedirs(DB_FILE_DIR, exist_ok=True)
        # Remove files older then 1 day.
        rm_old_files(DB_FILE_DIR)
        # Create file name for file being uploaded
        ran_filename_str = str(uuid.uuid4()).replace("-", "")[0:10]
        file_basename, file_ext = os.path.splitext(filename)
        lcl_filename = "{}_{}{}".format(file_basename, ran_filename_str, file_ext)
        ful_lcl_filepath = os.path.join(DB_FILE_DIR, lcl_filename)
        # Perfrom upload/save to local space
        f.save(ful_lcl_filepath)
        # Check file has been correctly uploaded.
        if not os.path.exists(ful_lcl_filepath):
            flash('Something has gone wrong no input database file was found.')
            return redirect('/upload')
        #else if uploaded save to session cookie for reuse.
        session['db_file'] = lcl_filename
        return redirect('/joblist')
    return render_template('upload.html', title='Upload: Compute Job Recorder', form=form)


@app.route('/joblist')
def joblist():
    cjr_db_file = get_db_connect_str()
    if cjr_db_file is None:
        return redirect('/upload')

    try:
        job_names = cjrlib.cjr_queries.query_job_names(cjr_db_file=cjr_db_file)
    except Exception as e:
        flash('Something has gone wrong reading the database file to retrieve job names - try another file.')
        return redirect('/upload')

    jobs = []
    for job_name in job_names:
        versions = cjrlib.cjr_queries.get_job_versions(job_name, cjr_db_file=cjr_db_file)
        for version in versions:
            jobs.append({'jobname': job_name, 'version': version})

    return render_template('joblist.html', jobs=jobs)

@app.route('/tasklist', methods=['GET'])
def tasklist():
    job_name = request.args.get('jobname')
    version = request.args.get('version')
    status = request.args.get('status')

    cjr_db_file = get_db_connect_str()
    if cjr_db_file is None:
        return redirect('/upload')

    tasks = []
    if status == 'all':
        try:
            tasks = cjrlib.cjr_queries.get_all_tasks(job_name, version, cjr_db_file=cjr_db_file)
        except:
            flash('Something has gone wrong, the job/version combination is probably not valid')
    elif status == 'uncomplete':
        try:
            tasks = cjrlib.cjr_queries.get_uncompleted_tasks(job_name, version, cjr_db_file=cjr_db_file)
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

    cjr_db_file = get_db_connect_str()
    if cjr_db_file is None:
        return redirect('/upload')

    task = {}
    try:
        task = cjrlib.cjr_queries.get_task(job_name, task_id, version, cjr_db_file=cjr_db_file)
    except:
        flash('Something has gone wrong, the task/job/version combination is probably not valid')

    params_str = json.dumps(task['params'], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=True)
    task['params'] = params_str
    update_info_str = json.dumps(task['update_info'], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=True)
    task['update_info'] = update_info_str
    end_info_str = json.dumps(task['end_info'], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=True)
    task['end_info'] = end_info_str

    return render_template('taskinfo.html', task=task)

