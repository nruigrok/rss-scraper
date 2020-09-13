import csv
import re
import locale
import datetime
from lxml import html

from amcatclient import AmcatAPI
from pprint import pprint
import collections
import requests
from rsslib import create_connection



c = AmcatAPI("https://bz.nieuwsmonitor.org")



def polish(textstring):
    #This function polishes the full text of the articles - it separated the lead from the rest by ||| and separates paragraphs and subtitles by ||.
    lines = textstring.strip().split('\n')
    lead = lines[0].strip()
    rest = '||'.join( [l.strip() for l in lines[1:] if l.strip()] )
    if rest: result = lead + ' ||| ' + rest
    else: result = lead
    return result.strip()


def scrape_telegraaf(session, url):
    page = session.get(url)
    if page.status_code == 404:
        return
    page.raise_for_status()
    open("/tmp/test7.html", "w").write(page.text)
    tree = html.fromstring(page.text)
    for label in tree.cssselect("span.label"):
        if label.text_content().strip().startswith("Liveblog"):
            return None
    lead_ps = tree.cssselect('p.ArticleIntroBlock__paragraph')
    body_ps = tree.xpath('//div[@data-element="articleBodyBlocks"]/p')
    text = "\n\n".join(p.text_content() for p in lead_ps + body_ps)
    text = polish(text)
    return text



def create_cookie(domain, name, value):
    return {
        "name": name,
        "value": value,
        "domain": domain,
    }

def get_telegraaf():
    COOKIES = {
        '__cfduid':'d56655838cd13e536c63a84867a1cd55c1585123110',
        'clientid':"ck871dfn22m9y568461ch66fv",
        'didomi_token':'eyJ1c2VyX2lkIjoiMTcxMTBiMzMtMTBjYS02YTViLWFkNDAtMmQwMGFjNGJlZTY2IiwiY3JlYXRlZCI6IjIwMjAtMDMtMjVUMDc6NTg6MzEuMjA4WiIsInVwZGF0ZWQiOiIyMDIwLTAzLTI1VDA3OjU4OjUwLjk0OFoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiZmFjZWJvb2siLCJjOm5sLXByb2ZpZWwiXSwiZGlzYWJsZWQiOltdfSwicHVycG9zZXMiOnsiZW5hYmxlZCI6WyJmdW5jdGlvbmVlbCIsInNvY2lhbF9tZWRpYSIsIm5sX3Byb2ZpZWwiLCJjb29raWVzIiwiYWR2ZXJ0aXNpbmdfcGVyc29uYWxpemF0aW9uIiwiY29udGVudF9wZXJzb25hbGl6YXRpb24iLCJhZF9kZWxpdmVyeSIsImFuYWx5dGljcyJdLCJkaXNhYmxlZCI6W119fQ==',
        'euconsent': 'BOwzpeIOwzphNAHABBNLC--AAAAuhr_7__7-_9_-_f__9uj3Or_v_f__32ccL59v_h_7v-_7fi_20nV4u_1vft9yfk1-5ctDztp507iakivXmqdeb9v_nz3_5pxP78k89r7337Ew_v8_v-b7BCON_YxEiA',
        'OB-USER-TOKEN': '82e48dea-c07a-420c-a5e2-cece4269fb48',
        'paywallversion': '1',
    }
    session = requests.session()
    for name, value in COOKIES.items():
        session.cookies.set(**create_cookie("www.telegraaf.nl", name, value))
    r = session.get("https://www.telegraaf.nl/nieuws/1071777683/pvd-a-ers-houden-samengaan-met-groen-links-af")
    r.raise_for_status()
    return session

def get_ad():
    session = requests.session()
    r = session.post(
        "https://www.ad.nl/privacy-gate/accept?redirectUri=%2f&pwv=2&pws=functional%7Canalytics%7Ccontent_recommendation%7Ctargeted_advertising%7Csocial_media&days=390&referrer=")
    r.raise_for_status()
    r = session.get(
        "https://www.ad.nl/politiek/pvda-leden-willen-geen-fusie-met-groenlinks-wel-meer-samenwerking~a4df1178/")
    r.raise_for_status()
    return session


def scrape_ad(session, url):
    page = session.get(url)
    if page.status_code == 404:
        return
    page.raise_for_status()
    open("/tmp/test7.html", "w").write(page.text)
    tree = html.fromstring(page.text)
    lead = tree.cssselect("p.article__intro")
    lead = lead[0].text_content()
    text = tree.cssselect("p.article__paragraph")
    text = "\n\n".join(p.text_content() for p in text)
    text = re.sub("\n\n\s*", "\n\n", text)
    text = polish(text)
    text2 = lead+text
    return text2


from amcatclient import AmcatAPI
c = AmcatAPI("https://amcat.nl")


with open("online_urls.csv", 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=",")
    for row in csv_reader:
        url =row['url']
        print(url)
        artdict ={}
        if 'telegraaf.nl' in url:
            if 'video' in url:
                continue
            session = get_telegraaf()
            date = row['date']
            headline = row['headline']
            text = scrape_telegraaf(session, url)
            artdict['headline']=headline
            artdict['medium']="telegraaf (www)"
            artdict['date']=date
            artdict['text']=text
            artdict['url']=url
            print(artdict)
          #  c.create_articles(2104, 80568, [artdict])
        if 'ad.nl' in url:
            session = get_ad()
            date = row['date']
            headline = row['headline']
            text = scrape_ad(session, url)
            artdict['headline']=headline
            artdict['medium']="ad (www)"
            artdict['date']=date
            artdict['text']=text
            artdict['url']=url
            print(artdict)


#date, medium, url, author, text, sentiment, pr

#    fieldnames = ["date","medium", "url","author","text","sentiment","pr"]
