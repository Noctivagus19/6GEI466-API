from flask import (
    Flask,
    jsonify,
)

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/v1/iss/astronauts', methods=['GET'])
def iss_astronauts():
    return jsonify([{'name': 'John Doe'}])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
