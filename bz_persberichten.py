from lxml import html, etree
from amcatclient import AmcatAPI
import requests
from itertools import count
from datetime import datetime
import html2text
import re
import datetime
import html2text
import sys
from datetime import date

URL_TEMPLATE = "https://www.rijksoverheid.nl/actueel/nieuws?periode-van=01-04-2020&periode-tot=15-10-2020&onderdeel=Ministerie+van+Buitenlandse+Zaken&pagina={page}"
URL_ROOT = "https://www.rijksoverheid.nl"

def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
        raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]
    
def scrape_pb(url):
    url = URL_ROOT + url
    page = requests.get(url)
    tree = html.fromstring(page.text)
    headline = get_css(tree, "h1.news")
    headline = headline.text_content()
    lead = get_css(tree, "div.intro")
    lead = lead.text_content()
    date = get_css(tree, "p.article-meta")
    date = date.text_content()
    m = re.search((r'\d{2}-\d{2}-\d{4}'),(date))
    if m:
        date2 = datetime.datetime.strptime(m.group(), '%d-%m-%Y').date()
    content = tree.cssselect("div > div.contentBox")
    content += tree.cssselect("div.intro ~ p")
    body2=[]
    body2.append(lead)
    for cont in content:
        text = cont.text_content()
        body2.append(text)
    body2 = "\n\n".join(body2)
    date3 =date2
    return {"title": headline,
            "text": body2,
            "date": date3,
            "medium": "Persberichten",
            "url": url}

def get_links():
    for page in range(1, 20):
        url = URL_TEMPLATE.format(**locals())
        page = requests.get(url)
        tree = html.fromstring(page.text)
        links = list(tree.cssselect('a.news'))
        if not links:
            if "Er zijn geen persberichten aanwezig" in page.text:
                break
            raise Exception("No links but also not done?")

        for a in links:
            link = a.get("href")
            if not link.startswith("/actueel/"):
                raise ValueError("Not a persbericht? {link}".format(**locals()))
            yield link


#a = scrape_pb("/actueel/nieuws/2019/03/04/reactie-minister-blok-op-het-terugroepen-van-de-nederlandse-ambassadeur-uit-iran")
#print(a)
#sys.exit()
from amcatclient import AmcatAPI
conn = AmcatAPI("https://bz.nieuwsmonitor.org")
for link in get_links():
    print(link)
    a = scrape_pb(link)
    conn.create_articles(2, 6, [a])
    
