
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



def scrape_article(url):
    try:
        page = requests.get(url)
    except:
        logging.error(f"no url {url}")
    try:
        tree = html.fromstring(page.text)
    except:
        logging.error("HTML tree cannot be parsed")
    if tree.cssselect("h1.page-403--title"):
        return
    if tree.cssselect("h1.text-center"):
        return
    if tree.cssselect("h1.article__title"):
        return
    title = tree.cssselect('h1.node-title')
    if not title:
        title = tree.cssselect("div.column.page__title")
        if not title:
            title = tree.cssselect("h1#text")
            if not title:
                title = tree.cssselect("h1")
    title = title[0].text_content()
    lead = tree.cssselect("p.lede")
    lead = lead[0].text_content()
    text = tree.cssselect("div.paragraph.paragraph--type--paragraph-text")
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    if not text:
        text = "-"
    text2 = lead.join(text)
    text2 = polish(text2)
    time = tree.cssselect("span.time.time-created")
    if not time:
        time = tree.cssselect("span.time")
    time = time[0].text_content()
    locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
    date = datetime.strptime(time, "%d %B %Y %H:%M")
    return {"headline": title,
            "text": text,
            "date": date,
            "medium": "rtl (www)",
            "url": url}




def get_links(f):
    with open(f, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        urls = []
        for row in csv_reader:
            url = row['url']
            if url.startswith("https://www.rtlnieuws.nl/"):
                urls.append(url)
        return(urls)



from amcatclient import AmcatAPI
c = AmcatAPI("https://amcat.nl")


links=get_links('rtl2.csv')
links = set(links)
for l in links:
    if 'video' in l:
        continue
    print(l)
    a = scrape_article(l)
    if a is not None:
        c.create_articles(2094, 80427, [a])
