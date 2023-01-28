import pymongo
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ.get('mongo_link'))
db = client.letters_sorting
collection = db.letterssorting

print(db.list_collection_names())
