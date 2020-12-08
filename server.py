"""
Server extension for the bot, with utilities to keep repl.it bots alive.

NOTE: repl.it still shuts the server down at a certain time each day
      basically, you will need an external service to ping the server
"""

import requests
import threading
import logging

from flask import Flask, request
from discord.ext import tasks

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

PORT = 3000
server = None
app = Flask(__name__)


@app.route('/')
def homepage():
    return 'The bot is up and running!'


@app.route('/shutdown')
def shutdown():
    if request.remote_addr == '127.0.0.1':
        print('[server] shutting down')
        func = request.environ.get('werkzeug.server.shutdown')
        func()
        return 'Ok!'

    return 'Hmm...', 401


def start_server():
    app.run(host='0.0.0.0', port=PORT, debug=False)


def fetch_on_thread():
    print('[keepalive] Doing keepalive fetch')
    requests.get('https://ASSISTant.davidtso.repl.co')


@tasks.loop(seconds=45)
async def keepalive_loop():
    threading.Thread(target=fetch_on_thread).start()


def setup(bot):
    global server

    if server:
        print('[server] WARNING! server already exists')

    keepalive_loop.start()
    server = threading.Thread(target=start_server)
    server.start()


def teardown(bot):
    global server

    keepalive_loop.cancel()

    if server:
        print('[server] Tearing down server')
        requests.get(f'http://127.0.0.1:{PORT}/shutdown')
        server.join()
        server.close()
        server = None
