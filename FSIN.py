import requests
from bs4 import BeautifulSoup

# FSIN database: two following lines are form a json with all available colonies
FSIN_base = requests.get('https://fsin-pismo.ru/client/rest/static/regions')
FSIN_json = FSIN_base.json()