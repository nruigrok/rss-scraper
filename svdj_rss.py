import collections
import logging
import sqlite3
import sys
import time
import requests, lxml
from lxml import etree, html
import datetime
import locale
import feedparser
import csv

Article = collections.namedtuple("Article", ["medium", "rss_feed", "title", "link", "date", "description"])

def create_connection(database):
    return sqlite3.connect(database)


def get_db_urls(conn):
    cur = conn.cursor()
    cur.execute("SELECT link FROM articles")
    rows = list(cur.fetchall())
    db_urls = []
    for row in rows:
        url = row[0]
        db_urls.append(url)
    return db_urls


def get_entries(url, medium, rss_feed):
    r = requests.get(url)
    r.raise_for_status()
    # fix broken feeds
    feed = r.content.replace(b"&nbsp;", b" ")
    t = etree.fromstring(feed)
    data2 = []
    for item in t.cssselect("item"):
        article_medium = medium
        article_rss_feed = rss_feed
        article_title, = item.cssselect("title")
        article_title = article_title.text
        article_link, = item.cssselect("link")
        article_link = article_link.text
        descriptions = item.cssselect('description')
        if len(descriptions) > 1:
            raise Exception("more descriptions")
        if descriptions:
            description = descriptions[0]
            article_description = description.text
        else:
            article_description = None
        dates = item.cssselect("pubDate")
        if len(dates) > 1:
            raise Exception("More than one date")
        if dates:
            date = dates[0]
            date = date.text
            date = date[:-5].strip()
            article_date = datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S")
        else:
            article_date = None
        data = Article(article_medium, article_rss_feed,article_title, article_link,article_date, article_description)
        print(data)
        data2.append(data)
    return data2

def get_entries2(url, medium, rss_feed):
        r = requests.get(url)
        r.raise_for_status()
        # fix broken feeds
        feed = r.content.replace(b"&nbsp;", b" ")
        urlset = etree.fromstring(feed)
        NS = urlset.nsmap
        print("!!!!!", NS)
        data2 = []
        for url in urlset.findall("url", NS):
            article_medium = medium
            article_rss_feed = rss_feed
            article_link = url.find("loc", NS).text
            article_description = None
            article_title = url.find(".//news:title", NS).text
            date = url.find(".//news:publication_date", NS).text
            date = date[:-6].strip()
            article_date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M")
            data = Article(article_medium, article_rss_feed,article_title, article_link,article_date, article_description)
            print(data)
            data2.append(data)
        return data2

def add_to_database(feed, conn):
    existing_urls = get_db_urls(conn)
    to_insert = [x for x in feed if x.link not in existing_urls]
    logging.info(f"will insert {len(to_insert)} extra articles to database")
    with conn:
        cursor = conn.cursor()
        cursor.executemany(f"insert into articles (medium, rssfeed, title, link, date, description) VALUES (?,?, ?,?,?,?)", to_insert)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')
    db = "svdj2020.db"
    with open("rss_feed.csv", 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=",")
        for row in csv_reader:
            medium = row['omroep']
            conn = create_connection(db)
            rss_feed = row['rss_feed']
            if "bosscheomroep.nl" in rss_feed:
                feed = get_entries2(rss_feed, medium, rss_feed)
            else:
                feed = get_entries(rss_feed, medium, rss_feed)
            print(feed)
            add_to_database(feed, conn)
