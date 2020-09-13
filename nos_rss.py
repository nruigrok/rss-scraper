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

Article = collections.namedtuple("Article", ["title","link","medium","author","date","text","rss_feed"])

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


def get_entries_nos(url, medium, rss_feed):
    r = requests.get(url)
    r.raise_for_status()
    # fix broken feeds
    feed = r.content.replace(b"&nbsp;", b" ")
    t = etree.fromstring(feed)
    print(feed)
    data2 = []
    for item in t.cssselect("div#bodyblock li.regularitem"):
        print(item)
        article_medium = medium
        print(f"dit is medium {article_medium}")
        article_rss_feed = rss_feed
        article_title, = item.cssselect("h4.itemtitle a")
        article_title = article_title.text
        article_link, = article_title.get("href")
        article_link = article_link.text
        article_text = item.cssselect('itemcontent')
        if len(article_text) > 1:
            raise Exception("more descriptions")
        if article_text:
            article_text2 = "\n\n".join(p.text_content() for p in article_text)
        else:
            article_text2 = None
        dates = item.cssselect("h5.itemposttime")
        if len(dates) > 1:
            raise Exception("More than one date")
        if dates:
            date = dates[0]
            date = date.text
            date = date[:-5].strip()
            article_date = datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S")
        else:
            article_date = None
        data = Article(article_medium, article_rss_feed,article_title, article_link,article_date, article_text2)
        print(data)
        data2.append(data)
    return data2


def add_to_database(feed, conn):
    existing_urls = get_db_urls(conn)
    to_insert = [x for x in feed if x.link not in existing_urls]
    logging.info(f"will insert {len(to_insert)} extra articles to database")
    with conn:
        cursor = conn.cursor()
        cursor.executemany(f"insert into articles (title,link,medium,author,date,text,rss_feed) VALUES (?,?, ?,?,?,?,?)", to_insert)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')
    db = "landelijkemedia.db"
    with open("rss_landelijk.csv", 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=",")
        for row in csv_reader:
            medium = row['medium']
            conn = create_connection(db)
            rss_feed = row['rss_feed']
            print(rss_feed)
            if "nos.nl" in rss_feed:
                feed = get_entries_nos(rss_feed, medium, rss_feed)
            add_to_database(feed, conn)
