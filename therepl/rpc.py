import logging
import threading

from time import sleep
from werkzeug.serving import run_simple
from flask import Flask, request, abort

app = Flask(__name__)


THREAD = None


@app.route('/')
def index():
    return 'Use /eval Luke!'


@app.route('/eval', methods=['POST'])
def eval_code():
    return process_eval()


@app.route('/switch', methods=['POST'])
def switch():
    import flask
    import therepl
    
    if not flask.request.content_type.startswith('plain/text'):
        abort(400, 'Plain/text body was expected.')

    module_name = flask.request.data.decode('utf-8').strip()
    therepl.shell.run_line_magic('in', module_name)
    return 'OK'


def process_eval():
    if not request.content_type.startswith('plain/text'):
        abort(400, 'Plain/text body was expected.')
    code = request.data.decode('utf-8')

    import therepl
    therepl.shell.run_cell(code, in_module=request.args.get('in-module'))
    return 'OK'


def start(host='localhost', port=5005, in_thread=True):
    global THREAD

    if in_thread and THREAD:
        raise RuntimeError('Already started. Call stop() before starting again.')

    def worker():
        run_simple(host, port, app, use_debugger=True)

    if in_thread:
        # to suppress werkzeug from it initial message
        logger = logging.getLogger("werkzeug")
        logger.setLevel(logging.ERROR)
        THREAD = threading.Thread(target=worker, name='IPython Modules RPC', daemon=True)
        THREAD.start()
    else:
        return worker()
