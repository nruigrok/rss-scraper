import csv
import logging
import sqlite3
from collections import namedtuple

from requests import HTTPError

from online_scrapers import all_scrapers
import re


def get_links(conn):
    cur = conn.cursor()
    cur.execute("SELECT link FROM articles")
    rows = list(cur.fetchall())
    db_links = []
    for row in rows:
        id = row[0]
        db_links.append(id)
    return db_links


def get_text(link):
    for scraper in scrapers:
        if scraper.can_scrape(link):
            return scraper.scrape_text(link)

def scrape(link):
    text = get_text(link)
    if not text:
        logging.error(f"No scraper available for {link}")
    return text


def get_articles(f):
    with open(f, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        article = {}
        for row in csv_reader:
            article['url'] = row['url']
            m = re.search(r'\.\w+.\w+', article['url'], re.M)
            med = m.group()
            if "nos.nl" in article['url']:
                article['publisher']="nos.nl"
            else:
                article['publisher']=med.replace(".","",1)
            article['title'] = row['titel']
            article['date'] = row['datum']
            article['author'] = row['auteur']
            article['comments'] = row['discussielengte']
            article['type']= row['type']
            yield article


from amcatclient import AmcatAPI
c = AmcatAPI("https://bz.nieuwsmonitor.org")
scrapers = all_scrapers()

f = "bz_okt2020.csv"
articles = get_articles(f)
for art in articles:
    link = art['url']
    print(link)
    if 'video' in link:
        continue
    if 'redirect' in link:
        continue
    if art['type']=="comment":
        continue
    if 'Liveblog' in art['title']:
        continue
    try:
        art['text'] = scrape(link)
    except HTTPError as err:
        if err.response.status_code in (403,404,410):
            continue
        else:
            raise
    if not art['text']:
        continue
    c.create_articles(2, 128, [art])


