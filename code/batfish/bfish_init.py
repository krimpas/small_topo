from pybatfish.client.session import Session
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
import os
from dotenv import load_dotenv

load_dotenv()


def bfish_init():
    """mpal mpla mpla mpal"""
    BFISH_HOST = os.environ.get("BATFISH_HOST")
    BFISH_NET = os.environ.get("BATFISH_NETWORK")
    SNAP_DIR = os.environ.get("SNAPSHOT_DIR")
    SNAP_NAME = os.environ.get("BATFISH_NAME")

    print(f"BFISH_HOST={BFISH_HOST}")
    print(f"BFISH_NET={BFISH_NET}")
    print(f"SNAP_DIR={SNAP_DIR}")
    print(f"SNAP_NAME={SNAP_NAME}")

    bf_session = Session(host=BFISH_HOST)

    bf_session.set_network(BFISH_NET)

    bf_session.init_snapshot(SNAP_DIR, name=SNAP_NAME, overwrite=True)
    # return  bdsession
    return bf_session
