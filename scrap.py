import os
import json

from bs4 import BeautifulSoup
import bs4.element
import requests


def find_slides(file_name):
    root_dir = '/Users/juliamaslova/Dropbox/CSClub/CSClubSlides/Slides/'
    found_slides = []
    for dir_name, _, file_list in os.walk(root_dir):
        if file_name in file_list:
            found_slides.append(dir_name + '/' + file_name)
    if len(found_slides) > 1:
        print "WARNING: more than one file found for", file_name
        return None
    elif len(found_slides) == 1:
        return found_slides[0]
    else:
        print "WARNING: no file with slides found for", file_name
        return None


def courses_content(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.text)

    course_title = soup.find(id="inner-content").find('h1').string

    lectures = []

    contents = soup.find_all('div', class_="view-course-lectures")
    assert len(contents) == 1
    content = contents[0]
    for td in content.find_all('td', class_='views-field views-field-body'):
        tags = td.contents

        title = td.find('a').string

        annotation = ''
        annotation_counter = 0
        for x in tags:
            if isinstance(x, bs4.element.Tag):
                if x.name == 'p':
                    if x.string is None:
                        print (u'WARNING: too complex annotation in p ({})'
                               .format(title))
                        break
                    annotation += x.string.strip()
                    annotation_counter += 1
                    print u'WARNING: annotation in p ({})'.format(title)
                    continue
                elif x.name == 'img':
                    print u'WARNING: picture in annotation ({})'.format(title)
                    continue
                else:
                    continue
            s = x.string
            if len(s.strip()) == 0:
                continue
            annotation += s.strip()
            annotation_counter += 1
        if annotation_counter > 1:
            print u"WARNING: more than one annotation piece ({})".format(title)

        date_display_td = td.find(class_='date-display-single')
        if date_display_td:
            date_substrings_raw = list(date_display_td.stripped_strings)
            date_substrings = []
            for s in date_substrings_raw:
                stripped = s.strip(' -')
                if len(stripped) > 0:
                    date_substrings.append(stripped)
            if len(date_substrings) == 2:
                date, time_start = date_substrings
                time_end = None
            elif len(date_substrings) == 3:
                date, time_start, time_end = date_substrings
            elif len(date_substrings) == 1:
                date, time_start = [s.strip()
                                    for s in date_substrings[0].split('-')]
                time_end = None
            else:
                assert False, ("unexpected substrings: {}"
                               .format(date_substrings))
        else:
            print "no date td found for {}".format(title.encode('utf-8'))
            date = None
            time_start = None
            time_end = None

        slides_list = []
        for tag_a in td.find_all('a'):
            if tag_a.string.endswith('.pdf'):
                maybe_slides = find_slides(tag_a.string)
                if maybe_slides:
                    slides_list.append(maybe_slides)
        if len(slides_list) > 1:
            print ("WARNING: more than one slide link for lecture {}"
                   .format(title.encode('utf-8')))

        slides = slides_list[0] if len(slides_list) == 1 else None

        lectures.append({'title': title.encode('utf-8'),
                         'annotation': annotation.encode('utf-8'),
                         'date': date.encode('utf-8') if date else None,
                         'time_start': (time_start.encode('utf-8')
                                        if time_start else None),
                         'time_end': (time_end.encode('utf-8')
                                      if time_end else None),
                         'slide': slides.encode('utf-8') if slides else None})

    return {'lectures': lectures,
            'url': url.encode('utf-8'),
            'title': course_title.encode('utf-8')}


def get_links():
    url_courses = 'http://old.compsciclub.ru/courses'
    prefix = 'http://old.compsciclub.ru'
    html = requests.get(url_courses)
    soup = BeautifulSoup(html.text)
    tag_td_list = soup.find_all('td', class_="views-field views-field-title")

    href_list = []
    for tag_td in tag_td_list:
        href_list.append(prefix + tag_td.contents[1].attrs['href'])

    return href_list


def get_data():
    urls = get_links()
    with file('courses_to_move.json') as f:
        courses_to_move = set([x['old'] for x in json.loads(f.read())])

    urls = [x for x in urls if x in courses_to_move]
    url_content = []
    for i, url in enumerate(urls):
        print "fetching", url, "({}/{})".format(i+1, len(urls))
        url_content.append(courses_content(url))
    with file('data.json', 'wb') as f:
        s = json.dumps(url_content,
                       indent=4, separators=(',', ': '),
                       ensure_ascii=False)
        f.write(s)
    return url_content
