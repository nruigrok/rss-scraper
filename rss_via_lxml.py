url = "https://sleutelstad.nl/feed/"
url = "https://www.regio8.nl/rss"
url = "https://omroephorstaandemaas.nl/rss/nieuws"
url = "http://www.radiohengelotv.nl/rss"
url = "http://www.rtvsternet.nl/rss"
url = "https://studio040.nl/rss/nieuws"
url = "https://leomiddelse.nl/rss"
url = "https://www.oogtv.nl/rss"
url = "https://www.rtvnof.nl/rss"
url = "https://www.bollenstreekomroep.nl/rss"
url = "https://www.rtvkatwijk.nl/rss"
url = "https://www.langstraatmedia.nl/rss"
url = "https://www.regionoordkop.nl/rss"
url = "https://rss.at5.nl/rss"
url = "https://www.rtvdordrecht.nl/rss"

# url = "https://www.bosscheomroep.nl/rss" CHECK!

import requests, lxml
from lxml import etree, html

r = requests.get(url)
r.raise_for_status()

# fix broken feeds
feed = r.content.replace(b"&nbsp;", b" ")
t = etree.fromstring(feed)

#t = html.fromstring(r.text)

for item in t.cssselect("item"):
    title, = item.cssselect("title")
    link, = item.cssselect("link")
    print(title.text, link.text)


