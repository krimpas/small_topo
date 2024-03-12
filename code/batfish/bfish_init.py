import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
import os
from dotenv import load_dotenv

load_dotenv()


def bfish_init():
    """ """
    BFISH_HOST = os.environ.get("BATFISH_HOST")
    BFISH_NET = os.environ.get("BATFISH_NETWORK")
    SNAP_DIR = os.environ.get("SNAPSHOT_DIR")
    SNAP_NAME = os.environ.get("BATFISH_NAME")

    print(f"BFISH_HOST={BFISH_HOST}")
    print(F"BFISH_NET={BFISH_NET}")
    print(F"SNAP_DIR={SNAP_DIR}")
    print(F"SNAP_NAME={SNAP_NAME}")

    bf_session = Session(host=BFISH_HOST)

    bf_session.set_network(BFISH_NET)

    bf_session.init_snapshot(SNAP_DIR, name=SNAP_NAME, overwrite=True)

    return bf_session
