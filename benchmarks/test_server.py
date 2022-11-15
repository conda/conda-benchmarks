"""
Flask-based conda repository server for testing.

Change contents to simulate an updating repository.
"""

import contextlib
import multiprocessing
import socket
import time
from pathlib import Path

import flask
from werkzeug.serving import WSGIRequestHandler, make_server, prepare_socket

app = flask.Flask(__name__)

base = Path(__file__).parents[1] / "env" / "conda-asyncio"

LATENCY = 0


@app.route("/shutdown")
def shutdown():
    server.shutdown()
    return "Goodbye"


@app.route("/latency/<float:delay>")
def latency(delay):
    """
    Set delay before each file response.
    """
    global LATENCY
    LATENCY = delay
    return "OK"


# flask.send_from_directory(directory, path, **kwargs)
# Send a file from within a directory using send_file().
@app.route("/<subdir>/<path:name>")
def download_file(subdir, name):
    time.sleep(LATENCY)
    # conditional=True is the default
    return flask.send_from_directory(base, name)


class NoLoggingWSGIRequestHandler(WSGIRequestHandler):
    def log(self, format, *args):
        pass


def make_server_with_socket(socket: socket.socket):
    global server
    assert isinstance(socket.fileno(), int)
    # processes may break global latency setting
    server = make_server(
        "127.0.0.1",
        port=0,
        app=app,
        fd=socket.fileno(),
        threaded=True,
        request_handler=NoLoggingWSGIRequestHandler,
    )
    server.serve_forever()


def run_on_random_port():
    """
    Run in a new process to minimize interference with test.
    """
    return run_and_cleanup().__enter__()


@contextlib.contextmanager
def run_and_cleanup(cleanup=True):
    socket = prepare_socket("127.0.0.1", 0)
    context = multiprocessing.get_context("spawn")
    process = context.Process(
        target=make_server_with_socket, args=(socket,), daemon=True
    )
    process.start()
    yield socket
    process.kill()


if __name__ == "__main__":

    print(run_on_random_port())
    time.sleep(60)
