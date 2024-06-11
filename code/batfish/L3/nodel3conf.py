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
import ipaddress
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

        self.sot_info = self.compute_interface_df(sot=sot[node])

        # keeps all duplicate ip address of the node if any.
        self.duplicates = self.compute_duplicates()

        self.transform()

    def compute_interface_df(self, sot: Dict):
        """builds a dataframe of interface conf info"""
        for iface in sot["interfaces"]:
            for some_key in DEFAULT_SOT_EXCLUDED_KEYS:
                iface.pop(some_key, None)

        tmp_list = [
            Interface(hostname=self.node, interface=iface["name"].replace(" ", ""))
            for iface in sot["interfaces"]
        ]
        tmp_df = pd.DataFrame.from_dict({"Interface": tmp_list})
        interface_info = pd.DataFrame.from_records(sot["interfaces"])
        result_df = pd.concat([tmp_df, interface_info], axis=1)

        # result_df.fillna("-", inplace=True)
        return result_df

    def compute_duplicates(self) -> pd.DataFrame:
        """
        Calculates all L3 interfaces with duplicate ipv4 addresses.

        Returns:
            pd.DataFrame: Duplicate IPv4 interfaces if any or empty.
        """
        any_duplicates = self.actual.duplicated(["Primary_Address"], keep=False)
        return self.actual[any_duplicates]

    def transform(self) -> pd.DataFrame:
        """
        Transform SoT into a frame similar to Batfish, in order to
        make comparisons.
        """
        self.sot_info["Primary_Address"] = self.sot_info.apply(self.get_IPv4, axis=1)

        self.sot_info["Primary_Network"] = self.sot_info.apply(self.get_IPv4net, axis=1)

        self.sot_info.drop(["ipv4", "mask", "name"], axis=1)

    @staticmethod
    def get_IPv4(row):
        return ipaddress.IPv4Interface(f"{str(row['ipv4'])}/{str(row['mask'])}")

    @staticmethod
    def get_IPv4net(row):
        return ipaddress.IPv4Interface(f"{str(row['ipv4'])}/{str(row['mask'])}").network

    @staticmethod
    def get_vrf(row):
        return row.VRF

    def send_results(self) -> pd.DataFrame:
        """returns actual"""
        return self.sot_info, self.duplicates
