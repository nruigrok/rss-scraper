import logging
import re
from collections import namedtuple

from amcatclient import AmcatAPI
from lxml import html
import requests

from rsslib import create_connection


def get_articles(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM articles where public_link is null and status is null")
    rows =[]
    colnames = [x[0] for x in cur.description]
    Row = namedtuple("Row", colnames)
    row = cur.fetchall()
    for r in row:
        r = Row(*r)
        rows.append(r)
    return rows


def login(username, password):
    s = requests.Session()
    s.get("https://www.newsdesk.lexisnexis.com")
    payload = {"userid": username,
               "password": password,
              }
    login = s.post("https://signin.lexisnexis.com/lnaccess/Transition?aci=nd", data=payload )
    login.raise_for_status()
    return s


def scrape_text(session, url):
    res = session.get(url)
    if not res.url.startswith("https://www.newsdesk.lexisnexis.com"):
        # Not a LN url
        return None, res.url
    page = html.fromstring(res.text)
    text = page.cssselect("section.article_extract *")
    if not text:
        open("/tmp/check.html", "wb").write(res.content)
        raise Exception(f"Could not scrape article from {url} -> {res.url}, written html to /tmp/check.html")
    # add paragraph separators to <br/> tags
    for p in text:
        for br in p.xpath(".//br"):
            br.tail = "\n\n" + br.tail if br.tail else "\n\n"
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    return text, res.url


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("nd_username", help="Newsdesk username")
    parser.add_argument("nd_password", help="Newsdesk password")
    parser.add_argument("hostname", help="AmCAT Server hostname")
    parser.add_argument("project", help="AmCAT Project ID", type=int)
    parser.add_argument("articleset", help="AmCAT Articleset ID", type=int)
    parser.add_argument("--verbose", "-v", help="Verbose (debug) output", action="store_true", default=False)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

    conn = create_connection()
    logging.info("Logging in to LN")
    session = login(args.nd_username, args.nd_password)

    logging.info(f"Connecting to AmCAT server {args.hostname}")
    c = AmcatAPI(args.hostname)

    for row in get_articles(conn):
        logging.info(f"Scraping article {row.article_id} from {row.link}")
        text, url = scrape_text(session, row.link)
        if not text:
            logging.info(f"Article {row.article_id} was public: {url}")
            cur = conn.cursor()
            cur.execute("Update articles set status = 'public', public_link=? where article_id = ?", [url, row.article_id])
            continue

        article = {"text": text, "title": row.title, "ln_id": row.article_id, "publisher": row.medium,
                   "author": row.author, "date": row.date, "url": row.public_link}
        article = {k: v for (k, v) in article.items() if v is not None}
        logging.info(f"Uploading article {row.article_id} to amcat project {args.project} set {args.articleset} (headline: {row.title}")

        c.create_articles(args.project, args.articleset, [article])

        cur = conn.cursor()
        cur.execute("Update articles set status = 'done' where article_id = ?", [row.article_id])
