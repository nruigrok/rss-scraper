import requests
session = requests.session()
session.get("https://login.nrc.nl/login")

links = ["https://www.nrc.nl/nieuws/2020/03/25/alles-kraakt-nu-in-het-ziekenhuis-a3994939",
         "https://www.nrc.nl/nieuws/2020/03/25/mag-ik-nog-met-vier-vrienden-naar-buiten-a3994890",
         "https://www.nrc.nl/nieuws/2020/03/25/kabinet-laat-de-volkswil-meetellen-in-de-coronacrisis-a3994880",
         "https://www.nrc.nl/nieuws/2020/03/25/ramvolle-londense-metro-doet-britse-politieke-vete-oplaaien-a3994881",
         "https://www.nrc.nl/nieuws/2020/03/25/wat-betekent-het-schrappen-van-de-eindexamens-a3994876",
         "https://www.nrc.nl/nieuws/2020/03/25/het-leiderschap-van-premier-conte-krijgt-rafelrandjes-a3994905",
         ]

for link in links:
    r = session.get(link)
    r.raise_for_status()
    print("In een land dat gewend is aan een kakafonie van stemmen " in r.text)
    open("/tmp/test8.html", "w").write(r.text)