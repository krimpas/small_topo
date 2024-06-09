"""
Name:
-----
    nodel3conf.py

Description:
------------
    Consists of the NodeL3IConf class which calculates all Layer 3 interfaces configuration mismatches.

Classes:
--------
    NodeL3Conf

Misc variables:
---------------
    __all__
    __version__
    __author__
"""

__all__ = ["NodeL3Conf"]
__version__ = "0.0.1"
__author__ = "Krimpas George"

from typing import Dict, Optional, Tuple
import pandas as pd
from pybatfish.client.session import Session
from .nodel3 import NodeL3
from .bfilters import BFilter as fltr

DEFAULT_PROPERTIES = (
    "Active,Admin_Up,All_Prefixes,Primary_Address,Primary_Network,VRF,MTU"
)


class NodeL3Conf(NodeL3):
    """
    Checks the SoT configuration parameters for L3 interfaces against actually configured on the node.

    Attributes
    ----------
    """

    def __init__(
        self,
        bf: Session,
        sot: Dict,
        node: Optional[str] = None,
        properties: str = DEFAULT_PROPERTIES,
    ) -> None:
        super().__init__(bf=bf, sot=sot, node=node, properties=properties)

    def send_results(self) -> pd.DataFrame:
        """returns actual"""
        return self.actual
