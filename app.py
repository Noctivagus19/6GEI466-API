from datetime import datetime
from flask import (
    Flask,
    jsonify,
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


@app.route('/api/v1/iss/astronauts', methods=["GET"])
def iss_astronauts():
    astronauts = col_astronaut.find({})
    return dumps(astronauts)



def up_in_space():
    r = http.request('GET', 'http://api.open-notify.org/astros.json')
    obj = json.loads(r.data)
    iss_astronauts = []
    for astro in obj["people"]:
        if astro["craft"] == 'ISS':
            astro['wiki_page'] = search_wikipedia(astro['name'])
            iss_astronauts.append(astro)

    col_astronaut.insert_many(iss_astronauts)


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

    return wiki_page


@scheduler.scheduled_job('interval', minutes=15, next_run_time=datetime.now())
def update_caching():
    print(f"The scheduled job runned at {datetime.now()}")

    col_astronaut.remove({})
    up_in_space()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
