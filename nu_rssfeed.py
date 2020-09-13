
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
    cur.execute("SELECT link FROM articles where medium ='nu.nl'")
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
    text = tree.cssselect('div.block-wrapper div.block-content > p')
    if not text:
        text = tree.cssselect('div.caption-wrapper')
        if not text:
            text = tree.cssselect('div.block-content')
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    return {"text": text}

COOKIES = {
    'euconsent': "BOwwpfuOwwpfuAxAABNLCx-AAAAs57_______9______9uz_Ov_v_f__33e8__9v_l_7_-___u_-33d4u_1vf99yfm1-7etr3tp_87ues2_Xur__79__3z3_9pxP78k89r7337Ew_v-_v8b7JCKN4A",
    'gig_bootstrap_3_pNK9L9zU_Sx2BKzTUJuAmy1im2zN0pOkwM-Ui3AgrneVzSpyQqioWy_iZ1cbQzS5' : '_gigya_ver3',
    'OPTOUTMULTI': '0:1|c5:0|c4:0|c3:0|c2:0|c1:0',
    'sanomaconsent_agreement': '105',
    'sanomaconsent_consent': 'true',
    'SanomaWeb': 'u4mynice5e',
    'SanomaWebSession': '5pzu8mrt36',
}

def create_cookie(domain, name, value):
    return {
        "name": name,
        "value": value,
        "domain": domain,
    }

session = requests.session()
##for name, value in COOKIES.items():
#    session.cookies.set(**create_cookie("www.nu.nl", name, value))

# r = session.get("https://www.nu.nl/coronavirus/6039787/lockdown-wuhan-wordt-over-twee-weken-opgeheven.html")
# r.raise_for_status()
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
        c.create_articles(2, 1382, [a])

