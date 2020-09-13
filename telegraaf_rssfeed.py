
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



def polish(textstring):
    #This function polishes the full text of the articles - it separated the lead from the rest by ||| and separates paragraphs and subtitles by ||.
    lines = textstring.strip().split('\n')
    lead = lines[0].strip()
    rest = '||'.join( [l.strip() for l in lines[1:] if l.strip()] )
    if rest: result = lead + ' ||| ' + rest
    else: result = lead
    return result.strip()


def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
        raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]


def get_links(conn):
    cur = conn.cursor()
    cur.execute("SELECT link FROM articles where medium ='telegraaf.nl'")
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
    for label in tree.cssselect("span.label"):
        if label.text_content().strip().startswith("Liveblog"):
            return None
    lead_ps = tree.cssselect('p.ArticleIntroBlock__paragraph')
    body_ps = tree.xpath('//div[@data-element="articleBodyBlocks"]/p')
    text = "\n\n".join(p.text_content() for p in lead_ps + body_ps)
    return {"text": text}

COOKIES = {
    '__cfduid':'d56655838cd13e536c63a84867a1cd55c1585123110',
    'clientid':"ck871dfn22m9y568461ch66fv",
    'didomi_token':'eyJ1c2VyX2lkIjoiMTcxMTBiMzMtMTBjYS02YTViLWFkNDAtMmQwMGFjNGJlZTY2IiwiY3JlYXRlZCI6IjIwMjAtMDMtMjVUMDc6NTg6MzEuMjA4WiIsInVwZGF0ZWQiOiIyMDIwLTAzLTI1VDA3OjU4OjUwLjk0OFoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiZmFjZWJvb2siLCJjOm5sLXByb2ZpZWwiXSwiZGlzYWJsZWQiOltdfSwicHVycG9zZXMiOnsiZW5hYmxlZCI6WyJmdW5jdGlvbmVlbCIsInNvY2lhbF9tZWRpYSIsIm5sX3Byb2ZpZWwiLCJjb29raWVzIiwiYWR2ZXJ0aXNpbmdfcGVyc29uYWxpemF0aW9uIiwiY29udGVudF9wZXJzb25hbGl6YXRpb24iLCJhZF9kZWxpdmVyeSIsImFuYWx5dGljcyJdLCJkaXNhYmxlZCI6W119fQ==',
    'euconsent': 'BOwzpeIOwzphNAHABBNLC--AAAAuhr_7__7-_9_-_f__9uj3Or_v_f__32ccL59v_h_7v-_7fi_20nV4u_1vft9yfk1-5ctDztp507iakivXmqdeb9v_nz3_5pxP78k89r7337Ew_v8_v-b7BCON_YxEiA',
    'OB-USER-TOKEN': '82e48dea-c07a-420c-a5e2-cece4269fb48',
    'paywallversion': '1',
}

def create_cookie(domain, name, value):
    return {
        "name": name,
        "value": value,
        "domain": domain,
    }

session = requests.session()
for name, value in COOKIES.items():
    session.cookies.set(**create_cookie("www.telegraaf.nl", name, value))
r = session.get("https://www.telegraaf.nl/nieuws/1071777683/pvd-a-ers-houden-samengaan-met-groen-links-af")
r.raise_for_status()
#
# print("aantal nieuwe bevestigde besmettingen" in r.text)
# open("/tmp/test.html", "w").write(r.text)
# sys.exit()
#links = ["https://www.nu.nl/coronavirus/6039788/kinderen-thuis-in-coronatijd-zoek-de-lichtpuntjes-ga-geen-schooltje-spelen.html"]



db = "landelijkemedia.db"
conn = create_connection(db)
links = get_links(conn)
from amcatclient import AmcatAPI
c = AmcatAPI("http://vu.amcat.nl")
#links=['https://www.telegraaf.nl/nieuws/321571165/tientallen-bedolven-door-instorten-quarantainehotel-in-china']
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
        c.create_articles(2, 1385, [a])

