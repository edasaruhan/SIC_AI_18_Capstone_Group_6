"""Run an isolated HTTP check against an ephemeral loopback socket."""

from contextlib import contextmanager
import socket
from threading import Thread
from time import perf_counter

import httpx
import uvicorn


@contextmanager
def loopback_client(app):
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", log_level="error", access_log=False))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = perf_counter() + 5
            while not server.started and thread.is_alive() and perf_counter() < deadline:
                thread.join(timeout=.02)
            if not server.started:
                raise RuntimeError("The loopback server did not start.")
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=5) as client:
                yield client
        finally:
            server.should_exit = True
            thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("The loopback server did not shut down.")
