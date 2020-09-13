
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


#def get_link(csv):
 #   with open(csv, 'r') as csv_file:
  #      csv_reader = csv.DictReader(csv_file, delimiter=';')
   #     urls =[]
    #    for row in csv_reader:
     #       url = row['url']
      #      urls.append(url)
       #     print(urls)
       # return(urls)


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
    except:
        title = ""
        logging.warning("Could not parse article title")
    text = tree.cssselect("p.text_3v_J6Y0G")
    if not text:
        text = tree.cssselect("header.liveblog-header")
        if not text:
            text = tree.cssselect("div.article_textwrap")
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    text = polish(text)
    time_spans = tree.cssselect("span.published_WzR_NC-U time")
    if not time_spans:
        time_spans = tree.cssselect("span.liveblog-header__meta-supplychannel-sub-title time")
    time = time_spans[0].get("datetime")
    #date =time.get("datetime")
    locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
    date = datetime.strptime(time[:19], "%Y-%m-%dT%H:%M:%S")
    return {"headline": title,
            "text": text,
            "date": date,
            "medium": "nos (www)",
            "url": url}


def get_links(f):
    with open(f, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        urls = []
        for row in csv_reader:
            url = row['url']
            if url.startswith("https://nos.nl/artikel"):
                urls.append(url)
        return(urls)



from amcatclient import AmcatAPI
c = AmcatAPI("https://amcat.nl")


links=get_links('nos2.csv')
links = set(links)
for l in links:
    print(l)
    a = scrape_article(l)
    if a is not None:
        c.create_articles(2094, 80427, [a])
