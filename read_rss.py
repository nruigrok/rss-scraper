"""
Read article metadata from LexisNexis CSS feed and add to local database
"""


import collections
import logging
import sqlite3
import sys
import time
from pathlib import Path

import feedparser

Article = collections.namedtuple("Article", ["id", "title", "link", "medium", "author", "date", "license"])

def create_database(database):
    conn = sqlite3.connect(database)
    sql = """CREATE TABLE articles (
    article_id INTEGER,
    title TEXT,
    link TEXT,
    medium TEXT,
    author TEXT,
    date TEXT,
    licence TEXT,
    status TEXT,
    public_link TEXT,
    license text    
    );"""
    cur = conn.cursor()
    cur.execute(sql)
    return conn



def get_db_ids(conn):
    cur = conn.cursor()
    cur.execute("SELECT article_id FROM articles")
    rows = list(cur.fetchall())
    db_ids = []
    for row in rows:
        id = row[0]
        db_ids.append(id)
    return db_ids


def get_entries(feed):
    data2 = []
    for entry in feed.entries:
        article_id = entry.m_article_id
        article_title = entry.title
        article_link = entry.link
        article_medium = entry.source['title']
        article_author = getattr(entry, 'author', None)
        article_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
        article_licence = entry.m_name
        data = Article(article_id, article_title, article_link, article_medium, article_author,
                       article_date, article_licence)
        data2.append(data)
    return data2


def add_to_database(art, conn):
    existing_ids = get_db_ids(conn)
    to_insert = [x for x in art if int(x[0]) not in existing_ids]
    logging.info(f"will insert {len(to_insert)} extra articles to database")
    with conn:
        cursor = conn.cursor()
        cursor.executemany(f'insert into articles (article_id, title, link, medium, author, date, license) VALUES (?, ?,?,?,?,?,?)', to_insert)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Database name", type=Path)
    parser.add_argument("url", help="NewsDesk feed URL (https://newsdesk-feeds.moreover.com/...)")
    args = parser.parse_args()

    if not args.db.exists():
        logging.info(f"Initializing new database {args.db}")
        conn = create_database(args.db)
    else:
        conn = sqlite3.connect(args.db)

    logging.info(f"Retrieving articles into {args.db} from {args.url} ...")
    feed = feedparser.parse(args.url)
    if feed.bozo:
        raise feed.bozo_exception
    art = get_entries(feed)
    add_to_database(art, conn)
