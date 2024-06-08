"""
Name:
-----
    nodesession.py

Description:
------------
    Consists of Batfish related classes used for the offline Validation
    checks of Layer 3 interfaces.

Classes:
--------
    NodeSession

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["NodeSession"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import Optional
from pybatfish.client.session import Session


class NodeSession:
    """
    Keeps a Batfish session object and the Node name.

    Attributes
    ----------
    bf: Session
        An already open batfish Session object used to query the batfish
        service.

    node: str
        The name of the device as Nornir Task Host Name to receive
        (task.host.name)
    """

    def __init__(self, bf: Session, node: Optional[str] = None):
        self.session_bf = bf
        self.node = node
