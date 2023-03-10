import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import argparse

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys/wired-analogy-379505-f88801e83871.json"
cred = credentials.ApplicationDefault()

firebase_admin.initialize_app(cred)
db = firestore.client()

parser = argparse.ArgumentParser()
parser.add_argument('--accountname')
args = parser.parse_args()

# doc_ref = db.collection(u'accounts').document(u'myfirstaccount')
doc_ref = db.collection(u'accounts').document(args.accountname)

f = open("keys/firestore-hash", "w")
f.write(doc_ref.get().to_dict()["password_hash"])
f.close()

