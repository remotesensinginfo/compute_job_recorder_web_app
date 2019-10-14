from flask import render_template, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
import os.path
import os
import shutil
import glob


from app import app

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import cjrlib.cjr_queries


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
        if os.path.exists(DB_FILE_DIR):
            shutil.rmtree(DB_FILE_DIR) 
        os.makedirs(DB_FILE_DIR, exist_ok=True)
        f.save(os.path.join(DB_FILE_DIR, filename))
        return redirect('/joblist')
    return render_template('upload.html', title='Upload: Compute Job Recorder', form=form)


@app.route('/joblist')
def joblist():
    dbfiles = glob.glob(os.path.join(DB_FILE_DIR, '*'))
    db_file = None
    if len(dbfiles) == 0:
        return redirect('/upload')
    elif len(dbfiles) == 1:
        db_file = dbfiles[0]
    else:
        flash('Something has gone wrong there seem to be multiple input database files.')
        return redirect('/upload')
    fileinfo = {'filename': os.path.basename(db_file)}
    os.environ['CJR_DB_FILE'] = 'sqlite:///' + db_file
    try:
        job_names = cjrlib.cjr_queries.query_job_names()
    except Exception as e:
        flash('Something has gone wrong reading the database file to retrieve job names - try another file.')
        return redirect('/upload')
    jobs = []
    for job_name in job_names:
        jobs.append({'jobname': job_name})

    return render_template('joblist.html', fileinfo=fileinfo, jobs=jobs)

@app.route('/tasklist', methods=['GET'])
def tasklist():
    job_name = request.args.get('jobname')
    print(job_name)
    status = request.args.get('status')
    print(status)
        
    return render_template('tasklist.html')

