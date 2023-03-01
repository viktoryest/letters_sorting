from FSIN import FSIN_json

regions = []
for region in FSIN_json:
    regions.append(region['name'])


cities = []
with open('cities.txt', 'r', encoding='utf-8') as file:
    for city in file:
        cities.append(city.strip())
cities = list(set(cities))


def FSIN_checker(region, prison):
    for item in FSIN_json:
        if item['name'] == region:
            for elem in item['departments']:
                if elem['name'] and prison and prison in elem['name']:
                    return True

