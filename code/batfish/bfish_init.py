from pybatfish.client.session import Session
from pybatfish.datamodel import *  # noqa: F403
from pybatfish.datamodel.answer import *  # noqa: F403
from pybatfish.datamodel.flow import *  # noqa: F403
import os
from dotenv import load_dotenv
import random

load_dotenv()


def bfish_init():
    """ """
    BFISH_HOST = os.environ.get("BATFISH_HOST")
    BFISH_NET = os.environ.get("BATFISH_NETWORK")
    SNAP_DIR = os.environ.get("SNAPSHOT_DIR")
    SNAP_NAME = os.environ.get("BATFISH_NAME")

    bf_session = Session(host=BFISH_HOST)
    seconds = random.randrange(1000)
    BFISH_NET = BFISH_NET + str(seconds)
    bf_session.set_network(BFISH_NET)
    SNAP_NAME = SNAP_NAME + str(seconds)
    bf_session.init_snapshot(SNAP_DIR, name=SNAP_NAME, overwrite=True)
    # return  bf_session
    return bf_session
