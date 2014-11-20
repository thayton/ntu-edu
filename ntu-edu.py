#!/usr/bin/env python

import sys, logging
import mechanize, time
from bs4 import BeautifulSoup, Comment

URL = 'https://wish.wis.ntu.edu.sg/webexe/owa/aus_subj_cont.main'
DELAY = 5

def soupify(page):
    s = BeautifulSoup(page)

    # Remove unwanted tags
    tags = s.findAll(lambda tag: tag.name == 'script' or \
                                 tag.name == 'style')
    for t in tags:
        t.extract()
        
    # Remove comments
    comments = s.findAll(text=lambda text:isinstance(text, Comment))
    for c in comments:
        c.extract()

    # Remove entity references?
    return s

def select_form(form):
    return form.attrs.get('target', None) == 'subjects'

def submit_form(item):
    maxtries = 3
    numtries = 0

    br = mechanize.Browser()

    while numtries < maxtries:
        try:
            br.open(URL)
            br.select_form(predicate=select_form)
            br.form['r_course_yr'] = [ item.name ]
            br.form.find_control('boption').readonly = False
            br.form['boption'] = 'CLoad'
            br.submit()
            break
        except (mechanize.HTTPError, mechanize.URLError) as e:
            if isinstance(e,mechanize.HTTPError):
                print e.code
            else:
                print e.reason.args

            numtries += 1
            time.sleep(numtries * DELAY)

    if numtries == maxtries:
        raise

    s = BeautifulSoup(br.response().read())

    label = ' '.join([label.text for label in item.get_labels()])
    label = '-'.join(label.split())

    with open("%s.html" % label, 'w') as f:
        f.write(s.prettify())
        f.close()
    
if __name__ == '__main__':
    br = mechanize.Browser()
    br.open(URL)
    br.select_form(predicate=select_form)

    items = br.form.find_control('r_course_yr').get_items()

    for item in items:
        if len(item.name) < 1:
            continue

        submit_form(item)
        time.sleep(3)
