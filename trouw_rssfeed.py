
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



def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
        raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]


def get_links(conn):
    cur = conn.cursor()
    cur.execute("SELECT link FROM articles where medium ='trouw.nl'")
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
    page = session.get(url)
    if page.status_code == 404:
        return
    page.raise_for_status()
    open("/tmp/test7.html", "w").write(page.text)
    tree = html.fromstring(page.text)
    lead = tree.cssselect("p.artstyle__intro")
    if not lead:
        lead ="-"
    lead_ps = tree.cssselect('p.p.artstyle__text')
    body_ps = tree.cssselect('p.artstyle__text')
    text = "\n\n".join(p.text_content() for p in lead_ps + body_ps)
    text = re.sub("\n\n\s*", "\n\n", text)
    return {"text": text}


session = requests.session()
r = session.post("https://www.trouw.nl/privacy-wall/accept?redirectUri=%2f&pwv=2&pws=functional%7Canalytics%7Ccontent_recommendation%7Ctargeted_advertising%7Csocial_media&days=390&referrer=")
r.raise_for_status()


db = "landelijkemedia.db"
conn = create_connection(db)
links = get_links(conn)


from amcatclient import AmcatAPI
c = AmcatAPI("http://vu.amcat.nl")

for l in links:
    print(l)
    if 'video' in l:
        continue
    if 'redirect' in l:
        continue
    meta = get_meta(conn, l)
    if 'Liveblog' in meta['title']:
        continue
    a = scrape_article(session, l)
    if not a:
        continue
    else:
        a.update(meta)
        print(a)
       # c.create_articles(2, 1384, [a])