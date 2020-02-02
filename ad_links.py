from urllib.parse import unquote, urlparse

from rsslib import create_connection
from lxml import html
import requests
from datetime import datetime
import locale
import logging
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime




def get_links(conn):
    cur = conn.cursor()
    cur.execute("SELECT public_link FROM articles where medium ='Trouw' and status='public'")
    rows = list(cur.fetchall())
    db_links = []
    for row in rows:
        id = row[0]
        db_links.append(id)
    return db_links



def scrape_article(session, url):
    r = session.get(url)
    r.raise_for_status()
    tree = html.fromstring(r.text)
    title, = tree.cssselect("h1.article__title")
    title = title.text_content()
    try:
        lead, = tree.cssselect("p.article__intro")
        lead = lead.text_content()
        lead = str(lead)
    except ValueError:
        lead = ""
    text = tree.cssselect("p.article__paragraph")
    if not text:
        text = "-"
    else:
        text = "\n\n".join([p.text_content() for p in text])
    text2 = "\n\n".join([lead, text])
    text2 = re.sub("\n\n\s*", "\n\n", text2)
    print(text2)
    time, = tree.cssselect("time.article__time")
    time=time.text_content()
    print(time)
    time2 = time.split(",")[0]
    print(time2)
    time2 = time2.replace(',', '')
    time2 = time2.replace('.', '')
    time2 = time2.strip()
    print(time2)
    locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
    try:
        date = datetime.strptime(time2, "%d-%m-%y")
    except:
        ValueError(f"something went wrong with {time2}")
        try:
            date = datetime.strptime(time2, "%d %m %y")
        except:
            ValueError(f"something went wrong with {time2}")
            date = datetime.strptime(time2, "%d %b %Y")
    return {"title": title,
            "text": text2,
            "date": date,
            "publisher": "trouw (www)",
            "url": url}

def extract_link(url):
    # decode double-encoded redirect link
    # 'https://myprivacy.dpgmedia.net/?siteKey=V9f6VUvlHxq9wKIN&callbackUrl=https%3a%2f%2fwww.ad.nl%2fprivacy-gate%2faccept%3fredirectUri%3d%252fpolitiek%252follongren-helaas-ben-ik-nog-te-ziek-om-mijn-werk-te-doen%257ea4e8fdee%252f'
    query = unquote(urlparse(url).query)
    redirect = unquote(urlparse(query).query)
    if not redirect.startswith("redirectUri="):
        raise ValueError(f"Cannot decode url {repr(url)}")
    url = redirect[len("redirectUri="):]
    return f"https://ad.nl{url}"

# Set cookie accept cookies
s = requests.session()
cookie = dict(domain="www.ad.nl", path="/",  name="pws",
              value="functional|analytics|content_recommendation|targeted_advertising|social_media")
s.cookies.set(**cookie)
cookie = dict(domain="www.ad.nl", path="/",  name="pwv", value="2")
s.cookies.set(**cookie)


conn = create_connection()
links = get_links(conn)

from amcatclient import AmcatAPI
c = AmcatAPI("http://localhost:8000")

for l in links:
    url = extract_link(l)
    print(url)
    a = scrape_article(s, url)
    c.create_articles(1, 76, [a])
