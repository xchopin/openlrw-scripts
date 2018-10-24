#!/usr/bin/python
# coding: utf-8

__author__ = "Xavier Chopin"
__copyright__ = "Copyright 2018, University of Lorraine"
__license__ = "ECL-2.0"
__version__ = "1.0.0"
__email__ = "xavier.chopin@univ-lorraine.fr"
__status__ = "Production"

import MySQLdb
import datetime
import sys
import os
import requests
import datetime

sys.path.append(os.path.dirname(__file__) + '/../../..')
from bootstrap.helpers import *

logging.basicConfig(filename=os.path.dirname(__file__) + '/import_results.log', level=logging.ERROR)

# -------------- GLOBAL --------------
DB_HOST = SETTINGS['db_moodle']['host']
DB_NAME = SETTINGS['db_moodle']['name']
DB_USERNAME = SETTINGS['db_moodle']['username']
DB_PASSWORD = SETTINGS['db_moodle']['password']

URI = SETTINGS['api']['uri'] + '/api/classes/'

MAIL = None

COUNTER = 0


# -------------- FUNCTIONS --------------
def post_result(jwt, class_id, data):
    response = requests.post(URI + str(class_id) + '/results?check=false', headers={'Authorization': 'Bearer ' + jwt},
                             json=data)
    print(Colors.OKBLUE + '[POST]' + Colors.ENDC + '/classes/' + str(class_id) + '/results - Response: ' + str(
        response.status_code))
    return response.status_code


def exit_log(result_id, reason):
    """
    Stops the script and email + logs the last event
    :param result_id:
    :param reason:
    """
    result_id = str(result_id)
    reason = str(reason)

    MAIL = smtplib.SMTP('localhost')
    email_message = "Subject: Error Moodle Results \n\n An error occured when sending the result " + result_id + \
                    "\n\n Details: \n" + reason
    db.close()
    MAIL.sendmail(SETTINGS['email']['from'], SETTINGS['email']['to'], email_message)
    logging.error("Subject: Error Moodle Results \n\n An error occured when sending the result " + result_id + \
                  "\n\n Details: \n" + reason)
    pretty_error("Error on POST", "Cannot send the result object " + result_id)  # It will also exit
    sys.exit(0)


# -------------- DATABASES --------------
db = MySQLdb.connect(DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME)
query = db.cursor()

# Query to get quizzes
query.execute("SELECT username, grades.id, grades.quiz, grades.grade, grades.timemodified, quiz.course"
              " FROM mdl_user as users, mdl_quiz_grades as grades, mdl_quiz as quiz"
              " WHERE grades.quiz = quiz.id AND users.id = grades.userid")

results = query.fetchall()

JWT = generate_jwt()

for result in results:
    student_id, result_id, lineitem_id, score, date, class_id = result

    if date > 0:
        date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%dT%H:%M:%S')
    else:
        date = ""

    json = {
        'sourcedId': result_id,
        'score': str(score),
        'date': date,
        'student': {
            'sourcedId': student_id
        },
        'lineitem': {
            'sourcedId': 'quiz_' + str(lineitem_id)
        },
        'metadata': {
            'category': 'Moodle',
            'type': 'quiz'
        }
    }

    try:
        response = post_result(JWT, class_id, json)
        if response == 401:
            JWT = generate_jwt()
            post_result(JWT, class_id, json)
        elif response == 500:
            exit_log(result_id, response)
    except requests.exceptions.ConnectionError as e:
        exit_log(result_id, e)

COUNTER = len(results)

# Query to get active quizzes
query.execute(
    "SELECT username, grades.id, activequiz.id, grades.finalgrade, grades.feedback, grades.timemodified, activequiz.course"
    " FROM mdl_user as users, mdl_activequiz as activequiz, mdl_grade_grades as grades, mdl_grade_items as items"
    " WHERE grades.itemid = items.id AND items.courseid = activequiz.course"
    " AND users.id = grades.userid AND grades.finalgrade is NOT NULL")

results = query.fetchall()

for result in results:
    student_id, result_id, lineitem_id, score, feedback, date, class_id = result

    if date > 0:
        date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%dT%H:%M:%S')
    else:
        date = ""

    if feedback == None:
        json = {
            'sourcedId': result_id,
            'score': str(score),
            'date': date,
            'student': {
                'sourcedId': student_id
            },
            'lineitem': {
                'sourcedId': 'active_quiz_' + str(lineitem_id)
            },
            'metadata': {
                'category': 'Moodle',
                'type': 'active_quiz'
            }
        }
    else:
        json = {
            'sourcedId': result_id,
            'score': str(score),
            'date': date,
            'student': {
                'sourcedId': student_id
            },
            'lineitem': {
                'sourcedId': 'active_quiz_' + str(lineitem_id)
            },
            'metadata': {
                'category': 'Moodle',
                'type': 'active_quiz',
                'feedback': feedback
            }
        }

    try:
        response = post_result(JWT, class_id, json)
        if response == 401:
            JWT = generate_jwt()
            post_result(JWT, class_id, json)
        elif response == 500:
            exit_log(result_id, response)
    except requests.exceptions.ConnectionError as e:
        exit_log(result_id, e)

COUNTER = COUNTER + len(results)
db.close()

pretty_message("Script finished",
               "Total number of results sent : " + str(COUNTER))

MAIL = smtplib.SMTP('localhost')

MAIL.sendmail(SETTINGS['email']['from'], SETTINGS['email']['to'],
            "Subject: Moodle Results script finished \n\n import_results.py finished its execution in " + measure_time() + "seconds "
            "\n\n -------------- \n SUMMARY \n -------------- \n Total number of results sent : " + str(COUNTER))
