"""Serve the verified bundle on loopback."""

import argparse
import os

import uvicorn

from nudgewell_hw6.api import create_app
from nudgewell_hw6.bundle import BUNDLE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    uvicorn.run(create_app(BUNDLE, os.environ.get("NUDGEWELL_HW6_API_KEY", "")),
                host="127.0.0.1", port=args.port, access_log=False)
