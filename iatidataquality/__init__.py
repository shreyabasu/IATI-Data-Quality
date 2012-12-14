from flask import Flask, render_template, flash, request, Markup, session, redirect, url_for, escape, Response, abort
from flask.ext.celery import Celery
from flask.ext.sqlalchemy import SQLAlchemy
#from celery.task.sets import TaskSet # Need to improve later

from sqlalchemy import func
from datetime import datetime

from db import *

import models
import api
import dqfunctions
import dqprocessing
import dqruntests

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/tests/")
@app.route("/tests/<id>/")
def tests(id=None):
    if (id is not None):
        test = models.Test.query.filter_by(id=id).first_or_404()
        return render_template("test.html", test=test)
    else:
        tests = models.Test.query.order_by(models.Test.id).all()
        return render_template("tests.html", tests=tests)

@app.route("/tests/<id>/edit/", methods=['GET', 'POST'])
def tests_editor(id=None):
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            test = models.Test.query.filter_by(id=id).first_or_404()
            test.name = request.form['name']
            test.description = request.form['description']
            test.test_level = request.form['test_level']
            test.active = request.form['active']
            test.test_group = request.form['test_group']
            db.session.add(test)
            db.session.commit()
            flash('Updated', "success")
            return render_template("test_editor.html", test=test)
        else:
            flash('Incorrect password', "error")
            test = models.Test.query.filter_by(id=id).first_or_404()
            return render_template("test_editor.html", test=test)
    else:
        test = models.Test.query.filter_by(id=id).first_or_404()
        return render_template("test_editor.html", test=test)

@app.route("/publisher_conditions/")
@app.route("/publisher_conditions/<id>/")
def publisher_conditions(id=None):
    if (id is not None):
        pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
        return render_template("publisher_condition.html", pc=pc)
    else:
        pcs = models.PublisherCondition.query.order_by(models.PublisherCondition.id).all()
        return render_template("publisher_conditions.html", pcs=pcs)

@app.route("/publisher_conditions/<id>/edit/", methods=['GET', 'POST'])
def publisher_conditions_editor(id=None):
    publishers = models.PackageGroup.query.order_by(models.PackageGroup.id).all()
    tests = models.Test.query.order_by(models.Test.id).all()
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
            pc.description = request.form['description']
            pc.publisher_id = int(request.form['publisher_id'])
            pc.test_id = int(request.form['test_id'])
            pc.operation = int(request.form['operation'])
            pc.condition = request.form['condition']
            pc.condition_value = request.form['condition_value']
            pc.file = request.form['file']
            pc.line = int(request.form['line'])
            pc.active = int(request.form['active'])
            db.session.add(pc)
            db.session.commit()
            flash('Updated', "success")
            return redirect(url_for('publisher_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
            pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
            return render_template("publisher_condition_editor.html", pc=pc, publishers=publishers, tests=tests)
    else:
        pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
        return render_template("publisher_condition_editor.html", pc=pc, publishers=publishers, tests=tests)

@app.route("/publisher_conditions/new/", methods=['GET', 'POST'])
def publisher_conditions_new(id=None):
    publishers = models.PackageGroup.query.order_by(models.PackageGroup.id).all()
    tests = models.Test.query.order_by(models.Test.id).all()
    if (request.method == 'POST'):
        pc = models.PublisherCondition()
        pc.description = request.form['description']
        pc.publisher_id = int(request.form['publisher_id'])
        pc.test_id = int(request.form['test_id'])
        pc.operation = int(request.form['operation'])
        pc.condition = request.form['condition']
        pc.condition_value = request.form['condition_value']
        pc.file = request.form['file']
        pc.line = int(request.form['line'])
        pc.active = int(request.form['active'])
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            db.session.add(pc)
            db.session.commit()
            flash('Created new condition', "success")
            return redirect(url_for('publisher_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
            return render_template("publisher_condition_editor.html", pc=pc, publishers=publishers, tests=tests)
    else:
        return render_template("publisher_condition_editor.html", pc={}, publishers=publishers, tests=tests)

@app.route("/publishers/")
def publishers():
    p_groups = models.PackageGroup.query.order_by(models.PackageGroup.name).all()

    pkgs = models.Package.query.order_by(models.Package.package_name).all()
    return render_template("publishers.html", p_groups=p_groups, pkgs=pkgs)

@app.route("/publishers/<id>/")
def publisher(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    latest_runtime = db.session.query(models.Runtime
        ).filter(models.PackageGroup.id==p_group.id
        ).join(models.Result,
               models.Package,
               models.PackageGroup,
        ).order_by(models.Runtime.id.desc()
        ).first()

    aggregate_results = db.session.query(models.Test,
                                         models.AggregateResult.results_data,
                                         models.AggregateResult.results_num,
                                         models.AggregateResult.result_hierarchy,
                                         models.AggregateResult.package_id
            ).filter(models.Package.package_group==p_group.id,
                     models.AggregateResult.runtime_id==latest_runtime.id
            ).group_by(models.AggregateResult.result_hierarchy, models.Test.id, models.AggregateResult.package_id
            ).join(models.AggregateResult,
                   models.Package
            ).all()

    pconditions = models.PublisherCondition.query.filter_by(publisher_id=p_group.id).all()

    aggregate_results = dqfunctions.agr_results(aggregate_results, conditions=pconditions, mode="publisher")

    return render_template("publisher.html", p_group=p_group, pkgs=pkgs, results=aggregate_results, runtime=latest_runtime)

@app.route("/packages/")
@app.route("/packages/<id>/")
@app.route("/packages/<id>/runtimes/<runtime_id>/")
def packages(id=None, runtime_id=None):
    if (id is None):
        pkgs = models.Package.query.order_by(models.Package.package_name).all()
        return render_template("packages.html", pkgs=pkgs)

    # Get package data
    p = db.session.query(models.Package,
        models.PackageGroup
		).filter(models.Package.package_name == id
        ).join(models.PackageGroup).first()

    if (p is None):
        p = db.session.query(models.Package
		).filter(models.Package.package_name == id
        ).first()
        pconditions = {}
    else:
        # Get publisher-specific conditions.

        pconditions = models.PublisherCondition.query.filter_by(publisher_id=p[1].id).all()

    # Get list of runtimes
    try:
        runtimes = db.session.query(models.Result.runtime_id,
                                    models.Runtime.runtime_datetime
            ).filter(models.Result.package_id==p[0].id
            ).distinct(
            ).join(models.Runtime
            ).all()
    except Exception:
        return abort(404)

    if (runtime_id):
        # If a runtime is specified in the request, get the data

        latest_runtime = db.session.query(models.Runtime
            ).filter(models.Runtime.id==runtime_id
            ).first()
        latest = False
    else:
        # Select the highest runtime; then get data for that one

        latest_runtime = db.session.query(models.Runtime
            ).filter(models.Result.package_id==p[0].id
            ).join(models.Result
            ).order_by(models.Runtime.id.desc()
            ).first()
        latest = True

    aggregate_results = db.session.query(models.Test,
                                         models.AggregateResult.results_data,
                                         models.AggregateResult.results_num,
                                         models.AggregateResult.result_hierarchy
            ).filter(models.AggregateResult.package_id==p[0].id,
                     models.AggregateResult.runtime_id==latest_runtime.id
            ).group_by(models.AggregateResult.result_hierarchy, models.Test
            ).join(models.AggregateResult
            ).all()

    aggregate_results = dqfunctions.agr_results(aggregate_results, pconditions)
 
    return render_template("package.html", p=p, runtimes=runtimes, results=aggregate_results, latest_runtime=latest_runtime, latest=latest, pconditions=pconditions)

@app.route("/runtests/new/")
def run_new_tests():
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()
    res = dqruntests.load_package.delay(newrun.id)
    
    flash('Running tests; this may take some time. Runtime ID is ' + str(newrun.id), "success")
    return render_template("runtests.html", task=res,runtime=newrun)

@app.route("/runtests/")
@app.route("/runtests/<id>/")
def check_tests(id=None):
    if (id):
        task = dqruntests.load_package.AsyncResult(id)
        return render_template("checktest.html", task=task)
    else: 
        i = celery.control.inspect()
        active_tasks = i.active()
        registered_tasks = i.reserved()
        return render_template("checktests.html", active_tasks=active_tasks, registered_tasks=registered_tasks)

@app.route("/tests/import/", methods=['GET', 'POST'])
def import_tests():
    if (request.method == 'POST'):
        import dqimporttests
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            if (request.form.get('local')):
                result = dqimporttests.importTests()
            else:
                url = request.form['url']
                level = int(request.form['level'])
                result = dqimporttests.importTests(url, level, False)
            if (result==True):
                flash('Imported tests', "success")
            else:
                flash('There was an error importing your tests', "error")
        else:
            flash('Wrong password', "error")
        return render_template("import_tests.html")
    else:
        return render_template("import_tests.html")

@app.route("/publisher_conditions/import/", methods=['GET', 'POST'])
def import_publisher_conditions():
    if (request.method == 'POST'):
        import dqimportpublisherconditions
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            """if (request.form.get('local')):"""
            results = dqimportpublisherconditions.importPCs()
            """else:
                url = request.form['url']
                level = int(request.form['level'])
                result = dqimporttests.importTests(url, level, False)
            """
            if (results):
                flash('Parsed tests', "success")
            else:
                results = None
                flash('There was an error importing your tests', "error")
        else:
            flash('Wrong password', "error")
            results = None
        return render_template("import_publisher_conditions.html", results=results)
    else:
        return render_template("import_publisher_conditions.html")

@app.route("/publisher_conditions/export/")
def export_publisher_conditions():
    conditions = db.session.query(models.PublisherCondition.description).all()
    conditionstext = ""
    for i, condition in enumerate(conditions):
        if (i != 0):
            conditionstext = conditionstext + "\n"
        conditionstext = conditionstext + condition.description
    rv = app.make_response(conditionstext)
    rv.mimetype = 'text'
    return rv

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
