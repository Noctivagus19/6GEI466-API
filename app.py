from datetime import datetime
from flask import (
    Flask,
)

from apscheduler.schedulers.background import BackgroundScheduler
from bson.json_util import dumps
import json
import pymongo
import urllib
from urllib.parse import urlencode
import urllib3

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

http = urllib3.PoolManager()

db_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = db_client['iss']
col_astronaut = db['astronaut']
col_iss_pos = db['iss_position']


@app.route('/api/v1/iss/astronauts', methods=["GET"])
def iss_astronauts():
    astronauts = col_astronaut.find({})
    return dumps(astronauts)


@app.route('/api/v1/iss/positions', methods=["GET"])
def iss_positions():
    positions = col_iss_pos.find({})
    return dumps(positions)


def up_in_space():
    r = http.request('GET', 'http://api.open-notify.org/astros.json')
    obj = json.loads(r.data)
    iss_astronauts = []
    for astro in obj["people"]:
        if astro["craft"] == 'ISS':
            astro['wiki_page'] = search_wikipedia(astro['name'])
            iss_astronauts.append(astro)

    col_astronaut.insert_many(iss_astronauts)


def get_iss_position():
    r = http.request('GET', 'http://api.open-notify.org/iss-now.json')
    obj = json.loads(r.data)
    longitude = obj['iss_position']['longitude']
    latitude = obj['iss_position']['latitude']
    col_iss_pos.insert(
        {
            "longitude": longitude,
            "latitude": latitude,
        }
    )


def search_wikipedia(term):
    payload = {
        'action': 'query',
        'list': 'search',
        'prop': 'pageimages',
        'srsearch': f'{term} astronaut',
        'format': 'json',
    }
    payload = urlencode(payload, quote_via=urllib.parse.quote)
    wiki_url = 'http://en.wikipedia.org/'
    link = f'{wiki_url}w/api.php?{payload}'
    r = http.request('GET', link)
    obj = json.loads(r.data)

    wiki_page = {}

    if len(obj['query']['search']) > 0:
        first_result = obj['query']['search'][0]
        page_title = str.replace(first_result['title'], ' ', '_')
        wiki_page['url'] = f'https://en.wikipedia.org/wiki/{page_title}'
        wiki_page['snippet'] = first_result['snippet']

        page_id = str(first_result["pageid"])

        payload = {
            'action': 'query',
            'prop': 'pageimages',
            'titles': first_result['title'],
            'format': 'json',
            'pithumbsize': 200,
        }

        payload = urlencode(payload, quote_via=urllib.parse.quote)
        link = f'{wiki_url}w/api.php?{payload}'
        r = http.request('GET', link)

        obj = json.loads(r.data)
        if len(obj['query']['pages']) > 0:
            try:
                wiki_page['image'] = obj['query']['pages'][page_id]['thumbnail']['source']
            except:
                wiki_page['image'] = None

    return wiki_page


@scheduler.scheduled_job('interval', minutes=15, next_run_time=datetime.now())
def update_astro_in_iss():
    col_astronaut.remove({})
    up_in_space()

    print(f"update_astro_in_iss job runned at {datetime.now()}")


@scheduler.scheduled_job('interval', minutes=1, next_run_time=datetime.now())
def update_iss_positions():
    positions = col_iss_pos.find({})
    if positions.count() > 60:
        col_iss_pos.remove({})

    get_iss_position()

    print(f"update_iss_positions job runned at {datetime.now()}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
