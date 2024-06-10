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

from typing import Dict, Optional, Tuple, List
import pandas as pd
from pybatfish.client.session import Session
from pybatfish.datamodel import Interface
from .nodel3 import NodeL3
from .bfilters import BatFilter as fltr

DEFAULT_PROPERTIES = (
    "Active, Admin_Up, All_Prefixes, Primary_Address, Primary_Network, VRF, MTU"
)
DEFAULT_SOT_EXCLUDED_KEYS = ["ospf_config"]


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

        self.sot_info = (
            self.session_bf.q.interfaceProperties(
                nodes=self.node, properties=properties
            )
            .answer()
            .frame()
        )

    @staticmethod
    def exclude_sot_keys(d: Dict, keys: List[str]) -> Dict:
        """Exclude a set of keys from dictionary"""
        return {x: d[x] for x in d if x not in keys}

    def compute_interface_df(self, sot: Dict) -> pd.DataFrame:
        """builds a dataframe of interface conf info"""
        new_sot = sot.copy()
        for iface in new_sot[self.node]["interfaces"]:
            iface.pop(DEFAULT_SOT_EXCLUDED_KEYS, None)

        interface_info = pd.DataFrame.from_records(new_sot[self.node]["interfaces"])
        result_df = pd.concat([self.sot, interface_info], axis=1).reset_index(deep=True)

        result_df.fillna("-", inplace=True)
        self.sot_info = interface_info

    def send_results(self) -> pd.DataFrame:
        """returns actual"""
        return self.sot_info, self.actual
