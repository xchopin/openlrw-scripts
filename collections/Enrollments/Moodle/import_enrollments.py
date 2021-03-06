#!/usr/bin/python
# coding: utf-8

__author__ = "Xavier Chopin"
__copyright__ = "Copyright 2019, University of Lorraine"
__license__ = "ECL-2.0"
__version__ = "1.0.4"
__email__ = "xavier.chopin@univ-lorraine.fr"
__status__ = "Production"

import MySQLdb
import datetime
import sys
import os
import requests
import datetime
import re
import json

sys.path.append(os.path.dirname(__file__) + '/../../..')
from bootstrap.helpers import *

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=os.path.dirname(__file__) + '/import_enrollments.log', level=logging.INFO)


parser = OpenLRW.parser
parser.add_argument('-f', '--from',  action='store', help='Timestamp (from) for querying Moodle`s database')
parser.add_argument('-u', '--update', action='store_true', help='Import newer enrollments than the last one stored in mongo')

args = vars(OpenLRW.enable_argparse())


# -------------- GLOBAL --------------
TIMESTAMP_REGEX = r'^(\d{10})?$'
DB_HOST = SETTINGS['db_moodle']['host']
DB_NAME = SETTINGS['db_moodle']['name']
DB_USERNAME = SETTINGS['db_moodle']['username']
DB_PASSWORD = SETTINGS['db_moodle']['password']


# -------------- FUNCTIONS --------------

def exit_log(enrollment_id, reason):
    """
    Stops the script and email + logs the last event
    :param enrollment_id:
    :param reason:
    """

    message = "An error occured when sending the object " + str(enrollment_id) + "\n\n Details: \n" + str(reason)
    db.close()
    OpenLrw.mail_server("Error Moodle Enrollments", message)
    logging.error(message)
    OpenLRW.pretty_error("HTTP POST Error", "Cannot send the enrollment object " + str(enrollment_id))
    sys.exit(0)


try:
    # ----- MAIN -------
    db = MySQLdb.connect(DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME)
    query = db.cursor()

    if (args['from'] is None) and (args['update'] is False):
        OpenLRW.pretty_error("Wrong usage", ["This script requires an argument, please run --help to get more details"])
        exit()

    if args['from'] is not None:
        if not re.match(TIMESTAMP_REGEX, args['from']):
            OpenLRW.pretty_error("Wrong usage", ["Argument must be a timestamp (from)"])
        else:
            sql_where = ">= " + args['from']

    elif args['update'] is True:
        jwt = OpenLrw.generate_jwt()
        last_enrollment = OpenLrw.http_auth_get('/api/enrollments?orderBy=begindate&page=0&limit=1', jwt)
        if last_enrollment is None:
            OpenLrw.pretty_error("ERROR : " + str(sys.argv[0]), "There is no enrollments")
            OpenLrw.mail_server("Subject: Error", "Either OpenLRW is turned off either, there is no enrollments")
            exit()
        last_enrollment = json.loads(last_enrollment)[0]
        date = datetime.datetime.strptime(last_enrollment['beginDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        query_timestamp = (date - datetime.datetime(1970, 1, 1)).total_seconds()
        sql_where = "> " + str(query_timestamp)


    query.execute("SELECT assignment.id, user.username, context.instanceid, assignment.userid, assignment.roleid, assignment.timemodified  "
                  "FROM mdl_role_assignments as assignment, mdl_context as context, mdl_user as user "
                  "WHERE context.id = assignment.contextid "
                  "AND user.id = assignment.userid AND (assignment.roleid = 3 OR assignment.roleid = 4 OR assignment.roleid = 5)"
                  "AND assignment.timemodified " + sql_where)

    enrollments = query.fetchall()

    JWT = OpenLrw.generate_jwt()

    OpenLRW.pretty_message('Info', 'Executing...')

    for enrollment in enrollments:
        enrollment_id, username, class_id, user_id, role, timestamp = enrollment
        json = {
            'sourcedId': enrollment_id,
            'role': 'student' if role == 5 else 'teacher',
            'user': {
                'sourcedId': username,
            },
            'beginDate': str(datetime.datetime.utcfromtimestamp(timestamp).isoformat()) + '.755Z',
            'primary': True,
            'status': 'active'
        }

        try:
            OpenLrw.post_enrollment(class_id, json, JWT, False)
        except ExpiredTokenException:
            JWT = OpenLrw.generate_jwt()
            OpenLrw.post_enrollment(class_id, json, JWT, False)
        except InternalServerErrorException:
            exit_log(enrollment_id, "Error 500")
        except requests.exceptions.ConnectionError as e:
            time.sleep(5)
            try:  # last try
                OpenLrw.post_enrollment(class_id, json, JWT, False)
            except requests.exceptions.ConnectionError as e:
                exit_log(enrollment_id, e)

    db.close()

    OpenLRW.pretty_message("Script finished", "Total number of enrollments sent : " + str(len(enrollments)))

    message = "import_enrollments.py finished its execution in " + measure_time() + " seconds " \
              "\n\n -------------- \n SUMMARY \n -------------- \n Total number of enrollments sent : "\
              + str(len(enrollments))

    # OpenLrw.mail_server(str(sys.argv[0]) + " executed", message)
    logging.info("Script finished | Total number of enrollments sent : " + str(len(enrollments)))
except Exception as e:
    print(repr(e))
    OpenLrw.mail_server(str(sys.argv[0]) + ' error', repr(e))
    logging.error(repr(e))
    exit()