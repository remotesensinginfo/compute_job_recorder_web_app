#!/usr/bin/env python
"""
compute_job_recorder - Command to record the status of a compute job.
"""
# This file is part of 'compute_job_recorder'
# A library for recording compute job progress.
#
# Copyright 2019 Pete Bunting
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Purpose:  Command line tool for running the system.
#
# Author: Pete Bunting
# Email: pfb@aber.ac.uk
# Date: 28/07/2019
# Version: 1.0
#
# History:
# Version 1.0 - Created.

import cjrlib.cjr_queries
from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

@app.route('/')
def options_page():
    return "Hello World!"


@app.route('/jobnames')
def jobnames_page():
    job_names = cjrlib.cjr_queries.query_job_names()
    i = 0
    str_val = ""
    for job_name in job_names:
        str_val = str_val + "{}: {}\n".format(i, job_name)
        i = i + 1
    return str_val


@app.route('/tasks/alltasks', methods=['GET', 'POST'])
def alltasks_page():
    return_str = ""
    have_inputs = False
    if request.method == 'GET':
        try:
            jobname_str = request.args.get('jobname')
            version_str = request.args.get('version')
            have_inputs = True
        except Exception as e:
            return_str = str(e)
    elif request.method == 'POST':
        try:
            jobname_str = request.form['jobname']
            version_str = request.form['version']
            have_inputs = True
        except Exception as e:
            return_str = str(e)
    else:
        return_str = "To retrieve all tasks a jobname and version are required."

    if have_inputs:
        tasks_lst = cjrlib.cjr_queries.get_all_tasks(jobname_str, version_str)
        return jsonify(*tasks_lst)

    return return_str


@app.route('/tasks/incomplete', methods=['GET', 'POST'])
def incomplete_page():
    return_str = ""
    have_inputs = False
    if request.method == 'GET':
        try:
            jobname_str = request.args.get('jobname')
            version_str = request.args.get('version')
            have_inputs = True
        except Exception as e:
            return_str = str(e)
    elif request.method == 'POST':
        try:
            jobname_str = request.form['jobname']
            version_str = request.form['version']
            have_inputs = True
        except Exception as e:
            return_str = str(e)
    else:
        return_str = "To retrieve all uncompleted tasks a jobname and version are required."

    if have_inputs:
        tasks_lst = cjrlib.cjr_queries.get_uncompleted_tasks(jobname_str, version_str)
        return jsonify(*tasks_lst)

    return return_str


@app.route('/tasks/task', methods=['GET', 'POST'])
def task_page():
    return_str = ""
    have_inputs = False
    if request.method == 'GET':
        try:
            jobname_str = request.args.get('jobname')
            taskid_str = request.args.get('taskid')
            have_inputs = True
        except Exception as e:
            return_str = str(e)
    elif request.method == 'POST':
        try:
            jobname_str = request.form['jobname']
            taskid_str = request.form['taskid']
            have_inputs = True
        except Exception as e:
            return_str = str(e)
    else:
        return_str = "To retrieve a task a jobname and taskid are required."

    if have_inputs:
        tasks_lst = cjrlib.cjr_queries.get_tasks(jobname_str, taskid_str)
        return jsonify(*tasks_lst)

    return return_str

if __name__ == '__main__':
    app.run()

