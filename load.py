from datetime import datetime, timedelta
import json

import requests

import private


def load_lecture(url, lecture):
    resp = requests.get(url, cookies={'sessionid': private.SESSION_ID})

    csrftoken = resp.cookies['csrftoken']

    cookies = {'sessionid': private.SESSION_ID, 'csrftoken': csrftoken}
    d, m, y = lecture['date'].split('.')
    date = '{}-{}-{}'.format(y, m, d)

    if lecture['time_end'] is None:
        hours, mins = lecture['time_start'].split(':')
        hours = int(hours)
        mins = int(mins)
        dt_start = datetime(year=2015, month=7, day=13,
                            hour=hours, minute=mins)
        dt_end = dt_start + timedelta(hours=1, minutes=30)
        time_end = dt_end.time().strftime('%H:%M')
    else:
        time_end = lecture['time_end']

    data = {'csrfmiddlewaretoken': csrftoken,
            'type': 'lecture',
            'venue': '1',
            'name': lecture['title'],
            'description': lecture['annotation'],
            'date': date,
            'starts_at': lecture['time_start'],
            'ends_at': time_end}

    if lecture['slide'] is not None:
        with file(lecture['slide'], 'rb') as f:
            files = {'slides': f}
            resp = requests.post(url, cookies=cookies, data=data,
                                 files=files,
                                 allow_redirects=False)
    else:
        resp = requests.post(url, cookies=cookies, data=data,
                             allow_redirects=False)

    if resp.status_code != 302:
        print resp.text
        assert False


def load_course(new_url, course):
    add_url = new_url + 'classes/add'
    for lecture in course['lectures']:
        print u'    loading lecture {}'.format(lecture['title'])
        load_lecture(add_url, lecture)


def load():
    url_old_to_new = {}
    with file('courses_to_move.json', 'rb') as f:
        for pair in json.loads(f.read()):
            url_old_to_new[pair['old']] = pair['new']

    with file('data.json', 'rb') as f:
        courses = json.loads(f.read())

        done = ({course['url'] for course in courses[:17]} |
                {course['url'] for course in courses[:64]})
        broken = {'http://old.compsciclub.ru/courses/selectedtopicscs'}

        for i, course in enumerate(courses):
            if course['url'] in done | broken:
                print "skipping {}".format(course['url'])
                continue
            new_url = url_old_to_new[course['url']]
            print ("loading course {} ({}/{})"
                   .format(course['url'], i+1, len(courses)))
            load_course(new_url, course)
