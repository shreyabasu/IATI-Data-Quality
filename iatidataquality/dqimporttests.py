from db import *
import models
import csv
import urllib2

def hardcodedTests():
    hardcoded_tests = [
        (-2, 'url_exists', "Check that the xml file actually exists."),
        (-3, 'valid_xml', "Check that xml is well structured"),
        (-4, 'schema_conformance', "Check that xml conforms to schema")
    ]
    for hardcoded_test in hardcoded_tests:
        if models.Test.query.filter(models.Test.id==hardcoded_test[0]).first():
            continue
        test = models.Test()
        test.id = hardcoded_test[0]
        test.name = hardcoded_test[1]
        test.description =  hardcoded_test[2]
        test.test_level = 2 # File
        test.active = True
        db.session.add(test)
        db.session.commit()

def importTests(filename='tests/activity_tests.csv', level=1, local=True):
    #models.Test.query.filter(models.Test.test_level==1).update({models.Test.active: False})

    if (local==True):
        f = open(filename, 'r')
    else:
        try:
            f = urllib2.urlopen(filename, timeout=60)
        except:
            return False
    
    
    data = csv.DictReader(f)

    for row in data:
        test = models.Test.query.filter(models.Test.name==row['test']).first()

        if not test:
            test = models.Test()
        test.name = row['test']
        test.description = row['description']
        test.test_group = row['group']
        test.file = filename
        test.line = data.line_num
        test.test_level = level
        test.active = True
        db.session.add(test)
    db.session.commit()
    print "Imported successfully"
    return True

if __name__ == "__main__":
    hardcodedTests()
    importTests('../tests/activity_tests.csv')
