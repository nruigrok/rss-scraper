import requests
from lxml import etree
import datetime

url = "https://www.bosscheomroep.nl/rss"

r = requests.get(url)
r.raise_for_status()
# fix broken feeds
feed = r.content.replace(b"&nbsp;", b" ")
urlset = etree.fromstring(feed)
NS = urlset.nsmap
print("!!!!!", NS)
for url in urlset.findall("url", NS):
    article_link = url.find("loc", NS).text
    article_title = url.find(".//news:title", NS).text
    date = url.find(".//news:publication_date", NS).text
    date = date[:-6].strip()
    article_date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M")
    print(article_title, article_date, article_link)