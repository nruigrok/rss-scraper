import csv

import datetime
import logging

from amcatclient import AmcatAPI


def parse_row(row):
    article = {}
    article['url'] = row['url']
    date = row['date']
    date = datetime.datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
    article['date'] = date
    article['title'] = "-"
    article['text'] = row['text']
    if not article['text']:
        article['text'] = "-"
    if article['text'] is None:
        article['text'] = "-"
    article['author'] = row['author']
    article['sentiment'] = row['Sentiment']
    article['publisher'] = "BZ"
    return article


def get_articles(fn):
    with open(fn, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=";")
        for row in csv_reader:
            article = parse_row(row)
            yield article

def create_articles(conn, project, aset, articles):
    logging.info(f"Uploading {len(articles)} articles")
    conn.create_articles(project, aset, articles)


logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')
buffer = []
c = AmcatAPI("https://bz.nieuwsmonitor.org")


fn = "kaag_april2.csv"
logging.info(f"Reading articles from {fn}")

for art in get_articles(fn):
    buffer.append(art)
    if len(buffer) >= 100:
        create_articles(c, 2, 13, buffer)
        buffer = []

if len(buffer) > 0:
    create_articles(c, 2, 13, buffer)




#date, medium, url, author, text, sentiment, pr

#    fieldnames = ["date","medium", "url","author","text","sentiment","pr"]
