
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
        return
    try:
        tree = html.fromstring(page.text)
    except:
        logging.error("HTML tree cannot be parsed")
        return
    try:
        title = tree.cssselect('h1.title.fluid')
        title = title[0].text_content()
    except (ValueError, IndexError, KeyError) as e:
        logging.error("title cannot be parsed")
        return
    #lead = tree.cssselect("div.block-content.excerpt > p")
    text = tree.cssselect("div.block-content > p")
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    time = tree.xpath('//span[@class="pubdate large"]')
    try:
        time2 = time[0].text_content()
    except (IndexError, ValueError) as e:
        logging.error("Time cannot be parsed")
        return
    locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
    date = datetime.strptime(time2, "%d %B %Y %H:%M")
    return {"headline": title,
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
c = AmcatAPI("https://amcat.nl")


links = get_links('nu2.csv')
links = set(links)
for l in links:
    print(l)
    a = scrape_article(l)
    if a is not None:
        c.create_articles(2094, 80427, [a])

