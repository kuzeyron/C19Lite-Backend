import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def text_strip(text):
    """Removes odd encodings from the html part"""

    for character in ['\n', '\xa0', ' **', ' *']:
        text = text.replace(character, '')

    text = re.sub(r'\([^)]*\)', '', text)

    return text.strip()


def wikipedia(response):
    """Table of content getting put together from Wikipedia"""

    container = {'sv': {}, 'fi': {}, 'en': {}, }

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        for table in soup.find_all(
            "table", {"class": "sortable wikitable"}
        ):
            for tr in table.find_all('tr'):
                rows = []

                for td in tr.find_all('td'):
                    for span in td.find_all('span'):
                        span.decompose()

                    rows.append(text_strip(td.get_text()))

                if rows:
                    container['sv'][rows[0]] = int(rows[3])
                    container['fi'][rows[1]] = int(rows[3])
        container['en'] = {**container['fi'], **container['sv']}

    return container


def cache_get(url, path, ftype='json'):

    headers = {
        'User-Agent': (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/50.0.2661.102 Safari/537.36")}

    response = requests.get(url=url, headers=headers)
    if ftype == 'json':
        content = response.json()
    else:
        content = wikipedia(response)

    with open(path, 'w') as data:
        data.write(json.dumps(content, indent=4))

    return content


def cache_load(path):
    with open(path) as f:
        data = json.load(f)

    return data


def municipality_amount(value, index, key):
    """Converts the amount of diseases into
        a valid `int()` format"""

    value = value.get(str(index.get(key)))

    if value.isdigit():
        amount = int(value)
    else:
        amount = 0

    return amount


def district_strip(data, lang):
    """Puts together the dictionary with all the contents
        from thl.fi and Wikipedia"""

    population = download_district_population(lang)
    dataset = data['dataset']
    value = dataset['value']
    dimension = dataset['dimension']
    target = dimension['hcdmunicipality2020']
    category = target['category']
    labels = category['label']
    index = category['index']
    content = {
        k: {'name': v, 'amount': municipality_amount(
            value, index, k), 'population': population.get(v, 0)}
        for k, v in labels.items()}

    return content


def cache_expired(path, age=(60 * 60)):

    if os.path.exists(path):

        time_now = datetime.now()
        time_stat = os.stat(path).st_mtime
        time_then = datetime.fromtimestamp(time_stat)
        expired = (time_now - time_then).seconds

        if expired > age:
            os.remove(path)

    else:

        expired = age + 1

    return expired


def cache_path(path):
    where = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(f'{where}/content', exist_ok=True)
    path = f"{where}/content/{path}"

    return path


def download_districts(lang='sv'):
    """Downloads the content from thl.fi"""

    path = cache_path(f"districts_{lang}.json")

    if cache_expired(path):

        url = (
            f"https://sampo.thl.fi/pivot/prod/{lang}/"
            f"epirapo/covid19case/fact_epirapo_covid19case."
            f"json?column=hcdmunicipality2020-445268L")
        data = cache_get(url, path)

    else:

        data = cache_load(path)

    return district_strip(data, lang)


def download_district_population(lang='sv'):
    """Reads the table from Wikipedia"""

    path = cache_path("population.json")

    if cache_expired(path, age=(60 * 60 * 24 * 7)):

        url = (
            "https://sv.wikipedia.org/wiki/"
            "Lista_%C3%B6ver_Finlands_kommuner")
        data = cache_get(url, path, ftype='wikipedia')

    else:

        data = cache_load(path)

    return data[lang]


if __name__ == "__main__":
    print(download_districts('sv'))