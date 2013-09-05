from server import app
from gevent import monkey
import argparse
from socketio.server import SocketIOServer


monkey.patch_all()

parser = argparse.ArgumentParser(description='Simple deep-tac-toe flask app.')
parser.add_argument('port', type=int, default=80, help='HTTP port for app')

if __name__ == '__main__':
    args = parser.parse_args()
    print 'Listening on http://127.0.0.1:%s and on port 10843 (flash policy server)' % args.port
    SocketIOServer(('', args.port), app, resource="socket.io").serve_forever()
