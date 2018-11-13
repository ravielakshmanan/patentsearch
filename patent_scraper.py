from __future__ import print_function

import re
import json
import argparse

from math import ceil
from time import sleep
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup


#################################
#                               #
#    ~ U.S. patent scraper ~    #
#  New awards posted Tuesdays.  #
#                               #
#################################


class PatentAward(object):
    """A patent award."""

    def __init__(self, url, html):
        self.url = url
        self._html = html
        self._soup = BeautifulSoup(self._html, 'html.parser')

    @property
    def patent_number(self):
        return self._soup.find('title').text.split(':')[1].strip()

    @property
    def invention_description(self):
        description = self._soup.find('font', {'size': '+1'}).text.strip() \
                          .replace('\n', '')

        return ' '.join(description.split())

    @property
    def assignee(self):
        assignee = self._soup.find('th', text=re.compile('^Assignee')) \
                       .parent.td.text.strip().replace('\n', '')

        return ' '.join(assignee.split())

    @property
    def link_to_pdf(self):
        return self._soup.find('img', {'alt': '[Image]'}).parent['href']

    def get_inventor_details(self):
        inv_raw = self._soup.find('th', text=re.compile('^Inventor')) \
                      .parent.td.text

        inv_raw_ls = inv_raw.split(')')

        ls = []

        for name in inv_raw_ls:
            d = {}
            name_and_place = name.split(' (')

            if len(name_and_place) > 1:
                city_state = name_and_place[1].split(',')
                city = city_state[0].strip()
                state = city_state[1].strip()

                name_split = name_and_place[0].replace('\n', '') \
                                              .replace(', ', '') \
                                              .split(';')

                last = name_split[0].strip()
                rest = name_split[1].strip()

                d['last'] = last
                d['rest'] = rest
                d['city'] = city
                d['state'] = state

                ls.append(d)

        return ls

    @property
    def award_date(self):
        right_aligned_half_width_tds = self._soup.find_all('td', {
            'align': 'right',
            'width': '50%'
        })

        # this is kind of gross, i know
        date_tag = [x for x in right_aligned_half_width_tds if \
                    x.text.strip()[-4:].isnumeric() and \
                    int(x.text.strip()[-4:]) > 1900][0]

        return date_tag.text.strip()

    def __str__(self):
        return self.patent_number


def get_encoded_date(date_obj):
    """Return a encoded date string like what PTO expects."""

    try:
        return '%2F'.join([
            str(date_obj.month),
            str(date_obj.day),
            str(date_obj.year)
        ])
    except ValueError:
        return None


def build_list_url(page_num, start_date, city, state, end_date=date.today()):
    """Build URL for results list.

    Arguments:
        page_num:   results page number
        city:       inventor city
        state:      2-letter abbreviation for inventor state
        start_date: `date` object - first date to search
        end_date:   `date` object - last day to search,
                    defaults to today

    Returns:
        URL string
    """

    city = city.replace(' ', '+')

    url = ''.join([
        'http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2',
        '=HITOFF&p=',
        str(page_num),
        '&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&f=S&l=50&d=PTXT',
        '&Query=ic%2F%22',
        city,
        '%22+and+is%2F%22',
        state,
        '%22+and+isd%2F',
        get_encoded_date(start_date),
        '-%3E',
        get_encoded_date(end_date)
    ])

    return url


def extract_links(soup):
    """Extract links from results list page.

    Argument:
        soup: BeautifulSoup'd HTML of a result page

    Returns:
        A unique list of URLs to patent detail pages
    """

    prefix = 'http://patft.uspto.gov'
    table = soup.find('th', text='PAT. NO.').parent.parent
    links = [prefix + x['href'] for x in table.find_all('a')]

    return list(set(links))


def get_patent_list():
    """Fetch a list of links to patents awarded in the past week.

        CLI arguments:
            --city: inventor city, defaults to Austin
            --state: inventor state (postal abbr), defaults to TX
            --days: number of days back to search, defaults to 7

        Creates:
            ./links_to_recent_patents.txt
    """

    parser = argparse.ArgumentParser(
        description='Fetch patents recently awarded to inventors in a ' \
                    'given city.'
    )

    parser.add_argument('--city', metavar='', type=str, default='Austin',
                       help='the city for which you want data' \
                            ' (defaults to "Austin")')

    parser.add_argument('--state', metavar='', type=str, default='TX',
                        help='2-letter abbreviation of state for which you' \
                        'want data (defaults to "TX")')

    parser.add_argument('--days', metavar='', type=int, default=7,
                        help='how many days back to search (defaults to 7)')

    args = parser.parse_args()

    city = args.city.replace(' ', '+')
    state = args.state
    days_to_search = args.days

    days_ago = date.today() - timedelta(days=days_to_search)

    results_url = build_list_url(page_num=1, start_date=days_ago,
                                 city=city, state=state)

    r = requests.get(results_url)

    if r.status_code == 200:
        print('search connected')

        no_results = 'No patents have matched your query'

        some_results = 'Patent Database Search Results'

        # no results
        if no_results in r.text:
            print('~ no results found ~')

        else:

            ls = []

            # more than one result
            if some_results in r.text:

                # get total number of results
                regex_test = re.compile('<DOCS\: (\d+)>', re.IGNORECASE)
                results_count = regex_test.findall(r.text)[0]

                # calculate number of pages to loop over
                pages = ceil(int(results_count) / 50)

                print('~ found', results_count, 'results over',
                      pages, 'pages ~')

                # grab links from this page
                soup = BeautifulSoup(r.text, 'html.parser')
                ls += extract_links(soup)

                print('fetching links for page 1')

                # get data from multiple pages
                if pages > 1:
                    for page in range(2, pages+1):
                        sleep(2)

                        print('fetching links for page', page)

                        results_url = build_list_url(page_num=page,
                                                     start_date=days_ago,
                                                     city=city,
                                                     state=state)

                        r = requests.get(results_url)
                      
                        if r.status_code == 200:
                            soup = BeautifulSoup(r.text, 'html.parser')
                            ls += extract_links(soup)
                        else:
                            print('couldn\'t connect to page', page + ':',
                                  r.status_code)

            else:
                # if only one result, you're redirected to that detail page
                print('~ found one patent ~')

                ls.append(results_url)

            with open('links_to_recent_patents.txt', 'w') as out:
                for link in ls:
                    out.write(link + '\n')

            print('wrote file: links_to_recent_patents.txt')

    else:
        print('search didn\'t connect, yo:', r.status_code)


def get_patent_details():
    """Follow links to URLs and scrape data from detail pages.

    Creates:
        ./recent-patents.json
    """

    with open('links_to_recent_patents.txt', 'r') as infile:
        links = infile.readlines()

    ls = []

    for link in links:
        r = requests.get(link)
        d = {}

        patent = PatentAward(link, r.text)

        print(patent.invention_description)

        d['link_to_page'] = patent.url
        d['description'] = patent.invention_description
        d['assignee'] = patent.assignee
        d['award_date'] = patent.award_date
        d['link_to_pdf'] = patent.link_to_pdf
        d['inventors'] = patent.get_inventor_details()

        ls.append(d)
        sleep(2)

    with open('recent_patents.json', 'w') as inventions:
        inventions.write(json.dumps(ls))


if __name__ == '__main__':
    get_patent_list()
    get_patent_details()
