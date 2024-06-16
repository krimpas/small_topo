"""
Name:
-----
    nodel3conf.py

Description:
------------
    Consists of the NodeL3IConf class which calculates all Layer 3 interfaces
    configuration mismatches.

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

        self.ipv4_mismatch = self.compute_ipv4_mismatch()

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

        self.sot_info["Admin_Up"] = self.sot_info.apply(self.get_enabled, axis=1)
        self.sot_info["Active"] = self.sot_info.apply(self.get_enabled, axis=1)

        self.sot_info.pop("ipv4")
        self.sot_info.pop("mask")
        self.sot_info.pop("name")
        self.sot_info.pop("enabled")

    @staticmethod
    def get_IPv4(row):
        """Returns an IPv4 in CIDR form"""
        return ipaddress.IPv4Interface(f"{str(row['ipv4'])}/{str(row['mask'])}")

    @staticmethod
    def get_IPv4net(row):
        """Returns the Network Address of an IPv4 address in a CIDR form."""
        return ipaddress.IPv4Interface(f"{str(row['ipv4'])}/{str(row['mask'])}").network

    @staticmethod
    def get_vrf(row):
        """Returns the VRF of the interface"""
        return row["VRF"]

    @staticmethod
    def get_enabled(row):
        """Returns if the interface is enabled"""
        return row["enabled"]

    @staticmethod
    def left_anti_join2(
        left_df: pd.DataFrame, right_df: pd.DataFrame, properties=List[str]
    ) -> pd.DataFrame:
        """
        Performs a left anti join to identify missing and unexpected interfaces.

        Parameters
        ----------
        left_df: pd.DataFrame
            The left DataFrame for the join.
        right_df: pd.DataFrame
            The right DataFrame for the join.
        properties: str
            The column used for the join. Defaults to 'Interface'.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the results of the left anti join.
        """
        outer = pd.merge(
            left_df[properties], right_df[properties], how="outer", indicator=True
        )
        # anti_join = (
        #    outer[outer["_merge"] == "left_only"]
        #    .drop(columns=["_merge"])
        #    .reset_index(drop=True)
        # )
        return outer

    def compute_ipv4_mismatch(self) -> pd.DataFrame:
        """
        Computes the configuration mismatches on L3 interfaces
        on the node.
        """
        iface = "Interface"
        pa = "Primary_Address"

        tmp_mismatch = self.left_anti_join2(
            left_df=self.actual,
            right_df=self.sot_info,
            properties=[iface, pa],
        )
        return tmp_mismatch

    def send_results(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """returns mismatch & actual"""
        return self.ipv4_mismatch, self.ipv4_mismatch
