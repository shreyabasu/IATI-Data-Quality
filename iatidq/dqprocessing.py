
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, aggregations, dqpackages
import models
from sqlalchemy import func, distinct

def add_hardcoded_result(test_id, runtime_id, package_id, result_data):
    with db.session.begin():
        result = models.Result()
        result.test_id = test_id 
        result.runtime_id = runtime_id
        result.package_id = package_id
        result.result_data = int(bool(result_data))
        db.session.add(result)

def aggregate_results(runtime, package_id):
        # for each package, get results for this runtime
        # compute % pass for each hierarchy and test
        # write to db
    check_existing_results = db.session.query(models.AggregateResult
            ).filter(models.AggregateResult.runtime_id==runtime
            ).filter(models.AggregateResult.package_id==package_id
            ).first()

    if check_existing_results:
        status = "Already aggregated"
        aresults = "None"
        return {"status": status, "data": aresults}

    def get_organisation_ids():
        return [ o.Organisation.id for o in 
                 dqpackages.packageOrganisations(package_id) ]

    status = "Updating"

    agg_types = models.AggregationType.query.all()
    if len(agg_types) == 0:
        return {"status": status, "data": []}

    print "getting org ids"
    organisation_ids = get_organisation_ids()
    print organisation_ids
    aresults = []

    for agg_type in agg_types:
        if len(organisation_ids) > 0:
            data = aggregate_results_orgs(runtime, package_id, 
                                          organisation_ids, agg_type)
        else:
            data = aggregate_results_single_org(runtime, package_id, agg_type)
        aresults += data["data"]

    return {"status": status, "data": aresults}

def get_results(runtime, package_id, agg_type):
    print "results: lookup by aggtype"
    print agg_type
    print agg_type.test_id

    if agg_type.test_id is not None:
        results = db.session.query(distinct(models.Result.result_identifier)).filter(
            models.Result.test_id == agg_type.test_id
            ).filter(
            models.Result.result_data == '1'
            )
    else:
        results = db.session.query(distinct(models.Result.result_identifier))

    print "results: filter by runtime,packageid"

    results = results.filter(
        models.Result.runtime_id == runtime
        ).filter(
        models.Result.package_id == package_id
        ).all()

    print "doing distinct on result ids"

    result_identifiers = results # set([r.result_identifier for r in results])

    print "finished doing distinct"
    print len(result_identifiers)

    if result_identifiers:
        results = models.Result.query.filter(
            models.Result.runtime_id == runtime,
            models.Result.package_id == package_id,
            models.Result.result_identifier.in_(result_identifiers)
            ).all()
    else:
        print "short cut"
        results = []

    print "doing res2"

    results2 = models.Result.query.filter(
        models.Result.runtime_id == runtime,
        models.Result.package_id == package_id,
        models.Result.result_identifier == None
        ).all()

    results += results2
    return set([r.id for r in results])

def aggregate_results_single_org(runtime, package_id, agg_type):
    status = "Updating"
    print "getting result ids"
    result_ids = get_results(runtime, package_id, agg_type)
    print "getting data"
    data = db.session.query(models.Test.id,
                models.Result.result_data,
                models.Result.result_hierarchy,
                func.count(models.Result.id),
                models.Result.package_id
        ).filter(models.Result.runtime_id==runtime
        ).filter(models.Result.package_id==package_id
        ).filter(models.Result.id.in_(result_ids)
        ).join(models.Result
        ).group_by(models.Result.package_id, 
                   models.Result.result_hierarchy, 
                   models.Test.id, 
                   models.Result.result_data
        ).all()

    print "got data, len:"
    print len(data)

    print "calc percentages"
    aresults = aggregations.aggregate_percentages(data)
    print "finished calculating percentages"

    with db.session.begin():
        for aresult in aresults:
            a = models.AggregateResult()
            a.runtime_id = runtime
            a.package_id = aresult["package_id"]
            a.test_id = aresult["test_id"]
            a.result_hierarchy = aresult["hierarchy"]
            a.results_data = aresult["percentage_passed"]
            a.results_num = aresult["total_results"]
            a.aggregateresulttype_id = agg_type.id
            db.session.add(a)
    
    return {"status": status, "data": aresults}

def aggregate_results_orgs(runtime, package_id, organisation_ids, agg_type):
    status = "Updating"
    result_ids = get_results(runtime, package_id, agg_type)

    print "len(result_ids): %d" % len(result_ids)

    # create temp table
    conn = db.session.connection()
    conn.execute('begin transaction;')
    conn.execute('''create temporary table relevant_result 
                                           (result_id int not null primary key);''')

    for result_id in result_ids:
        conn.execute('''insert into relevant_result values (%d);''' % result_id)

    sql = '''
        SELECT test.id AS test_id,
            result.result_data AS result_result_data,
            result.result_hierarchy AS result_result_hierarchy,
            count(result.id) AS count_1,
            result.package_id AS result_package_id,
            result.organisation_id AS result_organisation_id 
        FROM test JOIN result ON test.id = result.test_id 
        WHERE result.runtime_id = %d AND result.package_id = %d AND 
              result.id IN 
                  (select result_id from relevant_result) GROUP BY result.package_id,
            result.result_hierarchy,
            result.organisation_id,
            test.id,
            result.result_data'''

    stmt = sql % (runtime, package_id)
    data = [row for row in conn.execute(stmt)]
    conn.execute('''drop table relevant_result;''')
    conn.execute('rollback;')
    del(conn)

    aresults = aggregations.aggregate_percentages_org(data)

    with db.session.begin():
        for aresult in aresults:
            a = models.AggregateResult()
            a.runtime_id = runtime
            a.package_id = aresult["package_id"]
            a.test_id = aresult["test_id"]
            a.result_hierarchy = aresult["hierarchy"]
            a.results_data = aresult["percentage_passed"]
            a.results_num = aresult["total_results"]
            a.organisation_id = aresult["organisation_id"]
            a.aggregateresulttype_id = agg_type.id
            db.session.add(a)

    print "added to db"
    
    return {"status": status, "data": aresults}
