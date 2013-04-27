
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from sqlalchemy import *
from iatidq import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

## TEST RUNTIME-SPECIFIC DATA

class PackageStatus(db.Model):
    __tablename__ = 'packagestatus'
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey('package.id'))
    status = Column(Integer)
    runtime_datetime = Column(DateTime)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Runtime(db.Model):
    __tablename__ = 'runtime'
    id = Column(Integer, primary_key=True)
    runtime_datetime = Column(DateTime)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

## IATI REGISTRY PACKAGEGROUPS AND PACKAGES

class PackageGroup(db.Model):
    __tablename__ = 'packagegroup'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    name = Column(UnicodeText)
    ckan_id = Column(UnicodeText)
    revision_id = Column(UnicodeText)
    title = Column(UnicodeText)
    created_date = Column(UnicodeText)
    state = Column(UnicodeText)
    publisher_iati_id = Column(UnicodeText)
    publisher_segmentation = Column(UnicodeText)
    publisher_type = Column(UnicodeText)
    publisher_ui = Column(UnicodeText)
    publisher_organization_type = Column(UnicodeText)
    publisher_frequency = Column(UnicodeText)
    publisher_thresholds = Column(UnicodeText)
    publisher_units = Column(UnicodeText)
    publisher_contact = Column(UnicodeText)
    publisher_agencies = Column(UnicodeText)
    publisher_field_exclusions = Column(UnicodeText)
    publisher_description = Column(UnicodeText)
    publisher_record_exclusions = Column(UnicodeText)
    publisher_timeliness = Column(UnicodeText)
    license_id = Column(UnicodeText)
    publisher_country = Column(UnicodeText)
    publisher_refs = Column(UnicodeText)
    publisher_constraints = Column(UnicodeText)
    publisher_data_quality = Column(UnicodeText)

    def __init__(self, man_auto=None, name=None):
        if man_auto is not None:
            self.man_auto = man_auto
        if name is not None:
            self.name = name

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Package(db.Model):
    __tablename__ = 'package'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    source_url = Column(UnicodeText)
    package_ckan_id = Column(UnicodeText)
    package_name = Column(UnicodeText, nullable=False)
    package_title = Column(UnicodeText)
    package_license_id = Column(UnicodeText)
    package_license = Column(UnicodeText)
    package_metadata_created = Column(UnicodeText)
    package_metadata_modified = Column(UnicodeText)
    package_group = Column(Integer, ForeignKey('packagegroup.id'))
    package_activity_from = Column(UnicodeText)
    package_activity_to = Column(UnicodeText)
    package_activity_count = Column(UnicodeText)
    package_country = Column(UnicodeText)
    package_archive_file = Column(UnicodeText)   
    package_verified = Column(UnicodeText)  
    package_filetype = Column(UnicodeText)  
    package_revision_id = Column(UnicodeText)    
    active = Column(Boolean)
    __table_args__ = (UniqueConstraint('package_name'),)

    def __init__(self, man_auto=None, source_url=None):
        if man_auto is not None:
            self.man_auto = man_auto
        if source_url is not None:
            self.source_url = source_url

    def __repr__(self):
        source_url = self.source_url or "None"
        return source_url+u", "+str(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## RESULTS

class Result(db.Model):
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('runtime.id'), nullable=False)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    result_data = Column(Integer)
    result_identifier = Column(UnicodeText)
    result_hierarchy = Column(Integer)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

db.Index('result_runpack', 
         Result.runtime_id, Result.package_id, Result.result_identifier)
db.Index('result_test',
         Result.test_id)

class AggregateResult(db.Model):
    __tablename__='aggregateresult'
    id = Column(Integer,primary_key=True)
    runtime_id=Column(Integer, ForeignKey('runtime.id'), nullable=False)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    aggregateresulttype_id = Column(Integer, ForeignKey('aggregationtype.id'),
                                    nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    result_hierarchy = Column(Integer)
    results_data = Column(Float)
    results_num = Column(Integer)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# AggregationType allows for different aggregations
# Particularly used for looking only at current data
class AggregationType(db.Model):
    __tablename__ = 'aggregationtype'
    id = Column(Integer,primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    test_id = Column(Integer, ForeignKey('test.id'))
    test_result = Column(Integer)
    active = Column(Integer)

    def setup(self,
                 name,
                 description,
                 test_id,
                 test_result,
                 active,
                 id=None):
        self.name = name
        self.description = description
        self.test_id = test_id
        self.test_result = test_result
        self.active = active
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## TESTS

class Test(db.Model):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    test_group = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(Integer)
    test_level = Column(Integer)
    active = Column(Boolean)

    def setup(self,
                 name,
                 description,
                 test_group,
                 test_level,
                 active,
                 id=None):
        self.name = name
        self.description = description
        self.test_group = test_group
        self.test_level = test_level
        self.active = active
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## CODELISTS

class Codelist(db.Model):
    __tablename__ = 'codelist'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    source = Column(UnicodeText)

    def setup(self,
                 name,
                 description,
                 id=None):
        self.name = name
        self.description = description
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class CodelistCode(db.Model):
    __tablename__ = 'codelistcode'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    code = Column(UnicodeText)
    codelist_id = Column(Integer, ForeignKey('codelist.id'))
    source = Column(UnicodeText)

    def setup(self,
                 name,
                 code,
                 codelist_id,
                 id=None):
        self.name = name
        self.code = code
        self.codelist_id = codelist_id
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## INDICATORS

class IndicatorGroup(db.Model):
    __tablename__ = 'indicatorgroup'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

    def setup(self,
                 name,
                 description,
                 id=None):
        self.name = name
        self.description = description
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Indicator(db.Model):
    __tablename__ = 'indicator'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    indicatorgroup_id = Column(Integer, ForeignKey('indicatorgroup.id'))

    def setup(self,
                 name,
                 description,
                 indicatorgroup_id,
                 id=None):
        self.name = name
        self.description = description
        self.indicatorgroup_id = indicatorgroup_id
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class IndicatorTest(db.Model):
    __tablename__ = 'indicatortest'
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey('indicator.id'))
    test_id = Column(Integer, ForeignKey('test.id'))

    def setup(self,
                 indicator_id,
                 test_id,
                 id=None):
        self.indicator_id = indicator_id
        self.test_id = test_id
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationCondition(db.Model):
    __tablename__ = 'organisationcondition'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    test_id = Column(Integer, ForeignKey('test.id'))
    operation = Column(Integer) # show (1) or don't show (0) result
    condition = Column(UnicodeText) # activity level, hierarchy 2
    condition_value = Column(UnicodeText) # True, 2, etc.
    description = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(Integer)
    active = Column(Boolean)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationConditionFeedback(db.Model):
    __tablename__ ='organisationconditionfeedback'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(UnicodeText)
    uses = Column(UnicodeText)
    element = Column(UnicodeText)
    where = Column(UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## ORGANISATIONS; RELATIONS WITH PACKAGES

class Organisation(db.Model):
    __tablename__ = 'organisation'
    id = Column(Integer, primary_key=True)
    organisation_name = Column(UnicodeText, nullable=False)
    organisation_code = Column(UnicodeText, nullable=False)
    __table_args__ = (UniqueConstraint('organisation_name'),
                      UniqueConstraint('organisation_code'))
    # organisation_code is also used to communicate
    # with implementation schedules
    
    def setup(self,
                 organisation_name,
                 organisation_code,
                 id=None):
        self.organisation_name = organisation_name
        self.organisation_code = organisation_code
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationPackage(db.Model):
    __tablename__ = 'organisationpackage'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    package_id = Column(Integer, ForeignKey('package.id'))
    condition = Column(UnicodeText)
    __table_args__ = (UniqueConstraint('organisation_id', 'package_id', name='_organisation_package_uc'),
                     )
    def setup(self,
                 organisation_id,
                 package_id,
                 condition=None,
                 id=None):
        self.organisation_id = organisation_id
        self.package_id = package_id
        self.condition = condition
        if id is not None:
            self.id = id

class OrganisationPackageGroup(db.Model):
    __tablename__ = 'organisationpackagegroup'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    packagegroup_id = Column(Integer, ForeignKey('packagegroup.id'))
    condition = Column(UnicodeText)
    
    def setup(self,
                 organisation_id,
                 packagegroup_id,
                 condition=None,
                 id=None):
        self.organisation_id = organisation_id
        self.packagegroup_id = packagegroup_id
        self.condition = condition
        if id is not None:
            self.id = id

## INFORESULTS
# TODO: IMPLEMENT
# ==> total amount of disbursements in this package
# e.g. 1 = total disbursements

class InfoResult(db.Model):
    __tablename__ = 'info_result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('runtime.id'))
    package_id = Column(Integer, ForeignKey('package.id'))
    info_id = Column(Integer, ForeignKey('info_type.id'))
    result_data = Column(UnicodeText)
    
class InfoType(db.Model):
    __tablename__ = 'info_type'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

## USERS

class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(UnicodeText)
    first_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    email_address = Column(UnicodeText)
    reset_password_key = Column(UnicodeText)
    pw_hash = db.Column(String(255))

    def __init__(self, username, password, first_name, last_name, email_address):
        self.username = username
        self.pw_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def __repr__(self):
        return self.username, self.id, self.password2

class UserOption(db.Model):
    __tablename__ = 'useroption'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    option_id = Column(Integer, ForeignKey('option.id'))
    # basically two different values are permitted
    # given different names for clarity
    useroption_value = Column(UnicodeText)
    useroption_qualifier = Column(UnicodeText)

# Option: e.g. permission_view, survey_access
class Option(db.Model):
    __tablename__ = 'option'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    qualifier_required = Column(Integer)

## ORGANISATION SURVEYS

class OrganisationSurvey(db.Model):
    __tablename__ = 'organisationsurvey'
    id = Column(Integer,primary_key=True)
    currentworkflow_id = Column(Integer, ForeignKey('workflow.id'))
    currentworkflow_deadline = Column(DateTime)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    
    def setup(self,
                 organisation_id,
                 currentworkflow_id,
                 currentworkflow_deadline=None,
                 id=None):
        self.organisation_id = organisation_id
        self.currentworkflow_id = currentworkflow_id
        self.currentworkflow_deadline = currentworkflow_deadline
        if id is not None:
            self.id = id

class OrganisationSurveyData(db.Model):
    __tablename__ = 'organisationsurveydata'
    id = Column(Integer,primary_key=True)
    organisationsurvey_id = Column(Integer, ForeignKey('organisationsurvey.id'))
    indicator_id = Column(Integer, ForeignKey('indicator.id'))
    workflow_id = Column(Integer, ForeignKey('workflow.id'))
    published_status = Column(Integer, ForeignKey('publishedstatus.id'))
    published_source = Column(UnicodeText)
    published_comment = Column(UnicodeText)
    published_accepted = Column(Integer)
    
    def setup(self,
                 organisationsurvey_id,
                 indicator_id,
                 workflow_id=None,
                 published_status=None,
                 published_source=None,
                 published_comment=None,
                 published_accepted=None,
                 id=None):
        self.organisationsurvey_id = organisationsurvey_id
        self.workflow_id = workflow_id
        self.indicator_id = indicator_id
        self.published_status = published_status
        self.published_source = published_source
        self.published_comment = published_comment
        self.published_accepted = published_accepted

        if id is not None:
            self.id = id


class PublishedStatus(db.Model):
    __tablename__ = 'publishedstatus'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    publishedstatus_class = Column(UnicodeText)
    
    def setup(self,
                 name,
                 publishedstatus_class,
                 id=None):
        self.name = name
        self.publishedstatus_class = publishedstatus_class
        if id is not None:
            self.id = id
    
class Workflow(db.Model):
    __tablename__='workflow'
    id = Column(Integer,primary_key=True)
    name = Column(UnicodeText)
    leadsto = Column(Integer, ForeignKey('workflow.id'))
    workflow_type = Column(Integer, ForeignKey('workflowtype.id'))
    
    def setup(self,
                 name,
                 leadsto,
                 workflow_type=None,
                 id=None):
        self.name = name
        self.leadsto = leadsto
        self.workflow_type = workflow_type
        if id is not None:
            self.id = id

# WorkflowType: define what sort of workflow this should be.
#   Will initially be hardcoded but this should make it easier
#   to expand and define later.
class WorkflowType(db.Model):
    __tablename__='workflowtype'

    id = Column(Integer,primary_key=True)
    name = Column(UnicodeText)
    
    def setup(self,
                 name,
                 id=None):
        self.name = name
        if id is not None:
            self.id = id

class WorkflowNotification(db.Model):
    __tablename__='workflownotifications'
    id = Column(Integer, primary_key=True)
    workflow_from = Column(Integer, ForeignKey('workflow.id'))
    workflow_to = Column(Integer, ForeignKey('workflow.id'))
    workflow_notice = Column(UnicodeText)
