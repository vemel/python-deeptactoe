#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from flask import Flask, Response
from flask import render_template, request
from flask.ext.bootstrap import Bootstrap
import argparse
from socketio import socketio_manage

parser = argparse.ArgumentParser(description='Simple deep-tac-toe flask app.')
parser.add_argument('port', type=int, default=80, help='HTTP port for app')

app = Flask(__name__)
Bootstrap(app)

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))

app.logger.addHandler(handler)
# app.logger.error(sorted(app.jinja_env.globals.keys()))


import namespace


@app.route("/")
def view_index():
    return render_template('index.jade')


@app.route("/hotseat")
def view_hotseat():
    return render_template('game_hotseat.jade')


@app.route("/network")
def view_network():
    return render_template('game_network.jade', room_name='main')


@app.route("/ai")
def view_ai():
    return render_template('game_ai.jade', room_name='ai')


@app.route("/ai/<room_name>")
def view_ai_room(room_name):
    return render_template('game_ai.jade', room_name=room_name)


@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/game': namespace.GameNamespace}, request)
    except:
        app.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()


@app.route('/network/<room_name>')
def view_network_room(room_name):
    return render_template('game_network.jade', room_name=room_name)

if __name__ == "__main__":
    args = parser.parse_args()
    app.debug = True
    app.run(port=args.port)
