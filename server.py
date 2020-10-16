from threading import Lock
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from googleSheets import Googlesheet
import subprocess, shlex
import json
from urllib.parse import quote_plus
import sys, os
from datetime import datetime

async_mode = None
folder_scripts = os.path.abspath(os.path.split(__file__)[0])
if sys.platform == 'win32':
    controller = "{}\\controller.py".format(folder_scripts)
    python_path = "C:\\python\\python"
else:
    controller = "{}/controller.py".format(folder_scripts)
    python_path = "/usr/bin/python3"

app = Flask(__name__, static_folder='./build', static_url_path='/')
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins='*')
thread = None
thread_lock = Lock()

def run_bender(data):
    city = data["city"]
    category = data["category"]
    review = data["review"]
    precio = data["precio"]
    fecha = data.get("fecha", 'no definido')
    country = data["country"]
    scraper = data["scraper"]
    command_line = '{} {} --city "{}" --country "{}" --category {} --review {} --precio {} --scraper {} --fecha "{}"'\
       .format(python_path, controller, city, country, category, review, precio, scraper, fecha)
    if sys.platform == 'win32':
        args = command_line
    else:
        args = shlex.split(command_line)
    process = subprocess.Popen(args)
    return "ok"

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response', {'data': 'Server generated event', 'count': count})
                    
def timestamp():
    now = datetime.now()
    format = now.strftime('%H:%M:%S')
    return format

@socketio.on('connect')
def connect_socket():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/message_bender', methods=["POST"])
def message_bender():
    time = timestamp()
    data = json.loads(request.data)
    msg = "{} {}".format(data["msg"], time)
    socketio.emit("message_bender", msg, broadcast=True)
    return "Recibido"

@app.route('/api/run_scrapper', methods=["POST"])
def run_scrapper():
    data = request.get_json()
    msg = run_bender(data)
    print(msg)
    res = {'code':200, 'msg': 'finish'}
    return jsonify(res)

if __name__ == '__main__':
	#app.run(debug=True)
    socketio.run(app, debug=True)
