import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ.get('mongo_link'))
db = client.letters_sorting
collection = db.letterssorting

# print(collection.estimated_document_count())
for doc in collection.find():
    prisoner_id = doc['_id']
    name = doc['name']
    surname = doc['surname']
    patronymic = doc['patronymic']
    collection.delete_many({'name': name, 'surname': surname, 'patronymic': patronymic, '_id': {'$ne': prisoner_id}})
# print(collection.estimated_document_count())
