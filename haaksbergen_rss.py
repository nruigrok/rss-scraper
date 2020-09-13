
import logging
import re
from collections import namedtuple
import cssselect
import locale
from amcatclient import AmcatAPI
from lxml import html
import requests
from datetime import datetime
from rsslib import create_connection
import csv
import sys
from requests import HTTPError





def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
        raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]


def get_links(conn):
    cur = conn.cursor()
    cur.execute("SELECT link FROM articles where medium ='at5'")
    rows = list(cur.fetchall())
    db_links = []
    for row in rows:
        id = row[0]
        db_links.append(id)
    return db_links


def get_meta(conn,url):
    cur = conn.cursor()
    cur.execute(f"SELECT title, medium, date FROM articles where link ='{url}'")
    title, medium, date = list(cur.fetchall())[0]
    return {"title": title,
            "publisher": medium,
            "date": date}

def scrape_article(session, url):
    try:
        page = requests.get(url)
    except HTTPError as err:
        if (err.response.status_code == 404) or (err.response.status_code == 403) or (err.response.status_code == 410):
            logging.error(f"Article not found (404, 403): {link}")
            return
        else:
            raise
    page = html.fromstring(page.text)
    article={}
    article['url']=url
    lead_ps = page.cssselect("div.container--detail.intro__text p")
    body_ps = page.cssselect("div.container--detail.detail-text p")
    content = "\n\n".join(p.text_content() for p in lead_ps + body_ps)
    article['text'] = content
    return article


session = requests.session()

db = "svdj2020.db"
conn = create_connection(db)
links = get_links(conn)
print(links)
from amcatclient import AmcatAPI
c = AmcatAPI("http://vu.amcat.nl")
for l in links:
    print(l)
    if '200508' in l:
        continue
    if 'redirect' in l:
        continue
    meta = get_meta(conn, l)
    if 'Liveblog' in meta['title']:
        continue
    a = scrape_article(session, l)
    if not a:
        continue
    if not a['text']:
        continue
    if a['text'] is None:
        continue
    else:
        a.update(meta)
        c.create_articles(29, 1442, [a])

