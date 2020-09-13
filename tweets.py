import csv



from amcatclient import AmcatAPI
c = AmcatAPI("http://vu.amcat.nl")

with open("InstaMocomuseum.csv", 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        a={}
        a['insta_id'] = row['ID']
        a['URL'] = row['URL']
        a['likes'] = row['Likes']
        a['author'] = row['Owner']
        if row['Text'] == "":
            a['text'] = "-"
        else:
            a['text'] = row['Text']
        a['date'] = row['Date']
        a['title'] = "-"
        print(a)
        c.create_articles(19, 1352, [a])



#date, medium, url, author, text, sentiment, pr

#    fieldnames = ["date","medium", "url","author","text","sentiment","pr"]
