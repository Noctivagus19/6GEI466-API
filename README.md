# 6GEI466_API
by Jean-Michel Plourde, Jean-Philippe Lapointe and Joel Villeneuve

## About The Project

Project repo for 6GEI466 - Applications réseaux et sécurité informatique.

### Built With

* [Flask](https://flask.palletsprojects.com/en/1.1.x/)
* [MongoDB](https://www.mongodb.com/)


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* python3.9
* flask1.1.x
* mongodb community edition
* [6GEI466](https://github.com/giant995/6GEI466_Projet) installed and running if you want to use this API through a platform

### Installation

1. Clone or unzip the repo
   * SSH
     ```sh
     git clone git@github.com:giant995/6GEI466_API.git
     ```
   
   * HTTPS
     ```sh
     git clone https://github.com/giant995/6GEI466_API.git
     ```
   
   * Zip download
     ```
     https://github.com/giant995/6GEI466_API/archive/main.zip
     ```
   
1. Go into the project folder
   ```sh
   cd 6GEI466_API
   ```
 
1. Create a virtual environment
   ```sh
   python3 -m venv myvenv
   source myvenv/bin/activate
   ```
1. Install pip dependencies from `requirements.txt`
   ```sh
   python3 -m pip install -r requirements.txt
   ```
1. Export environment variables
   ```sh
   export FLASK_ENV=development
   export FLASK_APP=app.py
   ```
   
   
<!-- USAGE EXAMPLES -->
## Usage
1. Make sure MongoDB deamon is running
   ```sh
   sudo systemctl start mongod
   ```
1. Launch the app server
   ```sh
   flask run
   ```
1. Make sure calls are working through port 8080
   ```sh
   localhost:8080/
   ```
