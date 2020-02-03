
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


def scrape_article(url):
    try:
        page = requests.get(url)
    except:
        logging.error(f"no url {url}")
    try:
        tree = html.fromstring(page.text)
    except:
        logging.error("HTML tree cannot be parsed")
    try:
        title = tree.xpath('//h1')[0].text
    except (ValueError, IndexError, KeyError) as e:
       return
    text = tree.cssselect("div.block-content")
    if not text:
        text = tree.cssselect("header.liveblog-header")
        if not text:
            text = tree.cssselect("div.article_textwrap")
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    time = tree.xpath('//span[@class="pubdate large"]')
    try:
        time2 = time[0].text_content()
    except (IndexError, ValueError) as e:
        pass
    locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
    date = datetime.strptime(time2, "%d %B %Y %H:%M")
    return {"title": title,
            "text": text,
            "date": date,
            "medium": "nu (www)",
            "url": url}


def get_links(f):
    with open(f, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        urls = []
        for row in csv_reader:
            url = row['url']
            if url.startswith("https://www.nu.nl/"):
                urls.append(url)
        return(urls)



from amcatclient import AmcatAPI
c = AmcatAPI("http://localhost:8000")


#links=get_links('bz1.csv')
#for l in links:

l = "https://www.nu.nl/seminars/6005827/seminar-mindgym-sportschool-voor-je-geest-met-wouter-de-jong.html"
a = scrape_article(l)
c.create_articles(1, 80, [a])

