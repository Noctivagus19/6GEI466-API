from datetime import datetime
from flask import (
    Flask,
    request,
    Response,
    jsonify,
)

from apscheduler.schedulers.background import BackgroundScheduler
from bson.json_util import dumps
from geopy.geocoders import Nominatim
from ip2geotools.databases.noncommercial import DbIpCity
import json
import pymongo
from requests import get
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
col_iss_pos = db['position']
col_pass_time = db['pass_time']

geolocator = Nominatim(user_agent="6GEI466_API")


@app.route('/api/v1/iss/astronauts', methods=["GET"])
def iss_astronauts():
    astronauts = col_astronaut.find({})
    return dumps(astronauts)


@app.route('/api/v1/iss/positions', methods=["GET"])
def iss_positions():
    positions = col_iss_pos.find({})
    return dumps(positions)


@app.route('/api/v1/iss/pass-times', methods=["GET"])
def iss_pass_times():
    user_ip = request.remote_addr \
        if request.remote_addr != "127.0.0.1" \
        else get("https://api.ipify.org/").text

    user_loc_info = DbIpCity.get(user_ip, api_key='free')

    user_pass_time = get_iss_pass_times(user_loc_info)
    if user_pass_time:
        return dumps(user_pass_time)
    else:
        return Response(
            "Could not retrieve pass times.",
            status=500,
        )


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

    reverse = geolocator.reverse(f"{latitude}, {longitude}", language='en')

    try:
        state = reverse.raw['address']['state']
        country = reverse.raw['address']['country']
        location = f"{state}, {country}"
    except:
        location = "Unknown"

    col_iss_pos.insert(
        {
            "longitude": longitude,
            "latitude": latitude,
            "location": location,
        }
    )


def get_iss_pass_times(user_loc):
    user_pass_time = {
        "location":
            {
                "country": user_loc.country,
                "region": user_loc.region,
                "city": user_loc.city,
            }
    }
    result = col_pass_time.find_one(user_pass_time)

    if result:
        return result
    else:
        lat = user_loc.latitude
        lon = user_loc.longitude

        r = http.request("GET", f"http://api.open-notify.org/iss-pass.json?lat={lat}&lon={lon}")
        obj = json.loads(r.data)

        if obj["message"] == "success":
            iss_risetimes = []
            for response in obj["response"]:
                iss_risetimes.append(datetime.fromtimestamp(response['risetime']))

            user_pass_time["rise_time"] = iss_risetimes
            col_pass_time.insert_one(user_pass_time)

            return user_pass_time


def search_wikipedia(term):
    payload = {
        'action': 'query',
        'list': 'search',
        'prop': 'pageimages',
        'srsearch': f'{term}',
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


@scheduler.scheduled_job('interval', minutes=60, next_run_time=datetime.now())
def update_pass_times():
    col_pass_time.remove({})

    print(f"update_pass_times job runned at {datetime.now()}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
