import pymongo
import pandas as pd
username = 'atufashireen'
password = '7rrww1b9aQcv9mSF'
# email
url = f"mongodb+srv://{username}:{password}@analytics.lmbi7.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
mongo_client = pymongo.MongoClient(url)
mydb = mongo_client['usersinfo']
mycol=mydb['registered']
# email_found = mycolquery={"email": email})
myquery = { "email": "atufa@gm.cm" }
newvalues = { "$set": { "filename": "" } }
t = mycol.find(myquery)
print(t[0].get('filename'))
for i in t:
    print(i,i.get('filename'))
# print(t.get('filename'))
mycol.update_one(myquery, newvalues)
print(t)
# print(t.get('filename'))