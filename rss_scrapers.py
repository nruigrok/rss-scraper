import logging
import sqlite3

from requests import HTTPError

from online_scrapers import all_scrapers


def get_text(link):
    for scraper in scrapers:
        if scraper.can_scrape(link):
            return scraper.scrape_text(link)
    logging.error(f"No scraper available for {link}")
    return None


def get_articles(conn, where="status is null", n=100):
    cur = conn.cursor()
    cur.execute(f"SELECT link as url, title, medium as publisher, date FROM articles where {where} limit {n}")
    colnames = [x[0] for x in cur.description]
    rows = cur.fetchall()
    return [dict(zip(colnames, r)) for r in rows]


class SkipArticle(Exception):
    pass

def scrape_article(link):
    if ('video' in link) or ('redirect' in link) or ('Liveblog' in article['title']):
        raise SkipArticle("Video/redirect/liveblog")
    try:
        text = get_text(link)
    except HTTPError as err:
        if (err.response.status_code == 404) or (err.response.status_code == 403) or (err.response.status_code == 410):
            logging.error(f"Article not found (404, 403): {link}")
            raise SkipArticle("404")
        else:
            raise
    if not text:
        raise SkipArticle("Empty")
    return text


def set_status(conn, articles, status='done'):
    urls = ",".join(f"'{a['url']}'" for a in articles)
    with conn:
        cur = conn.cursor()
        cur.execute(f"Update articles set status = '{status}' where link in ({urls})")


logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

from amcatclient import AmcatAPI
c = AmcatAPI("http://localhost:8000")
scrapers = all_scrapers()

db = "coosto.db"
conn = sqlite3.connect(db)
project = 1
articleset = 129

while True:
    logging.info("Retrieving articles to scrape from database")
    articles = get_articles(conn)
    if not articles:
        break
    to_save = []
    to_skip = []

    for i, article in enumerate(articles):
        logging.info(f"[{i + 1}/{len(articles)}] Scraping article {article['url']}")
        try:
            print(article['url'])
            article['text'] = scrape_article(article['url'])
            to_save.append(article)
        except SkipArticle:
            to_skip.append(article)

    logging.info(f"Saving {len(to_save)} articles, skipped {len(to_skip)}")

    c.create_articles(project, articleset, to_save)
    set_status(conn, to_save, status='done')
    set_status(conn, to_skip, status='skip')

logging.info("DONE")
