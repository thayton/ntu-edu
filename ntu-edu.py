#!/usr/bin/env python

######################################################################
# PURPOSE:
#
# Script to scrape data off of page
# https://wish.wis.ntu.edu.sg/webexe/owa/aus_subj_cont.main
#
# Retrieves all of the data in the iframe by by selecting every 
# option in the second dropdown menu 
#
# Results written to *.html files in same directory as script
#
# USAGE: 
#   $ ./ntu-edu.py
######################################################################
import sys, signal, logging
import mechanize, time
from bs4 import BeautifulSoup, Comment

URL = 'https://wish.wis.ntu.edu.sg/webexe/owa/aus_subj_cont.main'
DELAY = 5

def sigint(signal, frame):
    sys.stderr.write('Exiting...\n')
    sys.exit(0)    

def select_form(form):
    '''
    Select the course display form
    '''
    return form.attrs.get('target', None) == 'subjects'

class NtuEduScraper:
    def __init__(self):
        self.br = mechanize.Browser()
        self.url = 'https://wish.wis.ntu.edu.sg/webexe/owa/aus_subj_cont.main'
        self.delay = 5
        self.items = []

    def soupify(self, page):
        '''
        Run HTML page through BeautifulSoup and return the results, 
        minus script/style tags and comments
        '''
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

        return s

    def submit_form(self, item):
        '''
        Submit form using selection item.name and write the results
        to file named according to item.label
        '''
        maxtries = 3
        numtries = 0

        sys.stderr.write('Submitting form for item %s\n' % item.name)

        while numtries < maxtries:
            try:
                self.br.open(self.url)
                self.br.select_form(predicate=select_form)
                self.br.form['r_course_yr'] = [ item.name ]
                self.br.form.find_control('boption').readonly = False
                self.br.form['boption'] = 'CLoad'
                self.br.submit()
                break
            except (mechanize.HTTPError, mechanize.URLError) as e:
                if isinstance(e,mechanize.HTTPError):
                    print e.code
                else:
                    print e.reason.args

            numtries += 1
            time.sleep(numtries * self.delay)

        if numtries == maxtries:
            raise

        self.item_results_to_file(item, self.br.response().read())

    def item_results_to_file(self, item, results):
        label = ' '.join([label.text for label in item.get_labels()])
        label = '-'.join(label.split())

        sys.stderr.write('Writing results for item %s to file %s.html\n' % (item.name, label))

        with open("%s.html" % label, 'w') as f:
            f.write(results)
            f.close()
        
    def get_items(self):
        '''
        Get the list of items in the second dropdown of the form
        '''
        sys.stderr.write('Generating list of items for form selection\n')

        self.br.open(self.url)
        self.br.select_form(predicate=select_form)

        items = self.br.form.find_control('r_course_yr').get_items()

        sys.stderr.write('Got %d items for form selection\n' % len(items))

        return items

    def scrape(self):
        self.items = self.get_items()

        for item in self.items:
            # Skip invalid/blank item selections
            if len(item.name) < 1:
                continue

            self.submit_form(item)
            time.sleep(3)
        
if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint)
    scraper = NtuEduScraper()
    scraper.scrape()
