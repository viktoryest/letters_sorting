import re
import requests
from bs4 import BeautifulSoup
from prisoner_class import Prisoner
import mongo_file
from reference_info import regions, cities, FSIN_checker

rosuznik_pages = [f'https://rosuznik.org/prisoner?page={page}' for page in range(1, 12)]
rosuznik_links = []

for link in rosuznik_pages:
    rosuznik_page = requests.get(link).text
    rosuznik_soup = BeautifulSoup(rosuznik_page, 'lxml')
    h3_tag_set = rosuznik_soup.find_all('h3')
    for h3_tag in h3_tag_set:
        if h3_tag.find('a'):
            rosuznik_links.append(f"https://rosuznik.org{h3_tag.find('a').get('href')}")

for prisoner_link in rosuznik_links:
    prisoner_page = requests.get(prisoner_link).text
    prisoner_soup = BeautifulSoup(prisoner_page, 'lxml')
    title = prisoner_soup.find('h1').get_text().split(' ')

    name = title[1]
    surname = title[0]
    patronymic = title[2]

    prisoner_info = prisoner_soup.find('div', attrs={'class': 'untree_co-section bg-primary-dark py-5'})
    photo_link = f"https://rosuznik.org/{prisoner_info.find('img').get('src')}"

    other_info = prisoner_info.find_all('div', attrs={'class': 'col-lg-3'})

    common_info = prisoner_soup.find('div', attrs={'class': 'accordion-body'})
    if common_info:
        description = common_info.get_text(strip=True)

    hometown = None
    date_of_birth = None
    address = None
    article = None

    for tag in other_info:
        statement = tag.get_text(strip=True)
        match statement.split(':'):
            case ['Адрес', *_]:
                hometown = statement.split(':')[1]
            case ['Год рождения', *_]:
                date_of_birth = statement.split(':')[1]
            case ['Место нахождения', *_]:
                address = statement.split(':')[1]
        match statement.split():
            case [*_] if 'УК' in statement:
                article = statement

    postcode = None
    city = None
    building = None
    prison = None
    region = None
    street = None
    ways = []

    for elem in address.split(', '):
        postcode_example = re.compile(r'\d{6}')
        building_example = re.compile(r'\d{1,3}\D?', re.IGNORECASE)
        prison_example = re.compile(r'СИЗО-?\d{1,3}|T-?\d{1,3}|ИК-\d{1,3}', re.IGNORECASE)
        region_aliases = re.compile(r'по?\s?(\D*(?:ая|ой|ому)\s*(?:республик[ае]|област[ьи]|кра[йю]))', re.IGNORECASE)
        street_aliases = re.compile(r' ул|ул.?', re.IGNORECASE)
        if re.search(postcode_example, elem):
            postcode = elem
        elif len(elem) < 20 and ('г.' in elem or elem in cities[1:]):
            city = elem.strip('г., ')
        elif re.search(prison_example, elem):
            prison = re.search(prison_example, elem).group(0)
            if re.search(region_aliases, elem) or elem in regions:
                region = (re.search(region_aliases, elem).group(1))
                region = region.replace('республике', 'республика')
                region = region.replace('края', 'край')
                region = region.replace('области', 'область')
                region = region.replace('ой', 'ая')
        elif re.search(building_example, elem):
            building = re.search(building_example, elem).group()
        elif re.search(region_aliases, elem) or elem in regions:
            region = elem
        elif re.search(street_aliases, elem):
            street = elem

    if FSIN_checker(region, prison):
        ways.append('ФСИН-письмо')

    prisoner = Prisoner(link=prisoner_link, source='Росузник', name=name, surname=surname, patronymic=patronymic,
                        date_of_birth=date_of_birth, description=description, article=article, category=None,
                        hometown=hometown, address=address, postcode=postcode, region=region, city=city, prison=prison,
                        street=street, building=building, photo=photo_link, sex=None, ways=['Росузник'], frequency=None)
    mongo_file.collection.insert_one(prisoner.__dict__)
