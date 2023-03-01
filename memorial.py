import re
import requests
from bs4 import BeautifulSoup
from prisoner_class import Prisoner
from reference_info import FSIN_checker
import mongo_file

common_list_link = 'https://memopzk.org/list-persecuted/spisok-politzaklyuchyonnyh-bez-presleduemyh-za-religiyu/?download'
religious_list_link = 'https://memopzk.org/list-persecuted/spisok-politzaklyuchyonnyh-presleduemyh-za-religiyu/?download'

common_list_request = requests.get(common_list_link, allow_redirects=True)
open('common_list.txt', 'wb').write(common_list_request.content)

religious_list_request = requests.get(religious_list_link, allow_redirects=True)
open('religious_list.txt', 'wb').write(religious_list_request.content)


def csv_reader(file):
    prisoners = []
    with open(file, 'r', encoding='utf-8') as prisoner_list:
        for record in prisoner_list.readlines()[1:]:
            prisoner_link = record.strip().split(';')[1]
            fio = record.strip().split(';')[0].split()
            name = fio[1]
            surname = fio[0]
            if len(fio) > 2:
                patronymic = fio[2]
            else:
                patronymic = None
            prisoners.append([prisoner_link, name, surname, patronymic])

    return prisoners


non_religious_result = csv_reader('common_list.txt')
religious_result = csv_reader('religious_list.txt')
common_result = non_religious_result + religious_result


date_of_birth = None
address = None
postcode = None
region = None
prison = None
city = None
street = None
building = None
photo = None
ways = []

for person in common_result:
    memorial_link = person[0]
    memorial_page = requests.get(memorial_link).text
    memorial_soup = BeautifulSoup(memorial_page, 'lxml')

    article = memorial_soup.find('a', attrs={'class': 'clause__link'}).get_text(strip=True)

    description = memorial_soup.find('meta', attrs={'property': 'og:description'}).get('content')

    date_of_birth_example = re.compile(r'родился \d{1,2}\D*\d{4} года')
    if re.search(date_of_birth_example, description):
        date_of_birth = re.search(date_of_birth_example, description).group(0).strip('родился ')

    photo_link = memorial_soup.find('img').get('src')
    photo = photo_link

    try:
        raw_address = memorial_soup.find('div', attrs={'data-modal': 'letter'}).get_text(strip=True)
        address_example = re.compile(r'.*\d{6},.*\d{4}.*г. ?р.')
        address = re.search(address_example, raw_address).group(0).strip('Написать письмо ')
    except:
        address = 'Адрес отсутствует'

    for elem in address.split(','):
        crimean_solidarity = re.compile(r'Крымск(?:ая|ой)\s*солидарност[ьи]', re.IGNORECASE)
        postcode_example = re.compile(r'(\d{6})')
        region_aliases = re.compile(r'по?\s?(\D*(?:ая|ой|ому)\s*(?:республик[ае]|област[ьи]|кра[йю]))', re.IGNORECASE)
        city_example = re.compile(r'\D{4,}\s*(г[.]\s*\D*)\s*', re.ASCII)
        prison_example = re.compile(r'((СИЗО|T|ИК)-?\s*\d{1,3})', re.IGNORECASE)
        street_aliases = re.compile(r'((?:ул|бульвар)[.][^ь]?\s*\D*\s*)', re.IGNORECASE)
        building_example = re.compile(r'(\d{1,3})\D?', re.IGNORECASE)
        if re.search(prison_example, elem):
            prison = re.search(prison_example, elem).group(1)
            if re.search(city_example, elem):
                city = re.search(city_example, elem).group(1)
        elif re.search(region_aliases, elem):
            region = (re.search(region_aliases, elem).group(1))
            region = region.replace('республике', 'республика')
            region = region.replace('края', 'край')
            region = region.replace('области', 'область')
            region = region.replace('ой', 'ая')
        elif re.search(postcode_example, elem):
            postcode = re.search(postcode_example, elem).group(0)
        elif re.search(building_example, elem):
            building = re.search(building_example, elem).group(1)
        elif re.search(street_aliases, elem):
            street = re.search(street_aliases, elem).group(1)

        elif re.search(crimean_solidarity, elem):
            ways.append('Крымская солидарность')

    if FSIN_checker(region, prison):
        ways.append('ФСИН-письмо')

    prisoner = Prisoner(link=person[0], source='Мемориал', name=person[1], surname=person[2], patronymic=person[3],
                        date_of_birth=date_of_birth, description=description, article=article, category=None,
                        hometown=None, address=address, postcode=postcode, region=region, city=city, prison=prison,
                        street=street, building=building, photo=photo, sex=None, ways=[], frequency=None)
    mongo_file.collection.insert_one(prisoner.__dict__)
